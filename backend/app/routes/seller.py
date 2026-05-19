from fastapi import APIRouter, Request

from app.errors import kanka_error

router = APIRouter()

@router.get("/products/{slug}/seller-quality")
async def seller_quality(slug: str, request: Request):
    products = request.app.state.ctx.get("products", {})
    if slug not in products:
        raise kanka_error("urun_bulunamadi", 404)

    seller_map = request.app.state.ctx.get("seller_quality", {})
    data = seller_map.get(slug, [])
    return data

@router.get("/products/{slug}/trend")
async def product_trend(slug: str, request: Request, window: str = "90d"):
    products = request.app.state.ctx.get("products", {})
    if slug not in products:
        raise kanka_error("urun_bulunamadi", 404)

    trend_map = request.app.state.ctx.get("trend", {})
    data = trend_map.get(slug)
    if not data:
        return {"slug": slug, "trend": "sabit", "veri": []}
    return data
