import asyncio
import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.errors import kanka_error
from app.schemas import ChatRequest

router = APIRouter()
logger = logging.getLogger("kanka.chat")

async def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

def _friendly_error_message(err: Exception) -> str:
    s = str(err).lower()
    if "429" in s or "resource_exhausted" in s or "quota" in s:

        import re as _re
        m = _re.search(r"retry in\s*(\d+)\s*[a-z]*", s)
        if m:
            secs = m.group(1)
            return (
                f"Bugünkü AI kotası doldu — Gemini servisi {secs} saniye sonra tekrar açılacak. "
                "O zamana kadar diğer hızlı eylemleri veya ürün açıklamasını inceleyebilirsin."
            )
        return (
            "Bugünkü AI kotası doldu (saatlik limit aşıldı). Birkaç dakika sonra tekrar dene; "
            "bu süreçte 'Detaylı anlat' veya 'Kombinleri Bul' butonlarını da deneyebilirsin."
        )
    if "deadline" in s or "timeout" in s:
        return "AI cevap için biraz fazla zaman aldı. Daha kısa bir soruyla tekrar dener misin?"
    if "safety" in s or "blocked" in s:
        return "Bu konu için cevap üretemedim. Sorunu biraz farklı şekilde sorabilir misin?"
    return "Hımm, şu an cevap üretemedim. Bir dakka sonra dener misin?"

async def _stream_chat(slug: str, message: str, history: list, ctx: dict):
    products = ctx.get("products", {})
    if slug not in products:
        yield await _sse_event("error", {"mesaj": "Ürün bulunamadı."})
        return

    gemini = ctx.get("gemini_client")
    if gemini is None:

        yield await _sse_event("token", {"text": "Merhaba! "})
        await asyncio.sleep(0.05)
        yield await _sse_event("token", {"text": "Gemini henüz bağlanmadı, ama buradayım 😊"})
        yield await _sse_event("done", {})
        return

    try:
        from app.ai.gemini import stream_chat
        async for event_type, payload in stream_chat(gemini, slug, message, history, ctx):
            yield await _sse_event(event_type, payload)
    except Exception as e:
        logger.error(f"Gemini hatası: {e}")
        msg = _friendly_error_message(e)
        yield await _sse_event("token", {"text": msg})
        yield await _sse_event("done", {})

@router.post("/chat/stream")
async def chat_stream(body: ChatRequest, request: Request):
    ctx = request.app.state.ctx

    return StreamingResponse(
        _stream_chat(body.slug, body.message, body.history, ctx),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )

async def _stream_combo(slug: str, extra_hint: str, ctx: dict):
    products = ctx.get("products", {})
    if slug not in products:
        yield await _sse_event("error", {"mesaj": "Ürün bulunamadı."})
        return

    gemini = ctx.get("gemini_client")
    if gemini is None:
        yield await _sse_event("token", {"text": "Şu an kombin servisi hazır değil, birazdan tekrar dene."})
        yield await _sse_event("done", {})
        return

    try:
        from app.ai.gemini import stream_combo_chat
        async for event_type, payload in stream_combo_chat(gemini, slug, ctx, extra_hint):
            yield await _sse_event(event_type, payload)
    except Exception as e:
        logger.error(f"Combo Gemini hatası: {e}")
        msg = _friendly_error_message(e)
        yield await _sse_event("token", {"text": msg})
        yield await _sse_event("done", {})

@router.post("/chat/combo-stream")
async def chat_combo_stream(body: ChatRequest, request: Request):
    ctx = request.app.state.ctx

    return StreamingResponse(
        _stream_combo(body.slug, body.message or "", ctx),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
