import logging
from pathlib import Path

import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger("kanka.berturk")

SENT_LABELS = ["positive", "neutral", "negative"]
FIT_LABELS = ["tam", "kucuk", "buyuk", "belirsiz"]
RISK_LABELS = ["kumas", "renk", "kalite", "kargo", "koku", "gorsel"]

class BERTurkMultiTask(nn.Module):
    def __init__(self, model_name: str = "dbmdz/convbert-base-turkish-cased"):
        super().__init__()
        self.bert = AutoModel.from_pretrained(model_name)
        hidden = self.bert.config.hidden_size
        self.dropout = nn.Dropout(0.1)
        self.head_sent = nn.Linear(hidden, len(SENT_LABELS))
        self.head_fit = nn.Linear(hidden, len(FIT_LABELS))
        self.head_risk = nn.Linear(hidden, len(RISK_LABELS))

    def forward(self, input_ids, attention_mask, token_type_ids=None):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask, token_type_ids=token_type_ids)
        pooled = self.dropout(out.last_hidden_state[:, 0])
        return self.head_sent(pooled), self.head_fit(pooled), self.head_risk(pooled)

class BERTurkInferencer:
    def __init__(self, model: BERTurkMultiTask, tokenizer, device: torch.device):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.model.eval()

    async def infer_batch(self, texts: list[str], batch_size: int = 8) -> list[dict]:
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            enc = self.tokenizer(
                batch,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128,
            ).to(self.device)
            with torch.no_grad():
                sent_logits, fit_logits, risk_logits = self.model(**enc)
            sent_probs = torch.softmax(sent_logits, dim=-1).cpu().tolist()
            fit_probs = torch.softmax(fit_logits, dim=-1).cpu().tolist()
            risk_probs = torch.sigmoid(risk_logits).cpu().tolist()
            for j in range(len(batch)):
                row = {
                    "sent_label": SENT_LABELS[int(torch.argmax(sent_logits[j]))],
                    "sent_pos": sent_probs[j][0],
                    "sent_neu": sent_probs[j][1],
                    "sent_neg": sent_probs[j][2],
                    "fit_label": FIT_LABELS[int(torch.argmax(fit_logits[j]))],
                    "fit_tam": fit_probs[j][0],
                    "fit_kucuk": fit_probs[j][1],
                    "fit_buyuk": fit_probs[j][2],
                    "fit_unknown": fit_probs[j][3],
                }
                for k, rl in enumerate(RISK_LABELS):
                    row[f"risk_{rl}"] = risk_probs[j][k]
                results.append(row)
        return results

async def load_berturk(model_dir: str) -> BERTurkInferencer | None:
    model_path = Path(model_dir) / "berturk_multitask"
    if not model_path.exists() or not (model_path / "pytorch_model.bin").exists():
        return None

    device = torch.device(
        "mps" if torch.backends.mps.is_available()
        else ("cuda" if torch.cuda.is_available() else "cpu")
    )

    tokenizer_dir = model_path / "tokenizer"
    tokenizer = AutoTokenizer.from_pretrained(str(tokenizer_dir if tokenizer_dir.exists() else model_path))

    import json
    base = "dbmdz/convbert-base-turkish-cased"
    labels_path = model_path / "labels.json"
    if labels_path.exists():
        with open(labels_path, encoding="utf-8") as f:
            base = json.load(f).get("base_model", base)

    model = BERTurkMultiTask(base)
    state = torch.load(model_path / "pytorch_model.bin", map_location=device, weights_only=True)
    model.load_state_dict(state, strict=True)
    model.to(device)

    logger.info(f"BERTurk yüklendi ({device}, base={base})")
    return BERTurkInferencer(model, tokenizer, device)
