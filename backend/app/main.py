import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import close_db, init_db
from app.errors import KankaError, kanka_error_handler

logger = logging.getLogger("kanka")

_state: dict = {}

@asynccontextmanager
async def lifespan(app: FastAPI):

    logging.basicConfig(level=logging.INFO if settings.is_dev else logging.WARNING)
    logger.info("Kanka backend başlatılıyor…")

    await init_db()
    logger.info("PostgreSQL havuzu hazır")

    data_dir = Path(__file__).parent / "data"
    products_path = data_dir / "products.json"
    if products_path.exists():
        with open(products_path, encoding="utf-8") as f:
            _state["products"] = {p["slug"]: p for p in json.load(f)}
        logger.info(f"{len(_state['products'])} ürün belleğe alındı")
    else:
        _state["products"] = {}
        logger.warning("products.json bulunamadı — ETL henüz koşulmamış")

    for fname in ("risk.json", "size_advice.json", "seller_quality.json", "trend.json"):
        fpath = data_dir / fname
        key = fname.replace(".json", "")
        if fpath.exists():
            with open(fpath, encoding="utf-8") as f:
                _state[key] = json.load(f)
            logger.info(f"{fname} yüklendi")
        else:
            _state[key] = {}

    try:
        from app.ai.berturk import load_berturk
        _state["berturk"] = await load_berturk(settings.model_dir)
        if _state["berturk"] is not None:
            logger.info("BERTurk modeli hazır")
        else:
            logger.info("BERTurk modeli HENÜZ YOK — eğitim koşulmamış")
    except Exception as e:
        _state["berturk"] = None
        logger.warning(f"BERTurk yüklenemedi: {e}")

    try:
        from app.ai.retrieval import load_retrieval
        _state["retrieval"] = await load_retrieval(settings.chroma_dir)
        if _state["retrieval"] is not None:
            logger.info("BGE-M3 + ChromaDB hazır")
        else:
            logger.info("Retrieval HENÜZ YOK — ingest_chroma.py koşulmamış")
    except Exception as e:
        _state["retrieval"] = None
        logger.warning(f"Retrieval katmanı yüklenemedi: {e}")

    try:
        from app.ai.gemini import init_gemini
        _state["gemini_client"] = init_gemini(settings.google_api_key)
        if _state["gemini_client"]:
            logger.info("Gemini client hazır")
    except Exception as e:
        _state["gemini_client"] = None
        logger.warning(f"Gemini başlatılamadı: {e}")

    app.state.ctx = _state
    logger.info("Kanka backend hazır ✓")

    yield

    await close_db()
    logger.info("Kanka backend kapandı")

app = FastAPI(
    title="Kanka AI Alışveriş Asistanı",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+)(:\d+)?",
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

app.add_exception_handler(KankaError, kanka_error_handler)  # type: ignore[arg-type]

from app.routes import cart, categories, chat, compare, products, qa, reviews, seller

app.include_router(categories.router, prefix="/api")
app.include_router(products.router, prefix="/api")
app.include_router(reviews.router, prefix="/api")
app.include_router(qa.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(seller.router, prefix="/api")
app.include_router(compare.router, prefix="/api")

@app.get("/api/health")
async def health():
    return {"durum": "ok", "ürün_sayisi": len(_state.get("products", {}))}
