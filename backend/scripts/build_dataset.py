import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("build_dataset")

OUT_DIR = Path(__file__).parent.parent / "app" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

HF_DATASET = "fthbrmnby/turkish_product_reviews"
HF_PARQUET = OUT_DIR / "hf_reviews.parquet"
KANKA_PARQUET = OUT_DIR / "reviews.parquet"
COMBINED_PARQUET = OUT_DIR / "dataset_full.parquet"

def download_hf() -> pd.DataFrame:
    log.info(f"HF dataset indiriliyor: {HF_DATASET}")
    from datasets import load_dataset

    ds = load_dataset(HF_DATASET)
    splits = list(ds.keys())
    log.info(f"  splitler: {splits}")

    frames = []
    for split in splits:
        df = ds[split].to_pandas()
        df["hf_split"] = split
        frames.append(df)
    hf = pd.concat(frames, ignore_index=True)
    log.info(f"  HF toplam satır: {len(hf):,}")
    log.info(f"  HF kolonlar: {list(hf.columns)}")

    if "sentence" in hf.columns:
        hf = hf.rename(columns={"sentence": "text"})
    if "review" in hf.columns:
        hf = hf.rename(columns={"review": "text"})

    if "sentiment" in hf.columns:
        hf["sentiment_hf"] = hf["sentiment"].astype("Int64")
    else:
        hf["sentiment_hf"] = pd.NA

    return hf

def normalize_hf(hf: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "id": [f"hf_{i}" for i in range(len(hf))],
        "source": "hf",
        "text": hf["text"].astype(str),
        "sentiment_hf": hf["sentiment_hf"],
        "urun_slug": pd.NA,
        "beden": pd.NA,
        "boy": pd.NA,
        "kilo": pd.NA,
        "boy_bin": pd.NA,
        "kilo_bin": pd.NA,
        "tarih": pd.NA,
        "kullanici": pd.NA,
        "satici": pd.NA,
    })
    return out

def normalize_kanka(k: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame({
        "id": k["id"].astype(str),
        "source": "kanka",
        "text": k["yorum_metni"].astype(str),
        "sentiment_hf": pd.NA,
        "urun_slug": k["urun_slug"],
        "beden": k["beden"],
        "boy": k["boy"],
        "kilo": k["kilo"],
        "boy_bin": k["boy_bin"],
        "kilo_bin": k["kilo_bin"],
        "tarih": k["tarih"],
        "kullanici": k["kullanici"],
        "satici": k["satici"],
    })
    return out

def main():

    if HF_PARQUET.exists():
        log.info(f"HF cache var, yeniden indirmiyorum: {HF_PARQUET}")
        hf = pd.read_parquet(HF_PARQUET)
    else:
        hf = download_hf()
        hf.to_parquet(HF_PARQUET, index=False)
        log.info(f"Yazıldı: {HF_PARQUET}")

    if not KANKA_PARQUET.exists():
        raise FileNotFoundError(f"{KANKA_PARQUET} yok — önce etl_normalize.py koş")
    kanka = pd.read_parquet(KANKA_PARQUET)
    log.info(f"Kanka reviews: {len(kanka):,} satır")

    hf_norm = normalize_hf(hf)
    kanka_norm = normalize_kanka(kanka)
    combined = pd.concat([hf_norm, kanka_norm], ignore_index=True)
    combined.to_parquet(COMBINED_PARQUET, index=False)
    log.info(f"Yazıldı: {COMBINED_PARQUET}")

    print(f"\n{'='*60}")
    print(f"HF       : {len(hf):,} satır")
    if "sentiment_hf" in hf_norm.columns:
        hf_pos = (hf_norm["sentiment_hf"] == 1).sum()
        hf_neg = (hf_norm["sentiment_hf"] == 0).sum()
        print(f"  positive: {hf_pos:,} (%{hf_pos/len(hf_norm)*100:.1f})")
        print(f"  negative: {hf_neg:,} (%{hf_neg/len(hf_norm)*100:.1f})")
    print(f"Kanka    : {len(kanka):,} satır")
    print(f"  text uzunluğu medyan: {kanka['yorum_metni'].str.len().median():.0f} ch")
    print(f"  text uzunluğu p90  : {kanka['yorum_metni'].str.len().quantile(0.9):.0f} ch")
    print(f"  boy dolu           : {kanka['boy'].notna().sum():,} (%{kanka['boy'].notna().mean()*100:.1f})")
    print(f"  kilo dolu          : {kanka['kilo'].notna().sum():,} (%{kanka['kilo'].notna().mean()*100:.1f})")
    print(f"  beden dolu         : {(kanka['beden'].astype(str).str.len() > 0).sum():,}")
    print(f"  benzersiz ürün     : {kanka['urun_slug'].nunique():,}")
    print(f"Combined : {len(combined):,} satır")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
