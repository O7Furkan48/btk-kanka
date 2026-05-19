from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import statistics
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import pandas as pd
from openai import APIError, APITimeoutError, AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError
from tqdm.asyncio import tqdm as tqdm_async

BACKEND_DIR = Path(__file__).parent.parent
DATA_DIR = BACKEND_DIR / "app" / "data"
REVIEWS_PARQUET = DATA_DIR / "reviews.parquet"
PRODUCTS_JSON = DATA_DIR / "products.json"
OUT_JSONL = DATA_DIR / "reviews_qwen.jsonl"
FAILED_JSONL = DATA_DIR / "reviews_qwen_failed.jsonl"

sys.path.insert(0, str(BACKEND_DIR))
from app.config import settings  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("label")

SENT = Literal["positive", "neutral", "negative"]
FIT = Literal["tam", "kucuk", "buyuk", "belirsiz"]
RISK = Literal["kumas", "renk", "kalite", "kargo", "koku", "gorsel"]

class QwenLabel(BaseModel):
    sentiment: SENT
    fit: FIT
    risks: list[RISK] = []
    confidence: float = Field(ge=0.0, le=1.0)

SYS_PROMPT = """Sen bir Türkçe e-ticaret yorumu sınıflandırıcısısın. Her yorum için TEK BİR JSON nesnesi döndür. SADECE JSON döndür; düşünme adımı, açıklama, markdown yazma.

ŞEMA:
{
  "sentiment": "positive" | "neutral" | "negative",
  "fit":       "tam" | "kucuk" | "buyuk" | "belirsiz",
  "risks":     ["kumas"|"renk"|"kalite"|"kargo"|"koku"|"gorsel"],
  "confidence": 0.0-1.0
}

═══════════════ SENTIMENT ═══════════════
Tek bir GÜÇLÜ pozitif veya negatif sinyal varsa NEUTRAL DEĞİL, kararı ver.

- positive : olumlu/memnun ifade (güzel, harika, süper, mükemmel, bayıldım,
             tavsiye ederim, kaliteli, beğendim, çok iyi). "Süper", "harika",
             "tavsiye ederim" varsa positive.
- negative : olumsuz/şikayet (kötü, berbat, iade ettim/edeceğim, hayal kırıklığı,
             parama yazık, beğenmedim, kalitesiz, rezalet, sahte). "İade" kelimesi
             bir nedenle birlikte geçiyorsa genelde negative.
- neutral  : Yalnızca bilgi paylaşımı (boy/kilo + beden bildirimi),
             ya da hem güçlü pozitif hem güçlü negatif içeren karışık yorum,
             ya da kararsızlık ("idare eder", "fena değil ama")

═══════════════ FIT ═══════════════ (sadece giyim/ayakkabı/aksesuar bedenli)
- tam     : doğru oturdu (oldu, tam, uyuyor, fit, "tam oldu")
- kucuk   : küçük/dar geldi ("dar", "sıktı", "küçük geldi", "bir beden büyük alın")
- buyuk   : büyük/bol/geniş geldi ("bol", "geniş", "çıkıyordu", "bir beden küçük alın")
- belirsiz: beden bilgisi yok, ya da ürün bedenli değil (çanta, kozmetik, ev)

═══════════════ RISKS (multi-label) ═══════════════
Yalnızca olumsuz sinyaller; net pozitif yorumda HEP boş [].
Her risk ayrı bağımsız; aynı yorumda birkaçı olabilir.

- kumas  : kumaş kalitesi şikayeti — kalın, ince, ucuz, plastik, sentetik gibi,
           kaşındırıyor, deri sahte, polyester benzeri
- renk   : renk farkı/soluk — "rengi farklı geldi", "soldu", "görseldeki rengi
           değil", "tonu farklı". (Sadece RENGE özel; ürünün başka boyutları için
           "gorsel" kullan.)
- kalite : dikiş/yapım/dayanıklılık + KIRIK/HASARLI ürün + YANLIŞ ürün +
           çabuk yıprandı, çabuk söküldü, kopuk iplik, çürümüş, deforme,
           "yüzük istedim küpe geldi", parçası eksik, defolu, ayakların biri
           sıktı diğeri olmadı (üretim tutarsızlığı)
- kargo  : geç teslimat, kargo süreç şikayeti, hasarlı paket, yanlış adres
           (paketin içindeki ürün hasarı kalite altına gider)
- koku   : kötü/yoğun/kimyasal koku, naylon kokusu, balık kokusu vs.
- gorsel : ÜRÜN GÖRSELLE/AÇIKLAMAYLA UYUMSUZ — "fotoğraftakinden küçük/büyük",
           "modeldeki gibi durmuyor", "yüksek bel diye aldım düşük bel geldi",
           "açıklamasındakinden farklı", "reklamdaki gibi değil",
           "manken üzerinde başka türlü", "bambaşka bir ürün geldi"
           (Bu RENK farkı DEĞİL — kesim/şekil/açıklama uyumsuzluğu)

═══════════════ CONFIDENCE ═══════════════
- 0.9+    : çok net (tek anlamlı yorum)
- 0.6-0.9 : emin ama küçük nüans var
- 0.4-0.6 : zor karar
- <0.4    : emin değilsen → "neutral" + "belirsiz" + [] döndür

═══════════════ ÖRNEKLER ═══════════════
"kazağı çok beğendim. yumuşak, sıcak tutuyor, M aldım tam oldu"
{"sentiment":"positive","fit":"tam","risks":[],"confidence":0.95}

"kumaşı kalitesizmiş, ince ve şeffaf. ayrıca kargo geç geldi"
{"sentiment":"negative","fit":"belirsiz","risks":["kumas","kargo"],"confidence":0.9}

"yüksek bel diye aldım ama düşük bel geldi için iade"
{"sentiment":"negative","fit":"belirsiz","risks":["gorsel"],"confidence":0.9}

"fotoğraftakinden baya küçük, modeldeki gibi durmuyor"
{"sentiment":"negative","fit":"belirsiz","risks":["gorsel"],"confidence":0.9}

"yüzük istedim küpe geldi üstelik küpenin birisi kırık"
{"sentiment":"negative","fit":"belirsiz","risks":["kalite"],"confidence":0.95}

"süper bir ürün tavsiye ederim, kalıbı tam oldu"
{"sentiment":"positive","fit":"tam","risks":[],"confidence":0.95}

"182 80 L aldım dar geldi"
{"sentiment":"neutral","fit":"kucuk","risks":[],"confidence":0.85}
"""

def user_prompt(review: dict, category: str | None) -> str:
    lines = [f'Yorum: "{review["yorum_metni"]}"']
    if category:
        lines.append(f"Ürün kategorisi: {category}")
    beden = review.get("beden")
    if beden and pd.notna(beden) and str(beden).strip():
        parts = [f'Beden: {beden}']
        boy = review.get("boy")
        if boy is not None and pd.notna(boy):
            parts.append(f"Boy: {int(boy)}cm")
        kilo = review.get("kilo")
        if kilo is not None and pd.notna(kilo):
            parts.append(f"Kilo: {int(kilo)}kg")
        lines.append("Profil: " + ", ".join(parts))
    return "\n".join(lines)

def load_completed(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    bozuk = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "id" in obj and "error" not in obj:
                    ids.add(obj["id"])
            except json.JSONDecodeError:
                bozuk += 1
    if bozuk:
        log.warning(f"{bozuk} bozuk satır atlandı (crash artığı)")
    return ids

class JsonlWriter:

    def __init__(self, path: Path):
        self.path = path
        self.f = open(path, "a", encoding="utf-8")
        self.lock = asyncio.Lock()
        self.count = 0

    async def write(self, obj: dict) -> None:
        line = json.dumps(obj, ensure_ascii=False)
        async with self.lock:
            self.f.write(line + "\n")
            self.f.flush()
            self.count += 1

    def close(self) -> None:
        try:
            self.f.flush()
            self.f.close()
        except Exception:
            pass

NEGATIVE_KW = [
    "iade", "berbat", "tavsiye etme", "kötü", "kalitesiz",
    "memnun değil", "para tuzağı", "rezalet", "boşa para",
    "hayal kırıklığı", "parama yazık", "yıkadım bitti", "yıkamayla",
]

def select_sample(reviews: pd.DataFrame, n: int, neg_ratio: float = 0.3) -> pd.DataFrame:
    df = reviews[reviews["yorum_metni"].astype(str).str.len() >= 20].copy()

    pattern = "|".join(NEGATIVE_KW)
    neg_mask = df["yorum_metni"].astype(str).str.contains(pattern, case=False, regex=True, na=False)

    rnd_neg = random.Random(2026)
    rnd_pos = random.Random(2027)

    neg_ids = sorted(df.loc[neg_mask, "id"].tolist())
    rnd_neg.shuffle(neg_ids)

    pos_ids = sorted(df.loc[~neg_mask, "id"].tolist())
    rnd_pos.shuffle(pos_ids)

    n_neg = min(int(round(n * neg_ratio)), len(neg_ids))
    n_pos = n - n_neg

    chosen = set(neg_ids[:n_neg]) | set(pos_ids[:n_pos])
    out = df[df["id"].isin(chosen)].copy()
    log.info(f"Seçildi: {len(out):,} ({n_neg} negatif-seed + {n_pos} rastgele)")
    return out.reset_index(drop=True)

async def label_one(
    client: AsyncOpenAI,
    sem: asyncio.Semaphore,
    review: dict,
    category: str | None,
    retries: int = 2,
) -> tuple[dict | None, dict | None]:
    start = time.monotonic()
    last_err: str | None = None
    last_raw: str | None = None

    for attempt in range(retries + 1):
        async with sem:
            try:
                completion = await client.chat.completions.create(
                    model="Qwen/Qwen3.5-9B",
                    messages=[
                        {"role": "system", "content": SYS_PROMPT},
                        {"role": "user", "content": user_prompt(review, category)},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    top_p=0.8,
                    max_tokens=256,
                    extra_body={
                        "top_k": 20,
                        "chat_template_kwargs": {"enable_thinking": False},
                    },
                )
            except (APITimeoutError, APIError) as e:
                last_err = f"api/{type(e).__name__}: {str(e)[:200]}"
                continue
            except Exception as e:
                last_err = f"unexpected/{type(e).__name__}: {str(e)[:200]}"
                continue

        raw = completion.choices[0].message.content or ""
        last_raw = raw
        try:
            label = QwenLabel.model_validate_json(raw)
        except (ValidationError, json.JSONDecodeError) as e:
            last_err = f"parse: {str(e)[:200]}"
            break

        latency_ms = int((time.monotonic() - start) * 1000)
        return (
            {
                "id": review["id"],
                "sentiment": label.sentiment,
                "fit": label.fit,
                "risks": label.risks,
                "confidence": label.confidence,
                "latency_ms": latency_ms,
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
            None,
        )

    return (
        None,
        {
            "id": review["id"],
            "error": last_err or "bilinmiyor",
            "raw": (last_raw or "")[:300],
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    )

async def run_labeling(n: int, concurrency: int) -> None:
    sem = asyncio.Semaphore(concurrency)
    client = AsyncOpenAI(
        api_key="EMPTY",
        base_url=settings.vllm_base_url,
        timeout=90.0,
        max_retries=0,
    )

    log.info("reviews.parquet okunuyor…")
    reviews = pd.read_parquet(REVIEWS_PARQUET)
    log.info(f"  {len(reviews):,} yorum")

    log.info("products.json okunuyor (kategori map için)…")
    with open(PRODUCTS_JSON, encoding="utf-8") as f:
        products = json.load(f)
    cat_map = {
        p["slug"]: " > ".join(c["label"] for c in p.get("category", [])[:3])
        for p in products
    }

    sample = select_sample(reviews, n)

    completed = load_completed(OUT_JSONL)
    log.info(f"Mevcut etiketli: {len(completed):,}")

    remaining_df = sample[~sample["id"].isin(completed)]
    remaining = remaining_df.to_dict("records")
    log.info(f"Kalan: {len(remaining):,}")

    if not remaining:
        log.info("Hiç kalmadı, rapora geçiyorum.")
        await client.close()
        print_report()
        return

    out_writer = JsonlWriter(OUT_JSONL)
    fail_writer = JsonlWriter(FAILED_JSONL)
    start = time.monotonic()

    pbar = tqdm_async(total=len(remaining), desc="Etiketleme", unit="yorum")

    async def worker(review: dict) -> None:
        cat = cat_map.get(review.get("urun_slug"))
        label, fail = await label_one(client, sem, review, cat)
        if label is not None:
            await out_writer.write(label)
        else:
            await fail_writer.write(fail)
        pbar.update(1)

    tasks = [asyncio.create_task(worker(r)) for r in remaining]
    try:
        await asyncio.gather(*tasks, return_exceptions=False)
    except asyncio.CancelledError:
        log.warning("İptal — in-flight task'lar drain ediliyor…")
    except KeyboardInterrupt:
        log.warning("Ctrl+C — task'lar iptal ediliyor, mevcut sonuçlar korundu.")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    finally:
        pbar.close()
        out_writer.close()
        fail_writer.close()
        await client.close()

    duration = time.monotonic() - start
    rate = len(remaining) / duration if duration > 0 else 0
    log.info(f"Bitti — {duration:.1f} sn ({rate:.1f} yorum/sn)")
    print_report()

def print_report() -> None:
    labels: list[dict] = []
    if OUT_JSONL.exists():
        with open(OUT_JSONL, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    labels.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    failed: list[dict] = []
    if FAILED_JSONL.exists():
        with open(FAILED_JSONL, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    failed.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if not labels and not failed:
        log.warning("Hiç sonuç yok.")
        return

    def pct(c: int, t: int) -> str:
        return f"%{100*c/t:5.1f}" if t else "  -  "

    sent_dist = Counter(l["sentiment"] for l in labels)
    fit_dist = Counter(l["fit"] for l in labels)
    risk_dist: Counter = Counter()
    no_risk = 0
    for l in labels:
        rs = l.get("risks", [])
        if not rs:
            no_risk += 1
        for r in rs:
            risk_dist[r] += 1

    confs = [l["confidence"] for l in labels if "confidence" in l]
    lats = [l["latency_ms"] for l in labels if "latency_ms" in l]

    total = len(labels) + len(failed)
    print(f"\n{'='*62}")
    print(f"BAŞARILI: {len(labels):>5,}   BAŞARISIZ: {len(failed):>5,}   TOPLAM: {total:>5,}")
    if total:
        print(f"Hata oranı: {pct(len(failed), total)}")

    print(f"\nSENTIMENT:")
    for k in ("positive", "neutral", "negative"):
        v = sent_dist.get(k, 0)
        bar = "█" * int(40 * v / max(len(labels), 1))
        print(f"  {k:9} {v:>5,}  {pct(v, len(labels))}  {bar}")

    print(f"\nFIT:")
    for k in ("tam", "kucuk", "buyuk", "belirsiz"):
        v = fit_dist.get(k, 0)
        bar = "█" * int(40 * v / max(len(labels), 1))
        print(f"  {k:9} {v:>5,}  {pct(v, len(labels))}  {bar}")

    print(f"\nRISK (multi-label, sıfır risk: {no_risk}/{len(labels)}):")
    for k in ("kumas", "renk", "kalite", "kargo", "koku", "gorsel"):
        v = risk_dist.get(k, 0)
        bar = "█" * int(40 * v / max(len(labels), 1))
        print(f"  {k:8} {v:>5,}  {pct(v, len(labels))}  {bar}")

    if confs:
        print(f"\nCONFIDENCE:")
        print(f"  ortalama: {statistics.mean(confs):.2f}")
        print(f"  medyan  : {statistics.median(confs):.2f}")
        print(f"  <0.4    : {sum(1 for c in confs if c < 0.4):,}")
        print(f"  ≥0.8    : {sum(1 for c in confs if c >= 0.8):,}")

    if lats:
        print(f"\nLATENCY (ms):")
        print(f"  ortalama: {statistics.mean(lats):.0f}")
        print(f"  medyan  : {statistics.median(lats):.0f}")
        if len(lats) >= 20:
            qs = statistics.quantiles(lats, n=20)
            print(f"  p95     : {qs[18]:.0f}")

    print(f"\nÖRNEK ETIKETLER:")
    for l in labels[:3]:
        print(f"  id={l['id']}  sent={l['sentiment']:8} fit={l['fit']:8} risks={l['risks']}  conf={l['confidence']:.2f}")
    if failed:
        print(f"\nÖRNEK HATALAR:")
        for f in failed[:3]:
            print(f"  id={f['id']}  err={f['error'][:80]}")
    print(f"{'='*62}\n")

def main() -> None:
    ap = argparse.ArgumentParser(description="vLLM Qwen3.5-9B ile yorum etiketleme")
    ap.add_argument("--n", type=int, default=100, help="örneklem boyutu (varsayılan 100)")
    ap.add_argument("--concurrency", type=int, default=16, help="paralel istek sayısı")
    ap.add_argument("--report", action="store_true", help="sadece mevcut sonuçların raporu")
    ap.add_argument("--reset", action="store_true", help="JSONL'i sıfırla (DİKKAT!)")
    args = ap.parse_args()

    if args.reset:
        for p in (OUT_JSONL, FAILED_JSONL):
            if p.exists():
                p.unlink()
                log.info(f"Silindi: {p.name}")

    if args.report:
        print_report()
        return

    try:
        asyncio.run(run_labeling(args.n, args.concurrency))
    except KeyboardInterrupt:
        log.warning("Çıkış (Ctrl+C). Kaydedilenler korundu, --report ile bakabilirsin.")

if __name__ == "__main__":
    main()
