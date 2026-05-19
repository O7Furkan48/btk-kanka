from fastapi import APIRouter, Request

from app.errors import kanka_error
from app.schemas import CompareRequest

router = APIRouter()

@router.post("/products/compare")
async def compare_products(body: CompareRequest, request: Request):
    products = request.app.state.ctx.get("products", {})
    risk_map = request.app.state.ctx.get("risk", {})

    for slug in (body.slug_a, body.slug_b):
        if slug not in products:
            raise kanka_error("urun_bulunamadi", 404)

    def _summary(slug: str) -> dict:
        p = products[slug]
        r = risk_map.get(slug, {})
        return {
            "slug": slug,
            "brand": p.get("brand", ""),
            "title": p.get("title", ""),
            "price": p.get("price", 0),
            "risk_level": r.get("level", "low"),
            "risk_percent": r.get("percent", 0),
            "satisfaction": r.get("satisfaction", 85),
            "bars": r.get("bars", []),
            "sizes": p.get("sizes", []),
            "summary": p.get("summary", ""),
        }

    return {
        "a": _summary(body.slug_a),
        "b": _summary(body.slug_b),
    }
