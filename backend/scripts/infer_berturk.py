from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm
from transformers import AutoTokenizer

BACKEND_DIR = Path(__file__).parent.parent
DATA_DIR = BACKEND_DIR / "app" / "data"
MODEL_DIR = DATA_DIR / "models" / "berturk_multitask"
REVIEWS_PARQUET = DATA_DIR / "reviews.parquet"
LABELS_PARQUET = DATA_DIR / "reviews_labels.parquet"

sys.path.insert(0, str(BACKEND_DIR))
from scripts.train_berturk import (  # noqa: E402
    BERTurkMultiTask, SENT_LABELS, FIT_LABELS, RISK_LABELS, BASE_MODEL,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("infer")

RISK_THRESHOLD = 0.5

class InferDataset(Dataset):
    def __init__(self, texts: list[str], tokenizer, max_len: int = 128):
        self.texts = texts
        self.tok = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tok(
            self.texts[idx],
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "token_type_ids": enc.get("token_type_ids", torch.zeros_like(enc["input_ids"])).squeeze(0),
        }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--max-len", type=int, default=128)
    ap.add_argument("--n", type=int, default=0, help="0 = tüm yorumlar")
    ap.add_argument("--num-workers", type=int, default=0)
    args = ap.parse_args()

    device = torch.device(
        "mps" if torch.backends.mps.is_available()
        else ("cuda" if torch.cuda.is_available() else "cpu")
    )
    log.info(f"Cihaz: {device}")

    model_path = MODEL_DIR / "pytorch_model.bin"
    if not model_path.exists():
        log.error(f"{model_path} yok — önce train_berturk.py koş")
        return

    log.info(f"Model yükleniyor: {MODEL_DIR}")
    model = BERTurkMultiTask().to(device)
    state = torch.load(model_path, map_location=device, weights_only=True)
    model.load_state_dict(state, strict=True)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR / "tokenizer" if (MODEL_DIR / "tokenizer").exists() else BASE_MODEL)

    df = pd.read_parquet(REVIEWS_PARQUET)
    if args.n > 0:
        df = df.head(args.n)
    log.info(f"Yorum sayısı: {len(df):,}")

    texts = df["yorum_metni"].astype(str).tolist()
    ids = df["id"].tolist()

    ds = InferDataset(texts, tokenizer, args.max_len)
    loader = DataLoader(ds, batch_size=args.batch, shuffle=False, num_workers=args.num_workers)

    all_sent_probs = []
    all_fit_probs = []
    all_risk_probs = []

    start = time.monotonic()
    with torch.no_grad():
        for batch in tqdm(loader, desc="Inference"):
            ids_b = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            tti = batch["token_type_ids"].to(device)
            sl, fl, rl = model(ids_b, mask, tti)
            all_sent_probs.append(torch.softmax(sl, -1).cpu().numpy())
            all_fit_probs.append(torch.softmax(fl, -1).cpu().numpy())
            all_risk_probs.append(torch.sigmoid(rl).cpu().numpy())

    sent_p = np.concatenate(all_sent_probs)
    fit_p = np.concatenate(all_fit_probs)
    risk_p = np.concatenate(all_risk_probs)
    dur = time.monotonic() - start
    log.info(f"Inference bitti: {dur:.0f}s ({len(ids)/dur:.0f} yorum/sn)")

    sent_label = [SENT_LABELS[i] for i in sent_p.argmax(-1)]
    fit_label = [FIT_LABELS[i] for i in fit_p.argmax(-1)]

    risk_top: list[str] = []
    for i in range(len(ids)):
        above = [(p, RISK_LABELS[j]) for j, p in enumerate(risk_p[i]) if p >= RISK_THRESHOLD]
        if above:
            above.sort(reverse=True)
            risk_top.append(above[0][1])
        else:
            risk_top.append("")

    out = pd.DataFrame({
        "review_id": ids,
        "sent_label": sent_label,
        "sent_pos": sent_p[:, 0],
        "sent_neu": sent_p[:, 1],
        "sent_neg": sent_p[:, 2],
        "fit_label": fit_label,
        "fit_tam": fit_p[:, 0],
        "fit_kucuk": fit_p[:, 1],
        "fit_buyuk": fit_p[:, 2],
        "fit_unknown": fit_p[:, 3],
        "risk_kumas": risk_p[:, 0],
        "risk_renk": risk_p[:, 1],
        "risk_kalite": risk_p[:, 2],
        "risk_kargo": risk_p[:, 3],
        "risk_koku": risk_p[:, 4],
        "risk_gorsel": risk_p[:, 5],
        "risk_top": risk_top,
    })
    out.to_parquet(LABELS_PARQUET, index=False)
    log.info(f"Yazıldı: {LABELS_PARQUET} ({len(out):,} satır)")

    from collections import Counter
    print(f"\nSENT dağılımı: {dict(Counter(sent_label))}")
    print(f"FIT  dağılımı: {dict(Counter(fit_label))}")
    risk_count = {r: int((risk_p[:, i] >= RISK_THRESHOLD).sum()) for i, r in enumerate(RISK_LABELS)}
    print(f"RISK ≥{RISK_THRESHOLD}: {risk_count}")

if __name__ == "__main__":
    main()
