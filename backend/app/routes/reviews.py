from typing import Annotated, Literal

from fastapi import APIRouter, Query, Request

from app.errors import kanka_error

router = APIRouter()

@router.get("/products/{slug}/reviews")
async def get_reviews(
    slug: str,
    request: Request,
    filter: Annotated[Literal["all", "pos", "neg", "me"], Query()] = "all",
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    height: int | None = None,
    weight: int | None = None,
):
    products = request.app.state.ctx.get("products", {})
    if slug not in products:
        raise kanka_error("urun_bulunamadi", 404)

    try:
        from app import db as _db
        if _db.async_session_factory is not None:
            return await _db_reviews(slug, filter, limit, offset, height, weight)
    except Exception as e:
        import logging
        logging.getLogger("kanka").warning(f"/reviews DB fail: {e}")

    reviews = products[slug].get("reviews", [])
    if filter == "pos":
        reviews = [r for r in reviews if r.get("rating", 3) >= 4]
    elif filter == "neg":
        reviews = [r for r in reviews if r.get("rating", 3) <= 2]

    return {
        "items": reviews[offset:offset + limit],
        "total": len(reviews),
    }

async def _db_reviews(
    slug: str,
    filter: str,
    limit: int,
    offset: int,
    height: int | None,
    weight: int | None,
) -> dict:
    from sqlalchemy import text
    from app import db as _db

    async with _db.async_session_factory() as session:
        conditions = ["r.urun_slug = :slug"]
        params: dict = {"slug": slug, "limit": limit, "offset": offset}

        if filter == "pos":
            conditions.append("rl.sent_label = 'positive'")
        elif filter == "neg":
            conditions.append("rl.sent_label = 'negative'")
        elif filter == "me" and height and weight:
            boy_bin = (height // 5) * 5
            kilo_bin = (weight // 10) * 10
            conditions.append("r.boy_bin = :boy_bin AND r.kilo_bin = :kilo_bin")
            params["boy_bin"] = boy_bin
            params["kilo_bin"] = kilo_bin

        where = " AND ".join(conditions)
        sql = text(f"""
            SELECT r.id, r.kullanici, r.yorum_metni, r.beden, r.boy, r.kilo,
                   r.tarih, r.satici, rl.sent_label, rl.fit_label, rl.risk_top
            FROM reviews r
            LEFT JOIN reviews_labels rl ON rl.review_id = r.id
            WHERE {where}
            ORDER BY r.tarih DESC
            LIMIT :limit OFFSET :offset
        """)
        rows = (await session.execute(sql, params)).mappings().all()

        count_sql = text(f"SELECT COUNT(*) FROM reviews r LEFT JOIN reviews_labels rl ON rl.review_id = r.id WHERE {where}")
        count_params = {k: v for k, v in params.items() if k not in ("limit", "offset")}
        total = (await session.execute(count_sql, count_params)).scalar_one()

    SENT_TO_RATING = {"positive": 5, "neutral": 3, "negative": 2}
    TOPIC_LABELS = {
        "kumas": "Kumaş", "renk": "Renk", "kalite": "Kalite",
        "kargo": "Kargo", "koku": "Koku", "gorsel": "Görsel",
    }

    items = []
    for r in rows:
        kullanici = r.get("kullanici") or "Anonim"

        parts = [p.strip("* ").strip() for p in kullanici.split() if p.strip("* ").strip()]
        initials = "".join(p[0].upper() for p in parts if p)[:2] or "?"

        hw = ""
        if r.get("boy") is not None and r.get("kilo") is not None:
            hw = f"{int(r['boy'])}cm {int(r['kilo'])}kg"
        elif r.get("boy") is not None:
            hw = f"{int(r['boy'])}cm"
        elif r.get("kilo") is not None:
            hw = f"{int(r['kilo'])}kg"

        sent = r.get("sent_label") or "neutral"
        fit = r.get("fit_label") or None
        risk_top = r.get("risk_top") or None
        topics = []
        if risk_top and risk_top in TOPIC_LABELS:
            topics.append({"label": TOPIC_LABELS[risk_top], "sentiment": "neg"})
        if sent == "positive" and not topics:
            topics.append({"label": "Genel memnuniyet", "sentiment": "pos"})

        items.append({
            "name": kullanici,
            "initials": initials,
            "heightWeight": hw,
            "size": r.get("beden") or "",
            "rating": SENT_TO_RATING.get(sent, 3),
            "date": r.get("tarih") or "",
            "text": r["yorum_metni"],
            "topics": topics,
            "helpful": 0,

            "classification": {
                "sent": sent,
                "fit": fit if fit and fit != "belirsiz" else None,
                "risk": risk_top if risk_top else None,
            },
        })
    return {"items": items, "total": total}

@router.get("/products/{slug}/reviews/aspect")
async def get_aspect_summary(
    slug: str,
    request: Request,
    aspect: Annotated[str, Query(min_length=2)] = "kumaş",
):
    products = request.app.state.ctx.get("products", {})
    if slug not in products:
        raise kanka_error("urun_bulunamadi", 404)

    retrieval = request.app.state.ctx.get("retrieval")
    if retrieval:
        try:
            from app.ai.retrieval import aspect_summary
            return await aspect_summary(retrieval, slug, aspect)
        except Exception:
            pass

    return {"aspect": aspect, "ozet": "Bu özellik henüz analiz edilmedi."}
