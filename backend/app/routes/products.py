import random
from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.errors import kanka_error
from app.schemas import (
    Product,
    ProductSummary,
    RiskAnalysis,
    SimilarProduct,
    SizeAdvice,
    SizeAdviceRequest,
)

router = APIRouter()

def _get_products(request: Request) -> dict:
    return request.app.state.ctx.get("products", {})

def _get_risk(request: Request) -> dict:
    return request.app.state.ctx.get("risk", {})

def _get_size_advice(request: Request) -> dict:
    return request.app.state.ctx.get("size_advice", {})

async def _build_review_counts(slug: str) -> dict:
    counts = {"all": 0, "positive": 0, "negative": 0, "matchedToMe": 0}
    try:
        from app import db as _db
        if _db.async_session_factory is None:
            return counts
        from sqlalchemy import text
        async with _db.async_session_factory() as session:
            sql = text("""
                SELECT
                    COUNT(*) AS total,
                    COUNT(*) FILTER (WHERE rl.sent_label = 'positive') AS pos,
                    COUNT(*) FILTER (WHERE rl.sent_label = 'negative') AS neg
                FROM reviews r
                LEFT JOIN reviews_labels rl ON rl.review_id = r.id
                WHERE r.urun_slug = :slug
            """)
            row = (await session.execute(sql, {"slug": slug})).mappings().first()
            if row:
                counts["all"] = int(row["total"] or 0)
                counts["positive"] = int(row["pos"] or 0)
                counts["negative"] = int(row["neg"] or 0)
    except Exception:
        pass
    return counts

async def _build_size_advice(slug: str, sizes: list[dict]) -> dict[int, SizeAdvice]:
    out: dict[int, SizeAdvice] = {}
    by_beden: dict[str, tuple[int, float]] = {}

    try:
        from app import db as _db
        if _db.async_session_factory is not None:
            from sqlalchemy import text
            async with _db.async_session_factory() as session:
                sql = text("""
                    SELECT r.beden,
                           COUNT(*) AS n,
                           COALESCE(AVG(rl.sent_pos), 0.85) AS mem
                    FROM reviews r
                    LEFT JOIN reviews_labels rl ON rl.review_id = r.id
                    WHERE r.urun_slug = :slug
                      AND r.beden IS NOT NULL AND r.beden <> ''
                    GROUP BY r.beden
                """)
                rows = (await session.execute(sql, {"slug": slug})).mappings().all()
                for row in rows:
                    by_beden[row["beden"]] = (int(row["n"]), float(row["mem"]))
    except Exception:
        pass

    for i, sz in enumerate(sizes):
        label = sz.get("label", "")
        info = by_beden.get(label)
        if info and info[0] >= 3:
            n, mem = info
            memnuniyet = max(0, min(100, int(mem * 100)))
            level: str = "low" if memnuniyet >= 70 else ("mid" if memnuniyet >= 50 else "high")
            out[i] = SizeAdvice(
                parts=[
                    {"text": f"{label}", "bold": True},
                    {"text": " bedeni "},
                    {"text": f"{n} kişi", "bold": True},
                    {"text": " almış. "},
                    {"text": f"%{memnuniyet}", "bold": True},
                    {"text": " memnun."},
                ],
                type=level,  # type: ignore[arg-type]
            )
        else:
            out[i] = SizeAdvice(
                parts=[
                    {"text": "Boy-kilonu gir, "},
                    {"text": "sana özel beden öneririm.", "bold": True},
                ],
                type="low",
            )
    return out

def _build_summary(slug: str, p: dict, risk_map: dict) -> ProductSummary:
    risk_data = risk_map.get(slug, {})
    risk_level = risk_data.get("level", "low")
    risk_percent = risk_data.get("percent", 0)

    sent_pos = risk_data.get("satisfaction", 85) / 100
    rating_val = round(2.5 + sent_pos * 2.5, 1)

    return ProductSummary(
        slug=slug,
        brand=p.get("brand", ""),
        name=p.get("title", ""),
        bg=p.get("bg", "ph-bg-1"),
        imageUrl=p.get("imageUrl"),
        placeholder=p.get("placeholder", ""),
        price=f"{p.get('price', 0):,.2f}".replace(",", ".").replace(".0", ",").replace(".", ",", 1),
        risk=risk_level,
        riskLabel=f"%{risk_percent}",
        rating=str(rating_val),
    )

@router.get("/products/recommended", response_model=list[ProductSummary])
async def get_recommended(
    request: Request,
    limit: Annotated[int, Query(ge=1, le=50)] = 12,
    category: str | None = None,
):
    products = _get_products(request)
    risk_map = _get_risk(request)

    slugs = list(products.keys())
    if category:
        slugs = [s for s in slugs if products[s].get("categoryKey") == category]

    rng = random.Random(42)
    rng.shuffle(slugs)
    selected = slugs[:limit]

    return [_build_summary(s, products[s], risk_map) for s in selected]

@router.get("/products/{slug}", response_model=Product)
async def get_product(slug: str, request: Request):
    products = _get_products(request)
    risk_map = _get_risk(request)

    p = products.get(slug)
    if not p:
        raise kanka_error("urun_bulunamadi", 404)

    risk_data = risk_map.get(slug)
    if risk_data:
        risk = RiskAnalysis(**risk_data)
    else:
        risk = RiskAnalysis(
            level="low",
            percent=0,
            levelLabel="Düşük",
            reviewCount=0,
            satisfaction=85,
            bars=[],
        )

    sizes = p.get("sizes", [])
    advice_by_size: dict[int, SizeAdvice] = await _build_size_advice(slug, sizes)

    review_counts = await _build_review_counts(slug)

    return Product(
        slug=slug,
        brand=p.get("brand", ""),
        title=p.get("title", ""),
        category=p.get("category", []),
        rating=p.get("rating", 4.0),
        reviewCount=p.get("reviewCount", 0),
        salesCount=p.get("salesCount", "0"),
        price=p.get("price", 0),
        oldPrice=p.get("oldPrice", 0),
        discountPercent=p.get("discountPercent", 0),
        risk=risk,
        colors=p.get("colors", []),
        defaultColorIndex=p.get("defaultColorIndex", 0),
        sizes=p.get("sizes", []),
        defaultSizeIndex=p.get("defaultSizeIndex", 0),
        adviceBySize=advice_by_size,
        gallery=p.get("gallery", []),
        summary=p.get("summary", ""),
        audience=p.get("audience", []),
        occasions=p.get("occasions", []),
        description=p.get("description", []),
        care=p.get("care", []),
        specs=p.get("specs", []),
        reviews=p.get("reviews", []),
        reviewCounts=review_counts,
        qa=p.get("qa", []),
        qaMeta=p.get("qaMeta", {"total": 0, "avgResponse": ""}),
        similar=p.get("similar", []),
    )

@router.post("/products/{slug}/size-advice", response_model=SizeAdvice)
async def post_size_advice(slug: str, body: SizeAdviceRequest, request: Request):
    products = _get_products(request)
    if slug not in products:
        raise kanka_error("urun_bulunamadi", 404)

    size_advice_map = _get_size_advice(request)
    slug_advice = size_advice_map.get(slug, {})

    boy_bin = (body.height // 5) * 5
    kilo_bin = (body.weight // 10) * 10
    lookup_key = f"{boy_bin}_{kilo_bin}"
    exact = slug_advice.get(lookup_key)

    MIN_SAMPLE = 5

    if exact and exact.get("_meta", {}).get("sample", 0) >= MIN_SAMPLE:
        return SizeAdvice(**{k: v for k, v in exact.items() if k != "_meta"})

    from collections import Counter
    neighbors = []
    for db in (-5, 0, 5):
        for dk in (-10, 0, 10):
            nb_key = f"{boy_bin + db}_{kilo_bin + dk}"
            nb = slug_advice.get(nb_key)
            if nb and nb.get("_meta"):
                neighbors.append((db, dk, nb["_meta"]))

    if neighbors:
        total_n = sum(n[2].get("sample", 0) for n in neighbors)
        if total_n >= 3:
            weighted_mem = sum(n[2].get("memnuniyet", 50) * n[2].get("sample", 0) for n in neighbors) / max(total_n, 1)
            bedens_counter: Counter = Counter()
            for _, _, m in neighbors:
                bedens_counter[m.get("beden", "?")] += m.get("sample", 0)
            top_beden, top_n = bedens_counter.most_common(1)[0]
            beden_dagilim = [{"beden": b, "n": n} for b, n in bedens_counter.most_common(5)]
            memnuniyet = int(round(weighted_mem))
            level = "low" if memnuniyet >= 70 else ("mid" if memnuniyet >= 50 else "high")

            is_fallback = exact is None or exact.get("_meta", {}).get("sample", 0) < MIN_SAMPLE
            prefix = "Yakın profillerden " if is_fallback else f"{boy_bin}cm {kilo_bin}kg "
            parts = [
                {"text": prefix},
                {"text": f"{total_n} kişi", "bold": True},
                {"text": " bu üründen "},
                {"text": top_beden, "bold": True},
                {"text": " almış. "},
                {"text": f"%{memnuniyet}", "bold": True},
                {"text": " memnun." + (" (komşu beden/kilo verisi)" if is_fallback else "")},
            ]
            return SizeAdvice(
                parts=parts,
                type=level,  # type: ignore[arg-type]
            )

    if slug_advice:
        all_buckets = [v["_meta"] for v in slug_advice.values() if v.get("_meta")]
        if all_buckets:
            total = sum(b.get("sample", 0) for b in all_buckets)
            if total >= 3:
                bedens_c: Counter = Counter()
                for b in all_buckets:
                    bedens_c[b.get("beden", "?")] += b.get("sample", 0)
                top_beden, _ = bedens_c.most_common(1)[0]
                mem = int(sum(b.get("memnuniyet", 50) * b.get("sample", 0) for b in all_buckets) / total)
                return SizeAdvice(
                    parts=[
                        {"text": "Genel kullanıcı verisinden "},
                        {"text": f"{total} kişi", "bold": True},
                        {"text": " en çok "},
                        {"text": top_beden, "bold": True},
                        {"text": " almış. "},
                        {"text": f"%{mem}", "bold": True},
                        {"text": " memnun. (profiline tam uyan veri henüz az)"},
                    ],
                    type="mid",
                )

    return SizeAdvice(
        parts=[
            {"text": "Bu profil için yeterli yorum yok. "},
            {"text": "Genel beden tablosu", "bold": True},
            {"text": " ya da AI'ya \"hangi beden uyar\" diye sor."},
        ],
        type="low",
    )

@router.get("/products/{slug}/risk-analysis", response_model=RiskAnalysis)
async def get_risk_analysis(slug: str, request: Request):
    products = _get_products(request)
    if slug not in products:
        raise kanka_error("urun_bulunamadi", 404)

    risk_map = _get_risk(request)
    risk_data = risk_map.get(slug)
    if not risk_data:
        return RiskAnalysis(
            level="low", percent=0, levelLabel="Düşük",
            reviewCount=0, satisfaction=85, bars=[],
        )
    return RiskAnalysis(**risk_data)

@router.get("/products/{slug}/similar", response_model=list[SimilarProduct])
async def get_similar(
    slug: str,
    request: Request,
    limit: Annotated[int, Query(ge=1, le=10)] = 4,
):
    products = _get_products(request)
    if slug not in products:
        raise kanka_error("urun_bulunamadi", 404)

    retrieval = request.app.state.ctx.get("retrieval")
    if retrieval:
        try:
            from app.ai.retrieval import find_similar
            return await find_similar(retrieval, slug, limit)
        except Exception:
            pass

    risk_map = _get_risk(request)
    target_cat = products[slug].get("categoryKey")
    candidates = [
        s for s, p in products.items()
        if s != slug and p.get("categoryKey") == target_cat
    ]
    rng = random.Random(slug)
    rng.shuffle(candidates)
    result = []
    for s in candidates[:limit]:
        p = products[s]
        risk_data = risk_map.get(s, {})
        sent_pos = risk_data.get("satisfaction", 85) / 100
        rating_val = round(2.5 + sent_pos * 2.5, 1)
        result.append(SimilarProduct(
            brand=p.get("brand", ""),
            name=p.get("title", ""),
            price=f"{p.get('price', 0):.2f}".replace(".", ","),
            rating=str(rating_val),
            bg=p.get("bg", "ph-bg-1"),
            imageUrl=p.get("imageUrl"),
            href=f"/urun/{s}",
        ))
    return result
