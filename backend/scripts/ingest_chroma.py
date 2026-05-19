from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

BACKEND_DIR = Path(__file__).parent.parent
DATA_DIR = BACKEND_DIR / "app" / "data"
CHROMA_DIR = DATA_DIR / "chroma"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

PRODUCTS_JSON = DATA_DIR / "products.json"
REVIEWS_PARQUET = DATA_DIR / "reviews.parquet"
LABELS_PARQUET = DATA_DIR / "reviews_labels.parquet"
QA_PARQUET = DATA_DIR / "qa.parquet"
RISK_JSON = DATA_DIR / "risk.json"

sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("chroma")

ENCODER_MODEL = "BAAI/bge-m3"
ENCODE_BATCH = 32

PER_PRODUCT_REVIEWS = 200
PER_PRODUCT_QA = 50

def load_encoder() -> SentenceTransformer:
    log.info(f"Encoder yükleniyor: {ENCODER_MODEL} (cold-load 30-60 sn)")
    t0 = time.monotonic()
    enc = SentenceTransformer(ENCODER_MODEL)
    log.info(f"  ✓ {time.monotonic()-t0:.0f}s")
    return enc

def get_client() -> chromadb.PersistentClient:
    return chromadb.PersistentClient(path=str(CHROMA_DIR))

def ingest_products(client, encoder) -> None:
    with open(PRODUCTS_JSON, encoding="utf-8") as f:
        products = json.load(f)
    risk = {}
    if RISK_JSON.exists():
        with open(RISK_JSON, encoding="utf-8") as f:
            risk = json.load(f)

    col = client.get_or_create_collection("products_collection")

    try:
        client.delete_collection("products_collection")
    except Exception:
        pass
    col = client.create_collection("products_collection")

    log.info(f"products ingest: {len(products)}")
    texts, ids, metas = [], [], []
    for p in products:
        cat_breadcrumb = p.get("category", []) or []

        kategori_son = ""
        for c in reversed(cat_breadcrumb):
            lbl = c.get("label", "") if isinstance(c, dict) else str(c)
            if lbl and "marka" not in lbl.lower() and "trendyol" not in lbl.lower():
                kategori_son = lbl
                break

        if not kategori_son and cat_breadcrumb:
            kategori_son = (cat_breadcrumb[-1].get("label") if isinstance(cat_breadcrumb[-1], dict) else str(cat_breadcrumb[-1]))

        cinsiyet = "unisex"
        all_labels = " ".join(
            (c.get("label", "") if isinstance(c, dict) else str(c)).lower()
            for c in cat_breadcrumb
        ).lower()
        title_lower = p.get("title", "").lower()
        combined = all_labels + " " + title_lower
        if "kadın" in combined or "kadin" in combined:
            cinsiyet = "kadin"
        elif "erkek" in combined:
            cinsiyet = "erkek"
        elif "çocuk" in combined or "bebek" in combined:
            cinsiyet = "cocuk"

        specs_text = " ".join(f"{k}:{v}" for k, v in (p.get("specs") or [])[:8])

        embed = (
            f"{kategori_son}. {kategori_son}. "
            f"{p.get('title','')} {p.get('brand','')} "
            f"{' > '.join(c.get('label','') for c in cat_breadcrumb[:4])} "
            f"{p.get('summary','')} {specs_text}"
        )
        rd = risk.get(p["slug"], {})
        meta = {
            "slug": p["slug"],
            "marka": str(p.get("brand", "") or "")[:80],
            "kategori_key": str(p.get("categoryKey", "") or ""),
            "kategori_son": kategori_son[:80],
            "cinsiyet": cinsiyet,
            "fiyat": float(p.get("price") or 0),
            "rating": float(p.get("rating") or 0),
            "risk_level": rd.get("level", "low"),
            "bg": str(p.get("bg", "") or ""),
            "imageUrl": str(p.get("imageUrl", "") or "")[:300],
        }
        texts.append(embed[:500])
        ids.append(p["slug"])
        metas.append(meta)

    embs = encoder.encode(texts, batch_size=ENCODE_BATCH, show_progress_bar=True, convert_to_numpy=True)
    col.add(ids=ids, embeddings=embs.tolist(), documents=texts, metadatas=metas)
    log.info(f"  ✓ {len(ids)} ürün vektör eklendi")

def select_top_reviews(reviews: pd.DataFrame, labels: pd.DataFrame | None) -> pd.DataFrame:
    df = reviews.copy()
    df["text_len"] = df["yorum_metni"].astype(str).str.len()
    df["has_size"] = df["boy"].notna() & df["kilo"].notna()
    if labels is not None and not labels.empty:
        df = df.merge(labels[["review_id", "sent_label", "fit_label", "risk_top"]],
                      left_on="id", right_on="review_id", how="left")
    else:
        df["sent_label"] = None
        df["fit_label"] = None
        df["risk_top"] = None
    df["score"] = (
        df["text_len"].clip(0, 300) / 300
        + df["has_size"].astype(int) * 0.5
        + df["sent_label"].notna().astype(int) * 0.3
    )
    return df.sort_values(["urun_slug", "score"], ascending=[True, False]).groupby("urun_slug").head(PER_PRODUCT_REVIEWS)

def ingest_reviews(client, encoder) -> None:
    reviews = pd.read_parquet(REVIEWS_PARQUET)
    labels = pd.read_parquet(LABELS_PARQUET) if LABELS_PARQUET.exists() else None
    log.info(f"Reviews: {len(reviews):,}, labels: {0 if labels is None else len(labels):,}")

    top = select_top_reviews(reviews, labels)
    log.info(f"  seçildi (ürün başı top {PER_PRODUCT_REVIEWS}): {len(top):,}")

    try:
        client.delete_collection("reviews_collection")
    except Exception:
        pass
    col = client.create_collection("reviews_collection")

    texts, ids, metas = [], [], []
    for row in top.to_dict("records"):
        text = str(row["yorum_metni"])
        if len(text) < 8:
            continue
        meta = {
            "urun_slug": str(row["urun_slug"]),
            "beden": str(row.get("beden") or ""),
            "boy_bin": int(row["boy_bin"]) if pd.notna(row.get("boy_bin")) else -1,
            "kilo_bin": int(row["kilo_bin"]) if pd.notna(row.get("kilo_bin")) else -1,
            "sent_label": str(row.get("sent_label") or "unknown"),
            "fit_label": str(row.get("fit_label") or "unknown"),
            "risk_top": str(row.get("risk_top") or ""),
            "has_size_signal": bool(row.get("has_size", False)),
        }
        texts.append(text[:600])
        ids.append(str(row["id"]))
        metas.append(meta)

    log.info(f"Encoding {len(texts):,} yorum (batch={ENCODE_BATCH})…")
    embs = encoder.encode(texts, batch_size=ENCODE_BATCH, show_progress_bar=True, convert_to_numpy=True)

    chunk = 5000
    for i in tqdm(range(0, len(ids), chunk), desc="Chroma add"):
        j = min(i + chunk, len(ids))
        col.add(
            ids=ids[i:j],
            embeddings=embs[i:j].tolist(),
            documents=texts[i:j],
            metadatas=metas[i:j],
        )
    log.info(f"  ✓ {len(ids)} yorum vektör eklendi")

def ingest_qa(client, encoder) -> None:
    df = pd.read_parquet(QA_PARQUET)
    df["text"] = df["soru"].astype(str) + " — " + df["cevap"].astype(str)
    df["rownum"] = df.groupby("urun_slug").cumcount()
    df = df[df["rownum"] < PER_PRODUCT_QA]
    log.info(f"qa subset (top {PER_PRODUCT_QA}/ürün): {len(df):,}")

    try:
        client.delete_collection("qa_collection")
    except Exception:
        pass
    col = client.create_collection("qa_collection")

    texts, ids, metas = [], [], []
    for i, row in enumerate(df.to_dict("records")):
        if len(row["text"]) < 8:
            continue
        meta = {
            "urun_slug": str(row["urun_slug"]),
            "satici": str(row.get("satici") or ""),
            "soru_tarihi": str(row.get("soru_tarihi") or ""),
        }
        texts.append(row["text"][:600])
        ids.append(f"qa_{i}")
        metas.append(meta)

    log.info(f"Encoding {len(texts):,} q&a…")
    embs = encoder.encode(texts, batch_size=ENCODE_BATCH, show_progress_bar=True, convert_to_numpy=True)
    chunk = 5000
    for i in tqdm(range(0, len(ids), chunk), desc="Chroma add"):
        j = min(i + chunk, len(ids))
        col.add(
            ids=ids[i:j],
            embeddings=embs[i:j].tolist(),
            documents=texts[i:j],
            metadatas=metas[i:j],
        )
    log.info(f"  ✓ {len(ids)} q&a vektör eklendi")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--collections", nargs="+", default=["products", "reviews", "qa"],
                    choices=["products", "reviews", "qa"])
    args = ap.parse_args()

    client = get_client()
    encoder = load_encoder()

    if "products" in args.collections:
        ingest_products(client, encoder)
    if "reviews" in args.collections:
        ingest_reviews(client, encoder)
    if "qa" in args.collections:
        ingest_qa(client, encoder)

    log.info("Tüm koleksiyonlar hazır")
    for name in ("products_collection", "reviews_collection", "qa_collection"):
        try:
            c = client.get_collection(name)
            print(f"  {name}: {c.count():,} doc")
        except Exception as e:
            print(f"  {name}: ✗ {e}")

if __name__ == "__main__":
    main()
