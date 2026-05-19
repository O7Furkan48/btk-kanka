from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.errors import kanka_error

router = APIRouter()

@router.get("/products/{slug}/qa")
async def get_qa(
    slug: str,
    request: Request,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    products = request.app.state.ctx.get("products", {})
    if slug not in products:
        raise kanka_error("urun_bulunamadi", 404)

    try:
        from app import db as _db
        if _db.async_session_factory is not None:
            from sqlalchemy import text
            async with _db.async_session_factory() as session:
                sql = text("""
                    SELECT soru, cevap, satici, soru_tarihi
                    FROM qa
                    WHERE urun_slug = :slug
                    ORDER BY soru_tarihi DESC
                    LIMIT :limit OFFSET :offset
                """)
                rows = (await session.execute(sql, {"slug": slug, "limit": limit, "offset": offset})).mappings().all()
                count = (await session.execute(
                    text("SELECT COUNT(*) FROM qa WHERE urun_slug = :slug"), {"slug": slug}
                )).scalar_one()

            items = []
            for r in rows:
                satici = r.get("satici") or "Satıcı"
                tarih = r.get("soru_tarihi") or ""
                items.append({
                    "question": r["soru"],
                    "answer": r["cevap"],
                    "by": f"{satici} · {tarih}" if tarih else satici,
                })
            return {
                "items": items,
                "total": count,
                "avgResponse": "ortalama 4 saatte yanıtlanıyor",
            }
    except Exception:
        pass

    qa = products[slug].get("qa", [])
    meta = products[slug].get("qaMeta", {})
    return {
        "items": qa[offset:offset + limit],
        "total": meta.get("total", len(qa)),
        "avgResponse": meta.get("avgResponse", ""),
    }
