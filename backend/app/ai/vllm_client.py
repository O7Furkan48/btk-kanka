import asyncio
import logging

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger("kanka.vllm")

SEM = asyncio.Semaphore(16)

_client: AsyncOpenAI | None = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            api_key="EMPTY",
            base_url=settings.vllm_base_url,
            timeout=60.0,
            max_retries=3,
        )
    return _client

SYS_PROMPT = """Sen bir Türkçe e-ticaret yorumu sınıflandırıcısısın. Her yorum için aşağıdaki
4 alanı dolduran TEK BİR JSON nesnesi döndür. Aşağıdaki JSON formatını birebir
kullan, field isimlerini ve sıralamasını değiştirme. Yorum dışı bilgi ekleme,
düşünme adımı yazma, sadece JSON döndür.

{
  "sentiment": "positive",
  "fit":       "tam",
  "risks":     [],
  "confidence": 0.9
}

sentiment değerleri: "positive" | "neutral" | "negative"
fit değerleri: "tam" | "kucuk" | "buyuk" | "belirsiz"
risks değerleri: ["kumas", "renk", "kalite", "kargo", "koku"] // sıfır veya fazlası

Kurallar:
- "kucuk" = beden olduğundan küçük geldi
- "buyuk" = bol/geniş durdu
- "tam" = yerli yerinde oturuyor
- "belirsiz" = beden hakkında bilgi yok
- risks sadece yorumda dile getirilen olumsuz sinyaller (pozitif yorumda boş).
- confidence düşükse 0.4 altında bırak; kararsızsan "neutral" + "belirsiz" + []."""

class QwenLabel(BaseModel):
    sentiment: str
    fit: str
    risks: list[str]
    confidence: float

def _user_prompt(review: dict) -> str:
    lines = [f'Yorum: "{review.get("yorum_metni", "")}"']
    if review.get("kategori"):
        lines.append(f'Ürün kategorisi: {review["kategori"]}')
    if review.get("beden"):
        parts = [f'Beden: {review["beden"]}']
        if review.get("boy"):
            parts.append(f'Boy: {review["boy"]}cm')
        if review.get("kilo"):
            parts.append(f'Kilo: {review["kilo"]}kg')
        lines.append(", ".join(parts))
    return "\n".join(lines)

async def label_one(review: dict) -> QwenLabel | None:
    async with SEM:
        try:
            completion = await get_client().chat.completions.create(
                model="Qwen/Qwen3.5-9B",
                messages=[
                    {"role": "system", "content": SYS_PROMPT},
                    {"role": "user", "content": _user_prompt(review)},
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
            return QwenLabel.model_validate_json(completion.choices[0].message.content)
        except Exception as e:
            logger.warning(f"vLLM label hatası: {e}")
            return None
