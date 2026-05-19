from __future__ import annotations

import argparse
import json
import logging
import math
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split
from torch.utils.data import DataLoader, Dataset, WeightedRandomSampler
from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup

BACKEND_DIR = Path(__file__).parent.parent
DATA_DIR = BACKEND_DIR / "app" / "data"
MODEL_DIR = DATA_DIR / "models" / "berturk_multitask"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

REVIEWS_PARQUET = DATA_DIR / "reviews.parquet"
HF_PARQUET = DATA_DIR / "hf_reviews.parquet"
QWEN_JSONL = DATA_DIR / "reviews_qwen.jsonl"
GOLD_PARQUET = DATA_DIR / "gold.parquet"

sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("train")

SENT_LABELS = ["positive", "neutral", "negative"]
FIT_LABELS = ["tam", "kucuk", "buyuk", "belirsiz"]
RISK_LABELS = ["kumas", "renk", "kalite", "kargo", "koku", "gorsel"]

SENT_IDX = {l: i for i, l in enumerate(SENT_LABELS)}
FIT_IDX = {l: i for i, l in enumerate(FIT_LABELS)}
RISK_IDX = {l: i for i, l in enumerate(RISK_LABELS)}

BASE_MODEL = "dbmdz/convbert-base-turkish-cased"

class BERTurkMultiTask(nn.Module):
    def __init__(self, base: str = BASE_MODEL):
        super().__init__()
        self.bert = AutoModel.from_pretrained(base)
        h = self.bert.config.hidden_size
        self.dropout = nn.Dropout(0.1)
        self.head_sent = nn.Linear(h, len(SENT_LABELS))
        self.head_fit = nn.Linear(h, len(FIT_LABELS))
        self.head_risk = nn.Linear(h, len(RISK_LABELS))

    def forward(self, input_ids, attention_mask, token_type_ids=None):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids)
        pooled = self.dropout(out.last_hidden_state[:, 0])
        return self.head_sent(pooled), self.head_fit(pooled), self.head_risk(pooled)

def freeze_encoder_except_last_n(model: BERTurkMultiTask, n: int = 2) -> None:
    for p in model.bert.embeddings.parameters():
        p.requires_grad = False
    layers = model.bert.encoder.layer
    cutoff = len(layers) - n
    for layer in layers[:cutoff]:
        for p in layer.parameters():
            p.requires_grad = False
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    log.info(f"Donduruldu: trainable {trainable/1e6:.1f}M / total {total/1e6:.1f}M")

def unfreeze_all(model: BERTurkMultiTask) -> None:
    for p in model.parameters():
        p.requires_grad = True

class MultiTaskDataset(Dataset):

    def __init__(self, records: list[dict], tokenizer, max_len: int = 128):
        self.records = records
        self.tok = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.records)

    def __getitem__(self, idx):
        r = self.records[idx]
        enc = self.tok(
            r["text"],
            truncation=True,
            padding="max_length",
            max_length=self.max_len,
            return_tensors="pt",
        )
        return {
            "input_ids": enc["input_ids"].squeeze(0),
            "attention_mask": enc["attention_mask"].squeeze(0),
            "token_type_ids": enc.get("token_type_ids", torch.zeros_like(enc["input_ids"])).squeeze(0),
            "sent": torch.tensor(r.get("sent", -100), dtype=torch.long),
            "fit": torch.tensor(r.get("fit", -100), dtype=torch.long),
            "risk": torch.tensor(r.get("risk", [-100.0] * len(RISK_LABELS)), dtype=torch.float),
        }

def load_hf_records() -> list[dict]:
    if not HF_PARQUET.exists():
        raise FileNotFoundError(f"{HF_PARQUET} yok — build_dataset.py koş")
    df = pd.read_parquet(HF_PARQUET)

    text_col = "sentence" if "sentence" in df.columns else "text"
    sent_col = "sentiment"
    df = df.dropna(subset=[text_col, sent_col])
    out = []
    for _, row in df.iterrows():
        s = int(row[sent_col])
        sent_idx = SENT_IDX["positive"] if s == 1 else SENT_IDX["negative"]
        out.append({
            "text": str(row[text_col]),
            "sent": sent_idx,

        })
    log.info(f"HF yüklendi: {len(out):,} satır")
    return out

def load_qwen_records() -> list[dict]:
    if not QWEN_JSONL.exists():
        raise FileNotFoundError(f"{QWEN_JSONL} yok — llm_label_qwen.py koş")

    labels = {}
    with open(QWEN_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "id" in obj and "error" not in obj:
                    labels[obj["id"]] = obj
            except json.JSONDecodeError:
                continue

    reviews = pd.read_parquet(REVIEWS_PARQUET)
    review_map = dict(zip(reviews["id"], reviews["yorum_metni"]))

    out = []
    for rid, lbl in labels.items():
        text = review_map.get(rid)
        if not text:
            continue
        risk_vec = [1.0 if r in lbl.get("risks", []) else 0.0 for r in RISK_LABELS]
        out.append({
            "text": str(text),
            "sent": SENT_IDX[lbl["sentiment"]],
            "fit": FIT_IDX[lbl["fit"]],
            "risk": risk_vec,
        })
    log.info(f"Qwen yüklendi: {len(out):,} etiketli yorum")
    return out

def load_gold_records() -> list[dict]:
    if not GOLD_PARQUET.exists():
        return []
    df = pd.read_parquet(GOLD_PARQUET)
    out = []
    for _, row in df.iterrows():
        risks = row.get("risks") or []
        if isinstance(risks, str):
            risks = json.loads(risks)
        risk_vec = [1.0 if r in risks else 0.0 for r in RISK_LABELS]
        out.append({
            "text": str(row["text"]),
            "sent": SENT_IDX[row["sentiment"]],
            "fit": FIT_IDX[row["fit"]],
            "risk": risk_vec,
        })
    log.info(f"Gold yüklendi: {len(out):,} kayıt")
    return out

def compute_loss(
    logits_sent, logits_fit, logits_risk,
    sent_y, fit_y, risk_y,
    risk_pos_weight: torch.Tensor,
    alpha: float = 1.0, beta: float = 1.0, gamma: float = 0.8,
) -> tuple[torch.Tensor, dict]:

    loss_sent = F.cross_entropy(logits_sent, sent_y, ignore_index=-100, reduction="mean")
    loss_fit = F.cross_entropy(logits_fit, fit_y, ignore_index=-100, reduction="mean")

    risk_mask = (risk_y[:, 0] != -100.0)
    if risk_mask.any():
        loss_risk = F.binary_cross_entropy_with_logits(
            logits_risk[risk_mask], risk_y[risk_mask], pos_weight=risk_pos_weight, reduction="mean"
        )
    else:
        loss_risk = torch.tensor(0.0, device=logits_sent.device, requires_grad=True)

    losses = []
    parts = {}
    if not torch.isnan(loss_sent):
        losses.append(alpha * loss_sent)
        parts["sent"] = loss_sent.item()
    if not torch.isnan(loss_fit):
        losses.append(beta * loss_fit)
        parts["fit"] = loss_fit.item()
    if not torch.isnan(loss_risk):
        losses.append(gamma * loss_risk)
        parts["risk"] = loss_risk.item()

    total = sum(losses) if losses else torch.tensor(0.0, device=logits_sent.device, requires_grad=True)
    return total, parts

@torch.no_grad()
def evaluate(model, loader, device) -> dict:
    model.eval()
    all_sent_pred, all_sent_true = [], []
    all_fit_pred, all_fit_true = [], []
    all_risk_pred, all_risk_true = [], []
    for batch in loader:
        ids = batch["input_ids"].to(device)
        mask = batch["attention_mask"].to(device)
        tti = batch["token_type_ids"].to(device)
        sl, fl, rl = model(ids, mask, tti)

        sent_y = batch["sent"].cpu().numpy()
        fit_y = batch["fit"].cpu().numpy()
        risk_y = batch["risk"].cpu().numpy()

        sent_pred = sl.argmax(-1).cpu().numpy()
        fit_pred = fl.argmax(-1).cpu().numpy()
        risk_pred = (torch.sigmoid(rl).cpu().numpy() > 0.5).astype(int)

        mask_sent = sent_y != -100
        mask_fit = fit_y != -100
        mask_risk = risk_y[:, 0] != -100.0

        if mask_sent.any():
            all_sent_pred.append(sent_pred[mask_sent]); all_sent_true.append(sent_y[mask_sent])
        if mask_fit.any():
            all_fit_pred.append(fit_pred[mask_fit]); all_fit_true.append(fit_y[mask_fit])
        if mask_risk.any():
            all_risk_pred.append(risk_pred[mask_risk]); all_risk_true.append(risk_y[mask_risk])

    metrics = {}
    if all_sent_true:
        sp = np.concatenate(all_sent_pred); st = np.concatenate(all_sent_true)
        if len(st) > 0:
            metrics["sent_acc"] = float(accuracy_score(st, sp))
            metrics["sent_f1_macro"] = float(f1_score(st, sp, average="macro", zero_division=0))
    if all_fit_true:
        fp = np.concatenate(all_fit_pred); ft = np.concatenate(all_fit_true)
        if len(ft) > 0:
            metrics["fit_acc"] = float(accuracy_score(ft, fp))
            metrics["fit_f1_macro"] = float(f1_score(ft, fp, average="macro", zero_division=0))
    if all_risk_true:
        rp = np.concatenate(all_risk_pred); rt = np.concatenate(all_risk_true).astype(int)
        if len(rt) > 0:
            metrics["risk_f1_macro"] = float(f1_score(rt, rp, average="macro", zero_division=0))
            metrics["risk_f1_micro"] = float(f1_score(rt, rp, average="micro", zero_division=0))
    return metrics

class EarlyStopper:
    def __init__(self, patience: int = 2, min_delta: float = 0.001):
        self.patience = patience
        self.min_delta = min_delta
        self.best_score: float = -float("inf")
        self.bad_epochs = 0
        self.best_state: dict | None = None
        self.best_epoch: int = 0
        self.stopped: bool = False

    def step(self, model: nn.Module, score: float, epoch: int) -> bool:
        if score > self.best_score + self.min_delta:
            self.best_score = score
            self.best_epoch = epoch
            self.bad_epochs = 0

            self.best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            log.info(f"  ★ Yeni en iyi val={score:.4f} (epoch {epoch}) — checkpoint güncellendi")
            return False
        self.bad_epochs += 1
        log.info(f"  ↓ İyileşme yok (bad_epochs={self.bad_epochs}/{self.patience}, best={self.best_score:.4f} ep{self.best_epoch})")
        if self.bad_epochs >= self.patience:
            self.stopped = True
            return True
        return False

    def restore_best(self, model: nn.Module) -> None:
        if self.best_state is not None:
            model.load_state_dict(self.best_state)
            log.info(f"  ↩ En iyi checkpoint geri yüklendi (epoch {self.best_epoch}, val={self.best_score:.4f})")

def train_loop(
    model, train_loader, val_loader, device,
    epochs: int, lr: float, warmup_ratio: float = 0.1,
    risk_pos_weight: torch.Tensor | None = None,
    alpha: float = 1.0, beta: float = 1.0, gamma: float = 0.8,
    label: str = "phase",
    early_stop_metric: str = "sent_acc",
    early_stop_patience: int = 2,
) -> tuple[list[dict], EarlyStopper]:
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=lr, weight_decay=0.01,
    )
    total_steps = len(train_loader) * epochs
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=int(total_steps * warmup_ratio), num_training_steps=total_steps
    )
    if risk_pos_weight is None:
        risk_pos_weight = torch.ones(len(RISK_LABELS), device=device)

    stopper = EarlyStopper(patience=early_stop_patience)
    history = []
    for epoch in range(1, epochs + 1):
        model.train()
        start = time.monotonic()
        losses: list[float] = []
        part_acc: dict = {"sent": [], "fit": [], "risk": []}

        for step, batch in enumerate(train_loader, 1):
            ids = batch["input_ids"].to(device)
            mask = batch["attention_mask"].to(device)
            tti = batch["token_type_ids"].to(device)
            sl, fl, rl = model(ids, mask, tti)
            loss, parts = compute_loss(
                sl, fl, rl,
                batch["sent"].to(device), batch["fit"].to(device), batch["risk"].to(device),
                risk_pos_weight, alpha, beta, gamma,
            )
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            losses.append(float(loss.item()))
            for k, v in parts.items():
                part_acc[k].append(v)
            if step % max(1, len(train_loader) // 8) == 0:
                pacc = ", ".join(f"{k}={np.mean(v):.3f}" for k, v in part_acc.items() if v)
                log.info(f"  [{label} ep{epoch} {step}/{len(train_loader)}] loss={np.mean(losses[-100:]):.3f}  {pacc}")

        dur = time.monotonic() - start
        val_metrics = evaluate(model, val_loader, device) if val_loader else {}
        log.info(f"[{label} EP {epoch}/{epochs}] {dur:.0f}s  train_loss={np.mean(losses):.3f}  val={val_metrics}")
        history.append({"epoch": epoch, "train_loss": float(np.mean(losses)), "val": val_metrics})

        score = val_metrics.get(early_stop_metric)
        if score is None:

            available = [v for k, v in val_metrics.items() if k.endswith(("_acc", "_f1_macro"))]
            score = float(np.mean(available)) if available else 0.0
        if stopper.step(model, score, epoch):
            log.warning(f"⏹  ERKEN DURMA — {early_stop_patience} epoch boyunca iyileşme yok")
            break

    stopper.restore_best(model)
    return history, stopper

def weighted_sampler(records: list[dict], by_key: str = "sent") -> WeightedRandomSampler:
    counts = Counter(r[by_key] for r in records if r.get(by_key, -100) != -100)
    total = sum(counts.values())
    class_weight = {c: total / (len(counts) * cnt) for c, cnt in counts.items()}
    weights = [class_weight.get(r.get(by_key), 0.0) for r in records]
    return WeightedRandomSampler(weights, num_samples=len(records), replacement=True)

def combined_sampler(records: list[dict]) -> WeightedRandomSampler:
    sent_c = Counter(r["sent"] for r in records if r.get("sent", -100) != -100)
    fit_c = Counter(r["fit"] for r in records if r.get("fit", -100) != -100)
    s_total = sum(sent_c.values())
    f_total = sum(fit_c.values())
    s_w = {c: s_total / (len(sent_c) * n) for c, n in sent_c.items()}
    f_w = {c: f_total / (len(fit_c) * n) for c, n in fit_c.items()}
    weights = [s_w.get(r.get("sent"), 0.0) * f_w.get(r.get("fit"), 0.0) for r in records]
    return WeightedRandomSampler(weights, num_samples=len(records), replacement=True)

def stratified_split(records: list[dict], val_ratio: float, key: str, seed: int = 2026) -> tuple[list[dict], list[dict]]:
    valid = [r for r in records if r.get(key, -100) != -100]
    if len(valid) < 10:

        np.random.seed(seed)
        idx = np.random.permutation(len(records))
        val_n = max(1, int(val_ratio * len(records)))
        return [records[i] for i in idx[val_n:]], [records[i] for i in idx[:val_n]]

    labels = [r[key] for r in valid]
    train_recs, val_recs = train_test_split(
        valid, test_size=val_ratio, stratify=labels, random_state=seed
    )
    return train_recs, val_recs

def compute_risk_pos_weight(records: list[dict]) -> torch.Tensor:
    n = len(records)
    pw = []
    for i in range(len(RISK_LABELS)):
        pos = sum(1 for r in records if isinstance(r.get("risk"), list) and r["risk"][i] == 1.0)
        neg = n - pos
        pw.append(neg / max(pos, 1))
    return torch.tensor(pw, dtype=torch.float)

def main():
    global BASE_MODEL
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", type=int, default=0, choices=[0, 1, 2], help="0=tümü, 1=warm-start, 2=joint")
    ap.add_argument("--epochs-warm", type=int, default=4, help="warm-start max epoch (early-stop bekler)")
    ap.add_argument("--epochs-joint", type=int, default=6, help="joint max epoch (early-stop bekler)")
    ap.add_argument("--patience", type=int, default=2, help="early-stop patience (epoch)")
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--max-len", type=int, default=128)
    ap.add_argument("--lr-warm", type=float, default=2e-5)
    ap.add_argument("--lr-joint", type=float, default=2e-5)
    ap.add_argument("--base-model", type=str, default=BASE_MODEL,
                    help="HF model id (örn: dbmdz/convbert-base-turkish-cased veya dbmdz/bert-base-turkish-cased)")
    ap.add_argument("--debug", action="store_true", help="küçük subset + 1 epoch")
    args = ap.parse_args()

    BASE_MODEL = args.base_model
    log.info(f"Base model: {BASE_MODEL}")

    device = torch.device("mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu"))
    log.info(f"Cihaz: {device}")

    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    if args.phase in (0, 1):
        log.info("=" * 60)
        log.info("FAZ 1 — Warm-start (HF Türkçe yorumlar, sadece sent head)")
        log.info("=" * 60)

        hf_records = load_hf_records()
        if args.debug:
            hf_records = hf_records[:2000]

        train_recs, val_recs = stratified_split(hf_records, val_ratio=0.05, key="sent")
        log.info(f"  train: {len(train_recs):,}  val: {len(val_recs):,}  (stratified by sent)")

        from collections import Counter as _C
        log.info(f"  train sent: {dict(_C(r['sent'] for r in train_recs))}")
        log.info(f"  val   sent: {dict(_C(r['sent'] for r in val_recs))}")

        train_ds = MultiTaskDataset(train_recs, tokenizer, args.max_len)
        val_ds = MultiTaskDataset(val_recs, tokenizer, args.max_len)
        sampler = weighted_sampler(train_recs, by_key="sent")
        train_loader = DataLoader(train_ds, batch_size=args.batch, sampler=sampler, num_workers=0)
        val_loader = DataLoader(val_ds, batch_size=args.batch * 2, num_workers=0)

        model = BERTurkMultiTask().to(device)
        freeze_encoder_except_last_n(model, n=2)

        epochs = 1 if args.debug else args.epochs_warm
        hist1, stopper1 = train_loop(
            model, train_loader, val_loader, device,
            epochs=epochs, lr=args.lr_warm,
            alpha=1.0, beta=0.0, gamma=0.0,
            label="WARM",
            early_stop_metric="sent_acc",
            early_stop_patience=args.patience,
        )

        ckpt_path = MODEL_DIR / "phase1_state.pt"
        torch.save(model.state_dict(), ckpt_path)
        log.info(f"Faz 1 model: {ckpt_path}")
        with open(MODEL_DIR / "metrics_phase1.json", "w") as f:
            json.dump(hist1, f, ensure_ascii=False, indent=2)

    if args.phase in (0, 2):
        log.info("=" * 60)
        log.info("FAZ 2 — Joint (Qwen + gold, 3 head birden)")
        log.info("=" * 60)

        qwen_records = load_qwen_records()
        if len(qwen_records) < 50:
            log.error(f"Çok az Qwen verisi ({len(qwen_records)}) — labelig henüz bitmedi mi?")
            return

        gold_records = load_gold_records()

        train_recs, val_recs = stratified_split(qwen_records, val_ratio=0.1, key="sent")
        val_recs = val_recs + gold_records
        log.info(f"  train: {len(train_recs):,}  val: {len(val_recs):,} (gold {len(gold_records)} dahil)  (stratified by sent)")
        from collections import Counter as _C
        log.info(f"  train sent: {dict(_C(r['sent'] for r in train_recs))}")
        log.info(f"  train fit : {dict(_C(r['fit'] for r in train_recs))}")
        log.info(f"  val   sent: {dict(_C(r['sent'] for r in val_recs))}")

        if args.debug:
            train_recs = train_recs[:300]

        train_ds = MultiTaskDataset(train_recs, tokenizer, args.max_len)
        val_ds = MultiTaskDataset(val_recs, tokenizer, args.max_len)

        sampler = combined_sampler(train_recs)
        train_loader = DataLoader(train_ds, batch_size=args.batch, sampler=sampler, num_workers=0)
        val_loader = DataLoader(val_ds, batch_size=args.batch * 2, num_workers=0)

        model = BERTurkMultiTask().to(device)

        ckpt = MODEL_DIR / "phase1_state.pt"
        if ckpt.exists():
            state = torch.load(ckpt, map_location=device, weights_only=True)
            model.load_state_dict(state)
            log.info(f"Faz 1 checkpoint yüklendi: {ckpt}")
        unfreeze_all(model)

        risk_pw = compute_risk_pos_weight(train_recs).to(device)
        log.info(f"Risk pos_weight: {dict(zip(RISK_LABELS, risk_pw.cpu().tolist()))}")

        epochs = 1 if args.debug else args.epochs_joint

        hist2, stopper2 = train_loop(
            model, train_loader, val_loader, device,
            epochs=epochs, lr=args.lr_joint,
            risk_pos_weight=risk_pw,
            alpha=1.0, beta=1.0, gamma=0.8,
            label="JOINT",
            early_stop_metric="sent_f1_macro",
            early_stop_patience=args.patience,
        )

        torch.save(model.state_dict(), MODEL_DIR / "pytorch_model.bin")
        tokenizer.save_pretrained(MODEL_DIR / "tokenizer")
        with open(MODEL_DIR / "labels.json", "w", encoding="utf-8") as f:
            json.dump({
                "base_model": BASE_MODEL,
                "sentiment": SENT_LABELS,
                "fit": FIT_LABELS,
                "risk": RISK_LABELS,
            }, f, ensure_ascii=False, indent=2)
        with open(MODEL_DIR / "metrics.json", "w", encoding="utf-8") as f:
            json.dump({"phase2": hist2, "final": hist2[-1] if hist2 else {}}, f, ensure_ascii=False, indent=2)
        log.info(f"Final model: {MODEL_DIR}/pytorch_model.bin")

if __name__ == "__main__":
    main()
