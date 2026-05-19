import logging
from pathlib import Path

logger = logging.getLogger("kanka.retrieval")

class RetrievalContext:
    def __init__(self, encoder, chroma_client, collections: dict):
        self.encoder = encoder
        self.client = chroma_client
        self.reviews = collections.get("reviews_collection")
        self.products = collections.get("products_collection")
        self.qa = collections.get("qa_collection")

async def load_retrieval(chroma_dir: str) -> RetrievalContext | None:
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        from app.config import settings

        encoder = SentenceTransformer("BAAI/bge-m3")

        http_url = (settings.chroma_http_url or "").strip()
        if http_url:

            from urllib.parse import urlparse
            u = urlparse(http_url)
            host = u.hostname or "localhost"
            port = u.port or 8000
            ssl = u.scheme == "https"
            client = chromadb.HttpClient(host=host, port=port, ssl=ssl)
            logger.info(f"ChromaDB HTTP modu: {http_url}")
        else:
            Path(chroma_dir).mkdir(parents=True, exist_ok=True)
            client = chromadb.PersistentClient(path=chroma_dir)
            logger.info(f"ChromaDB embedded modu: {chroma_dir}")

        collections = {}
        for name in ("reviews_collection", "products_collection", "qa_collection"):
            try:
                collections[name] = client.get_collection(name)
            except Exception:
                collections[name] = client.get_or_create_collection(name)

        logger.info("ChromaDB hazır — koleksiyonlar yüklendi")
        return RetrievalContext(encoder, client, collections)
    except Exception as e:
        logger.warning(f"Retrieval yüklenemedi: {e}")
        return None

async def search_reviews(
    ctx: RetrievalContext,
    query: str,
    slug: str,
    top_k: int = 5,
    filter_sent: str | None = None,
    filter_fit: str | None = None,
) -> list[dict]:
    if not ctx.reviews:
        return []

    embedding = ctx.encoder.encode([query])[0].tolist()
    where: dict = {"urun_slug": {"$eq": slug}}
    if filter_sent:
        where["sent_label"] = {"$eq": filter_sent}
    if filter_fit:
        where["fit_label"] = {"$eq": filter_fit}

    results = ctx.reviews.query(
        query_embeddings=[embedding],
        n_results=min(top_k, 10),
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    items = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        items.append({"text": doc, "meta": meta, "score": 1 - results["distances"][0][i]})
    return items

async def find_similar(ctx: RetrievalContext, slug: str, limit: int = 4) -> list[dict]:
    if not ctx.products:
        return []

    results = ctx.products.get(ids=[slug], include=["embeddings", "metadatas"])
    if not results["embeddings"]:
        return []

    emb = results["embeddings"][0]
    src_meta = (results["metadatas"] or [{}])[0]
    src_cat = src_meta.get("kategori_key")
    src_kat_son = src_meta.get("kategori_son")
    src_cinsiyet = src_meta.get("cinsiyet")

    def _hits(metas, exclude_slug):
        return [m for m in (metas or []) if m and m.get("slug") != exclude_slug]

    similar = None
    attempts = []
    if src_kat_son and src_cinsiyet:
        attempts.append({"$and": [{"kategori_son": {"$eq": src_kat_son}}, {"cinsiyet": {"$eq": src_cinsiyet}}]})
    if src_cat and src_cinsiyet:
        attempts.append({"$and": [{"kategori_key": {"$eq": src_cat}}, {"cinsiyet": {"$eq": src_cinsiyet}}]})
    if src_cat:
        attempts.append({"kategori_key": {"$eq": src_cat}})
    attempts.append(None)

    for where in attempts:
        try:
            kwargs = {"query_embeddings": [emb], "n_results": limit + 2,
                      "include": ["documents", "metadatas"]}
            if where is not None:
                kwargs["where"] = where
            r = ctx.products.query(**kwargs)
            if r["metadatas"] and len(_hits(r["metadatas"][0], slug)) >= limit:
                similar = r
                break
            similar = r
        except Exception:
            continue

    if similar is None:
        return []

    out = []
    for i, meta in enumerate(similar["metadatas"][0]):
        if meta.get("slug") == slug:
            continue
        out.append({
            "brand": meta.get("marka", ""),
            "name": similar["documents"][0][i],
            "price": str(meta.get("fiyat", "")),
            "rating": str(meta.get("rating", "4.0")),
            "bg": meta.get("bg", "ph-bg-1"),
            "imageUrl": meta.get("imageUrl"),
            "href": f"/urun/{meta.get('slug', '')}",
        })
        if len(out) >= limit:
            break
    return out

async def find_combos(
    ctx: RetrievalContext,
    slugs: list[str],
    products: dict,
    risk_map: dict,
) -> list[dict]:
    result = []
    for slug in slugs[:3]:
        items = await find_similar(ctx, slug, limit=2)
        p = products.get(slug, {})
        result.append({
            "sourceId": slug,
            "sourceName": p.get("title", ""),
            "sourceBg": p.get("bg", "ph-bg-1"),
            "scenario": "Stil uyumu",
            "items": items,
        })
    return result

async def aspect_summary(ctx: RetrievalContext, slug: str, aspect: str) -> dict:
    reviews = await search_reviews(ctx, aspect, slug, top_k=8)
    ozet = " ".join(r["text"][:100] for r in reviews[:3]) if reviews else "Yeterli veri yok."
    return {"aspect": aspect, "ozet": ozet, "kaynak_sayisi": len(reviews)}
