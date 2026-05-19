from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import sys
from pathlib import Path

import asyncpg
import pandas as pd

def _int_or_none(v):
    if v is None:
        return None
    try:
        if isinstance(v, float) and math.isnan(v):
            return None
    except Exception:
        pass
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

def _str_or_none(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    s = str(v).strip()
    return s or None

BACKEND_DIR = Path(__file__).parent.parent
DATA_DIR = BACKEND_DIR / "app" / "data"
PRODUCTS_JSON = DATA_DIR / "products.json"
REVIEWS_PARQUET = DATA_DIR / "reviews.parquet"
QA_PARQUET = DATA_DIR / "qa.parquet"
LABELS_PARQUET = DATA_DIR / "reviews_labels.parquet"

sys.path.insert(0, str(BACKEND_DIR))
from app.config import settings  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("ingest")

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
  slug         TEXT PRIMARY KEY,
  brand        TEXT,
  title        TEXT,
  category_key TEXT,
  price        DOUBLE PRECISION,
  data         JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS reviews (
  id           TEXT PRIMARY KEY,
  urun_slug    TEXT NOT NULL REFERENCES products(slug) ON DELETE CASCADE,
  yorum_metni  TEXT NOT NULL,
  beden        TEXT,
  boy          INTEGER,
  kilo         INTEGER,
  boy_bin      INTEGER,
  kilo_bin     INTEGER,
  tarih        TEXT,
  kullanici    TEXT,
  satici       TEXT
);
CREATE INDEX IF NOT EXISTS idx_reviews_slug ON reviews(urun_slug);
CREATE INDEX IF NOT EXISTS idx_reviews_slug_size ON reviews(urun_slug, boy_bin, kilo_bin);

CREATE TABLE IF NOT EXISTS qa (
  id             SERIAL PRIMARY KEY,
  urun_slug      TEXT NOT NULL REFERENCES products(slug) ON DELETE CASCADE,
  soru           TEXT NOT NULL,
  cevap          TEXT NOT NULL,
  satici         TEXT,
  soru_tarihi    TEXT,
  cevap_bilgi    TEXT
);
CREATE INDEX IF NOT EXISTS idx_qa_slug ON qa(urun_slug);

CREATE TABLE IF NOT EXISTS reviews_labels (
  review_id    TEXT PRIMARY KEY REFERENCES reviews(id) ON DELETE CASCADE,
  sent_label   TEXT,
  sent_pos     REAL,
  sent_neu     REAL,
  sent_neg     REAL,
  fit_label    TEXT,
  fit_tam      REAL,
  fit_kucuk    REAL,
  fit_buyuk    REAL,
  fit_unknown  REAL,
  risk_kumas   REAL,
  risk_renk    REAL,
  risk_kalite  REAL,
  risk_kargo   REAL,
  risk_koku    REAL,
  risk_gorsel  REAL,
  risk_top     TEXT
);
CREATE INDEX IF NOT EXISTS idx_labels_sent ON reviews_labels(sent_label);
CREATE INDEX IF NOT EXISTS idx_labels_fit ON reviews_labels(fit_label);
"""

async def setup_schema(conn: asyncpg.Connection) -> None:
    log.info("Şema oluşturuluyor (idempotent)...")
    await conn.execute(SCHEMA_SQL)
    log.info("  ✓ tablolar hazır")

async def ingest_products(conn: asyncpg.Connection) -> int:
    if not PRODUCTS_JSON.exists():
        log.warning(f"{PRODUCTS_JSON} yok, atlanıyor")
        return 0

    with open(PRODUCTS_JSON, encoding="utf-8") as f:
        products = json.load(f)

    log.info(f"products ingest: {len(products)} ürün")
    await conn.execute("TRUNCATE products CASCADE")

    rows = []
    for p in products:
        rows.append((
            p["slug"],
            p.get("brand"),
            p.get("title"),
            p.get("categoryKey"),
            float(p.get("price") or 0),
            json.dumps(p, ensure_ascii=False),
        ))
    await conn.executemany(
        "INSERT INTO products(slug, brand, title, category_key, price, data) VALUES($1,$2,$3,$4,$5,$6::jsonb)",
        rows,
    )
    log.info(f"  ✓ {len(rows)} ürün yazıldı")
    return len(rows)

async def ingest_reviews(conn: asyncpg.Connection) -> int:
    if not REVIEWS_PARQUET.exists():
        log.warning(f"{REVIEWS_PARQUET} yok, atlanıyor")
        return 0

    df = pd.read_parquet(REVIEWS_PARQUET)
    log.info(f"reviews ingest: {len(df):,} yorum")

    slug_set = {r["slug"] for r in await conn.fetch("SELECT slug FROM products")}
    df = df[df["urun_slug"].isin(slug_set)]
    log.info(f"  FK temizliği sonrası: {len(df):,}")

    records = [
        (
            str(row["id"]),
            str(row["urun_slug"]),
            str(row["yorum_metni"]),
            _str_or_none(row["beden"]),
            _int_or_none(row["boy"]),
            _int_or_none(row["kilo"]),
            _int_or_none(row["boy_bin"]),
            _int_or_none(row["kilo_bin"]),
            _str_or_none(row["tarih"]),
            _str_or_none(row["kullanici"]),
            _str_or_none(row["satici"]),
        )
        for row in df.to_dict("records")
    ]
    await conn.copy_records_to_table(
        "reviews",
        records=records,
        columns=["id", "urun_slug", "yorum_metni", "beden", "boy", "kilo", "boy_bin", "kilo_bin", "tarih", "kullanici", "satici"],
    )
    log.info(f"  ✓ {len(records):,} yorum yazıldı")
    return len(records)

async def ingest_qa(conn: asyncpg.Connection) -> int:
    if not QA_PARQUET.exists():
        log.warning(f"{QA_PARQUET} yok, atlanıyor")
        return 0

    df = pd.read_parquet(QA_PARQUET)
    log.info(f"qa ingest: {len(df):,}")

    slug_set = {r["slug"] for r in await conn.fetch("SELECT slug FROM products")}
    df = df[df["urun_slug"].isin(slug_set)]
    log.info(f"  FK temizliği sonrası: {len(df):,}")

    records = [
        (
            str(row["urun_slug"]),
            str(row["soru"]),
            str(row["cevap"]),
            _str_or_none(row["satici"]),
            _str_or_none(row["soru_tarihi"]),
            _str_or_none(row["cevap_bilgi"]),
        )
        for row in df.to_dict("records")
    ]
    await conn.copy_records_to_table(
        "qa",
        records=records,
        columns=["urun_slug", "soru", "cevap", "satici", "soru_tarihi", "cevap_bilgi"],
    )
    log.info(f"  ✓ {len(records):,} q&a yazıldı")
    return len(records)

async def ingest_labels(conn: asyncpg.Connection) -> int:
    if not LABELS_PARQUET.exists():
        log.warning(f"{LABELS_PARQUET} yok — BERT inference henüz koşmadı, atlanıyor")
        return 0

    df = pd.read_parquet(LABELS_PARQUET)
    log.info(f"reviews_labels ingest: {len(df):,}")

    valid = {r["id"] for r in await conn.fetch("SELECT id FROM reviews")}
    df = df[df["review_id"].isin(valid)]
    log.info(f"  FK temizliği sonrası: {len(df):,}")

    await conn.execute("TRUNCATE reviews_labels")
    cols = [
        "review_id", "sent_label", "sent_pos", "sent_neu", "sent_neg",
        "fit_label", "fit_tam", "fit_kucuk", "fit_buyuk", "fit_unknown",
        "risk_kumas", "risk_renk", "risk_kalite", "risk_kargo", "risk_koku", "risk_gorsel",
        "risk_top",
    ]
    records = [
        (
            str(row["review_id"]),
            _str_or_none(row.get("sent_label")),
            float(row.get("sent_pos") or 0),
            float(row.get("sent_neu") or 0),
            float(row.get("sent_neg") or 0),
            _str_or_none(row.get("fit_label")),
            float(row.get("fit_tam") or 0),
            float(row.get("fit_kucuk") or 0),
            float(row.get("fit_buyuk") or 0),
            float(row.get("fit_unknown") or 0),
            float(row.get("risk_kumas") or 0),
            float(row.get("risk_renk") or 0),
            float(row.get("risk_kalite") or 0),
            float(row.get("risk_kargo") or 0),
            float(row.get("risk_koku") or 0),
            float(row.get("risk_gorsel") or 0),
            _str_or_none(row.get("risk_top")),
        )
        for row in df.to_dict("records")
    ]
    await conn.copy_records_to_table("reviews_labels", records=records, columns=cols)
    log.info(f"  ✓ {len(records):,} label yazıldı")
    return len(records)

async def health(conn: asyncpg.Connection) -> None:
    products = await conn.fetchval("SELECT COUNT(*) FROM products")
    reviews = await conn.fetchval("SELECT COUNT(*) FROM reviews")
    qa = await conn.fetchval("SELECT COUNT(*) FROM qa")
    labels = await conn.fetchval("SELECT COUNT(*) FROM reviews_labels")
    print(f"\n{'='*50}")
    print(f"  products       : {products:,}")
    print(f"  reviews        : {reviews:,}")
    print(f"  qa             : {qa:,}")
    print(f"  reviews_labels : {labels:,}")
    print(f"{'='*50}\n")

async def main_async(args):

    pg_url = settings.database_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(pg_url)
    try:
        await setup_schema(conn)
        if args.raw:
            await ingest_products(conn)
            await ingest_reviews(conn)
            await ingest_qa(conn)
        if args.labels:
            await ingest_labels(conn)
        await health(conn)
    finally:
        await conn.close()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", action="store_true", help="products + reviews + qa")
    ap.add_argument("--labels", action="store_true", help="reviews_labels (BERT çıktısı)")
    args = ap.parse_args()
    if not (args.raw or args.labels):
        ap.error("--raw ve/veya --labels seçmek zorundasın")
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
