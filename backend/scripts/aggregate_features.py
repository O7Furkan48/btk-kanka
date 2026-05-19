from __future__ import annotations

import argparse
import json
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

BACKEND_DIR = Path(__file__).parent.parent
DATA_DIR = BACKEND_DIR / "app" / "data"
PRODUCTS_JSON = DATA_DIR / "products.json"
REVIEWS_PARQUET = DATA_DIR / "reviews.parquet"
LABELS_PARQUET = DATA_DIR / "reviews_labels.parquet"

OUT_RISK = DATA_DIR / "risk.json"
OUT_SIZE = DATA_DIR / "size_advice.json"
OUT_SELLER = DATA_DIR / "seller_quality.json"
OUT_TREND = DATA_DIR / "trend.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("agg")

RISK_BAR_NAMES = {
    "kumas": "Kumaş kalitesi",
    "renk": "Renk farkı",
    "kalite": "Genel kalite / hasar",
    "kargo": "Kargo süreci",
    "koku": "Koku",
    "gorsel": "Görsel uyumsuzluğu",
    "fit_mismatch": "Beden uyum riski",
}

TR_AY = {
    "ocak": 1, "şubat": 2, "subat": 2, "mart": 3, "nisan": 4, "mayıs": 5, "mayis": 5,
    "haziran": 6, "temmuz": 7, "ağustos": 8, "agustos": 8, "eylül": 9, "eylul": 9,
    "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12,
}

def parse_tr_date(s: str) -> datetime | None:
    if not s or pd.isna(s):
        return None
    m = re.match(r"\s*(\d{1,2})\s+([A-Za-zçşğöüı]+)\s+(\d{4})\s*", str(s))
    if not m:
        return None
    day, ay, yil = m.groups()
    month = TR_AY.get(ay.lower())
    if not month:
        return None
    try:
        return datetime(int(yil), month, int(day))
    except ValueError:
        return None

def risk_level(percent: float) -> tuple[str, str]:
    if percent < 15:
        return "low", "Düşük"
    if percent <= 28:
        return "mid", "Orta"
    return "high", "Yüksek"

def aggregate_risk(merged: pd.DataFrame) -> dict:
    out: dict = {}
    for slug, g in merged.groupby("urun_slug"):
        n = len(g)
        if n == 0:
            continue

        if "sent_pos" in g.columns and not g["sent_pos"].isna().all():
            sent_pos_mean = float(g["sent_pos"].mean())
            risk_signals = float(
                g[["risk_kumas", "risk_renk", "risk_kalite", "risk_kargo", "risk_koku", "risk_gorsel"]]
                .clip(0, 1).mean(axis=1).mean()
            )

            fit_kucuk_mean = float(g.get("fit_kucuk", pd.Series([0])).mean())
            fit_buyuk_mean = float(g.get("fit_buyuk", pd.Series([0])).mean())
            fit_mismatch = max(0.0, min(1.0, fit_kucuk_mean + fit_buyuk_mean))
            satisfaction = int(round(sent_pos_mean * 100))
            percent = int(round((1 - sent_pos_mean) * 30 + risk_signals * 70))
            percent = max(0, min(percent, 60))

            bars = []
            for k in ("kumas", "renk", "kalite", "kargo", "koku", "gorsel"):
                col = f"risk_{k}"
                if col not in g.columns:
                    continue
                v = int(round(float(g[col].mean()) * 100))
                lvl, _ = risk_level(v)
                bars.append({"label": RISK_BAR_NAMES[k], "value": v, "level": lvl})

            fit_v = int(round(fit_mismatch * 100))
            bars.append({"label": RISK_BAR_NAMES["fit_mismatch"], "value": fit_v, "level": risk_level(fit_v)[0]})

            bars.sort(key=lambda b: -b["value"])
            bars = bars[:4]
        else:

            sent_pos_mean = 0.85
            satisfaction = 85
            percent = 0
            bars = []

        lvl, lbl = risk_level(percent)
        out[slug] = {
            "level": lvl,
            "percent": percent,
            "levelLabel": lbl,
            "reviewCount": int(n),
            "satisfaction": satisfaction,
            "bars": bars,
        }
    log.info(f"risk.json: {len(out)} ürün")
    return out

def aggregate_size_advice(merged: pd.DataFrame) -> dict:
    out: dict = defaultdict(dict)
    sub = merged.dropna(subset=["boy_bin", "kilo_bin", "beden"])
    sub = sub[sub["beden"].astype(str).str.len() > 0]

    grouped = sub.groupby(["urun_slug", "boy_bin", "kilo_bin"])
    for (slug, bb, kb), g in grouped:
        beden_count = Counter(g["beden"].astype(str).str.upper().str.strip())
        if not beden_count:
            continue
        en_cok_beden, n_beden = beden_count.most_common(1)[0]
        sample_n = int(len(g))
        sat_mean = float(g.get("sent_pos", pd.Series([0.85])).mean())
        memnuniyet = int(round(sat_mean * 100))

        key = f"{int(bb)}_{int(kb)}"
        risk_lvl, _ = risk_level(100 - memnuniyet)
        parts = [
            {"text": f"{int(bb)}cm "},
            {"text": f"{int(kb)}kg "},
            {"text": "profilinden "},
            {"text": f"{sample_n} kişi"},
            {"text": " bu üründen "},
            {"text": en_cok_beden, "bold": True},
            {"text": " almış. "},
            {"text": f"%{memnuniyet}", "bold": True},
            {"text": " memnun."},
        ]
        out[slug][key] = {
            "parts": parts,
            "type": risk_lvl,
            "_meta": {"beden": en_cok_beden, "sample": sample_n, "memnuniyet": memnuniyet},
        }
    log.info(f"size_advice.json: {len(out)} ürün, {sum(len(v) for v in out.values())} bucket")
    return dict(out)

def aggregate_seller_quality(merged: pd.DataFrame) -> dict:
    out: dict = defaultdict(list)
    sub = merged.dropna(subset=["satici"])
    sub = sub[sub["satici"].astype(str).str.len() > 0]
    for (slug, sat), g in sub.groupby(["urun_slug", "satici"]):
        if len(g) < 3:
            continue
        out[slug].append({
            "satici": str(sat),
            "ortalama_sent": round(float(g.get("sent_pos", pd.Series([0.85])).mean()), 3),
            "kumas_freq": round(float(g.get("risk_kumas", pd.Series([0])).mean()), 3),
            "kargo_freq": round(float(g.get("risk_kargo", pd.Series([0])).mean()), 3),
            "ornek_sayisi": int(len(g)),
        })

    for slug in out:
        out[slug].sort(key=lambda x: -x["ornek_sayisi"])
    log.info(f"seller_quality.json: {len(out)} ürün")
    return dict(out)

def aggregate_trend(merged: pd.DataFrame) -> dict:
    out: dict = {}
    if "tarih_dt" not in merged.columns or merged["tarih_dt"].isna().all():
        log.warning("Tarih kolonu boş, trend.json üretilemedi")
        return out

    today = merged["tarih_dt"].max()
    if pd.isna(today):
        return out
    cutoff_90 = today - timedelta(days=90)

    for slug, g in merged.groupby("urun_slug"):
        g = g.dropna(subset=["tarih_dt"])
        if len(g) < 10:
            continue
        son_90 = g[g["tarih_dt"] >= cutoff_90]
        oncesi = g[g["tarih_dt"] < cutoff_90]
        if len(oncesi) < 3:
            continue
        sent_son = float(son_90["sent_pos"].mean()) if not son_90.empty and "sent_pos" in son_90.columns else 0.85
        sent_onc = float(oncesi["sent_pos"].mean()) if "sent_pos" in oncesi.columns else 0.85
        delta = sent_son - sent_onc
        if delta > 0.05:
            trend = "yukseliyor"
        elif delta < -0.05:
            trend = "dusuyor"
        else:
            trend = "sabit"
        out[slug] = {
            "slug": slug,
            "son_90_gun": round(sent_son, 3),
            "onceki": round(sent_onc, 3),
            "trend": trend,
            "veri": [],
        }
    log.info(f"trend.json: {len(out)} ürün")
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", help="sadece tek ürün için göster")
    ap.add_argument("--show", action="store_true", help="çıktıyı stdout'a yaz")
    args = ap.parse_args()

    log.info("Veri yükleniyor…")
    reviews = pd.read_parquet(REVIEWS_PARQUET)
    log.info(f"  reviews: {len(reviews):,}")

    if LABELS_PARQUET.exists():
        labels = pd.read_parquet(LABELS_PARQUET)
        log.info(f"  labels : {len(labels):,}")
        merged = reviews.merge(labels, left_on="id", right_on="review_id", how="left")
    else:
        log.warning("reviews_labels.parquet yok — BERT inference koşmadı")
        log.warning("  → naive agregatlar üretilecek (sent_pos=0.85 sabit)")
        merged = reviews.copy()

        for col in ("sent_pos", "sent_neu", "sent_neg",
                    "fit_tam", "fit_kucuk", "fit_buyuk", "fit_unknown",
                    "risk_kumas", "risk_renk", "risk_kalite",
                    "risk_kargo", "risk_koku", "risk_gorsel"):
            merged[col] = 0.0
        merged["sent_pos"] = 0.85

    log.info("Tarih parse ediliyor…")
    merged["tarih_dt"] = merged["tarih"].apply(parse_tr_date)
    valid_dates = merged["tarih_dt"].notna().sum()
    log.info(f"  geçerli tarih: {valid_dates:,}/{len(merged):,}")

    if args.slug:
        merged = merged[merged["urun_slug"] == args.slug]
        log.info(f"  filter: {args.slug} → {len(merged):,} satır")

    risk = aggregate_risk(merged)
    size = aggregate_size_advice(merged)
    seller = aggregate_seller_quality(merged)
    trend = aggregate_trend(merged)

    for path, data in [(OUT_RISK, risk), (OUT_SIZE, size), (OUT_SELLER, seller), (OUT_TREND, trend)]:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log.info(f"Yazıldı: {path.name}")

    if args.show and args.slug:
        print(f"\n=== {args.slug} ===")
        print("RISK    :", json.dumps(risk.get(args.slug, {}), ensure_ascii=False, indent=2))
        print("SIZE    :", json.dumps(size.get(args.slug, {}), ensure_ascii=False, indent=2))
        print("SELLER  :", json.dumps(seller.get(args.slug, []), ensure_ascii=False, indent=2)[:1000])
        print("TREND   :", json.dumps(trend.get(args.slug, {}), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
