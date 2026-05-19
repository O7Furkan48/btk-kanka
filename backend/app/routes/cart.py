from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.errors import kanka_error
from app.schemas import ComboGroup, CouponRequest, CouponResponse

router = APIRouter()

_KUPONLAR = {
    "KANKA50": {"discount": 50.0, "message": "50 TL indirim uygulandı!"},
    "BTK2026": {"discount": 100.0, "message": "BTK özel 100 TL indirimin uygulandı!"},
}

@router.post("/cart/coupon", response_model=CouponResponse)
async def apply_coupon(body: CouponRequest):
    kupon = _KUPONLAR.get(body.code.upper())
    if not kupon:
        raise kanka_error("kupon_gecersiz")
    return CouponResponse(valid=True, discount=kupon["discount"], message=kupon["message"])

@router.get("/cart/combo-suggestions")
async def combo_suggestions(
    request: Request,
    ids: Annotated[str, Query(description="Virgülle ayrılmış slug listesi")] = "",
):
    if not ids:
        return []

    slugs = [s.strip() for s in ids.split(",") if s.strip()]
    products = request.app.state.ctx.get("products", {})
    risk_map = request.app.state.ctx.get("risk", {})

    retrieval = request.app.state.ctx.get("retrieval")
    if retrieval:
        try:
            from app.ai.retrieval import find_combos
            return await find_combos(retrieval, slugs, products, risk_map)
        except Exception:
            pass

    import random
    result = []
    for slug in slugs[:3]:
        p = products.get(slug)
        if not p:
            continue
        target_cat = p.get("categoryKey", "")
        others = [
            s for s, pp in products.items()
            if s != slug and pp.get("categoryKey") != target_cat
        ]
        rng = random.Random(slug)
        rng.shuffle(others)
        combo_items = []
        for s in others[:2]:
            pp = products[s]
            rd = risk_map.get(s, {})
            combo_items.append({
                "id": s,
                "brand": pp.get("brand", ""),
                "name": pp.get("title", ""),
                "bg": pp.get("bg", "ph-bg-1"),
                "price": pp.get("price", 0),
                "risk": rd.get("level", "low"),
                "riskLabel": f"%{rd.get('percent', 0)}",
            })
        if combo_items:
            result.append({
                "sourceId": slug,
                "sourceName": p.get("title", ""),
                "sourceBg": p.get("bg", "ph-bg-1"),
                "scenario": "Kombin önerisi",
                "items": combo_items,
            })

    return result
