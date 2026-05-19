import asyncio
import json
import logging
import time
from collections import deque
from typing import AsyncGenerator

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError

from app.ai.tools import COMBO_SYSTEM_PROMPT, SYSTEM_PROMPT, TOOLS
from app.config import settings

logger = logging.getLogger("kanka.gemini")

_tool_log: deque = deque(maxlen=100)

MODEL_CHAIN = [
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3-flash-preview",
    "gemini-2.0-flash-lite",
    "gemini-2.5-flash",
]

_PRIMARY_MODEL: str = MODEL_CHAIN[0]

_MODEL_COOLDOWN_UNTIL: dict[str, float] = {}

def _set_primary(model: str) -> None:
    global _PRIMARY_MODEL
    _PRIMARY_MODEL = model

def _pick_model() -> str:
    now = time.time()
    for m in MODEL_CHAIN:
        if _MODEL_COOLDOWN_UNTIL.get(m, 0) <= now:
            return m

    return min(MODEL_CHAIN, key=lambda m: _MODEL_COOLDOWN_UNTIL.get(m, 0))

def _mark_quota_hit(model: str, cooldown_sec: int = 90) -> None:
    _MODEL_COOLDOWN_UNTIL[model] = time.time() + cooldown_sec
    logger.warning(f"[gemini] {model} kotası doldu, {cooldown_sec}s cooldown")

async def _generate_with_fallback(
    client: genai.Client,
    contents: list,
    config: "types.GenerateContentConfig",
) -> tuple[str, object]:
    last_err: Exception | None = None
    tried: list[str] = []

    primary = _pick_model()

    ordered = [primary] + [m for m in MODEL_CHAIN if m != primary]
    for model in ordered:
        if _MODEL_COOLDOWN_UNTIL.get(model, 0) > time.time():
            continue
        tried.append(model)
        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model=model,
                contents=contents,
                config=config,
            )
            _set_primary(model)
            return model, response
        except (ClientError, ServerError) as err:
            msg = str(err).lower()
            code = getattr(err, "code", None)
            if code == 429 or "resource_exhausted" in msg or "quota" in msg:

                import re as _re
                m = _re.search(r"retry in\s*([\d.]+)", msg)
                cd = 90
                try:
                    if m:
                        cd = max(30, int(float(m.group(1))) + 5)
                except Exception:
                    pass
                _mark_quota_hit(model, cd)
                last_err = err
                continue

            logger.warning(f"[gemini] {model} hata: {err}")
            _mark_quota_hit(model, 15)
            last_err = err
            continue
        except Exception as err:
            last_err = err
            logger.exception(f"[gemini] {model} beklenmeyen hata")
            _mark_quota_hit(model, 15)
            continue
    if last_err:
        raise last_err
    raise RuntimeError("Hiç model denenemedi")

def _build_declarations() -> list[types.FunctionDeclaration]:
    decls = []
    for t in TOOLS:
        decls.append(
            types.FunctionDeclaration(
                name=t["name"],
                description=t["description"],
                parameters=t.get("parameters", {}),
            )
        )
    return decls

async def _dispatch_tool(
    tool_name: str,
    tool_args: dict,
    slug: str,
    ctx: dict,
) -> dict:
    products = ctx.get("products", {})
    retrieval = ctx.get("retrieval")
    risk_map = ctx.get("risk", {})
    size_advice_map = ctx.get("size_advice", {})
    seller_map = ctx.get("seller_quality", {})
    trend_map = ctx.get("trend", {})

    if tool_name == "get_qa_answer_if_exists":

        if retrieval and retrieval.qa:
            query = tool_args.get("query", "")
            emb = retrieval.encoder.encode([query])[0].tolist()
            res = retrieval.qa.query(
                query_embeddings=[emb],
                n_results=1,
                where={"urun_slug": {"$eq": slug}},
                include=["documents", "distances"],
            )
            if res["distances"][0] and res["distances"][0][0] < 0.35:
                return {"found": True, "answer": res["documents"][0][0]}
        return {"found": False}

    elif tool_name == "search_reviews":
        if retrieval:
            from app.ai.retrieval import search_reviews
            results = await search_reviews(
                retrieval,
                tool_args.get("query", ""),
                tool_args.get("product_id", slug),
                top_k=tool_args.get("top_k", 5),
            )
            return {"reviews": results}
        return {"reviews": []}

    elif tool_name == "get_size_recommendation":
        height = tool_args.get("height", 0)
        weight = tool_args.get("weight", 0)
        boy_bin = (height // 5) * 5
        kilo_bin = (weight // 10) * 10
        key = f"{boy_bin}_{kilo_bin}"
        slug_advice = size_advice_map.get(slug, {})
        if key in slug_advice:
            return slug_advice[key]
        return {"parts": [{"text": "Bu profil için henüz yeterli veri yok."}], "type": "low"}

    elif tool_name == "get_return_risk":
        return risk_map.get(slug, {"level": "low", "percent": 0})

    elif tool_name == "find_compatible_products":
        if retrieval:
            from app.ai.retrieval import find_combos
            result = await find_combos(retrieval, [slug], products, risk_map)
            return {"items": result[0]["items"] if result else []}
        return {"items": []}

    elif tool_name == "get_alternative_product":
        constraint = tool_args.get("user_constraint", "")
        if retrieval:
            from app.ai.retrieval import search_reviews as sr
            results = await sr(retrieval, constraint, slug, top_k=3)
            return {"reviews": results, "constraint": constraint}
        return {"message": "Alternatif bulunamadı."}

    elif tool_name == "get_seller_quality":
        return {"sellers": seller_map.get(slug, [])}

    elif tool_name == "get_review_summary":
        if retrieval:
            from app.ai.retrieval import aspect_summary
            return await aspect_summary(retrieval, slug, tool_args.get("aspect", "genel"))
        return {"aspect": tool_args.get("aspect", ""), "ozet": "Veri yok."}

    elif tool_name == "get_size_distribution":
        slug_advice = size_advice_map.get(slug, {})
        return {"distribution": slug_advice}

    elif tool_name == "compare_products":
        def _s(s: str) -> dict:
            p = products.get(s, {})
            r = risk_map.get(s, {})
            return {"slug": s, "title": p.get("title", ""), "risk": r}
        return {"a": _s(tool_args.get("slug_a", "")), "b": _s(tool_args.get("slug_b", ""))}

    elif tool_name == "get_trending_for_category":
        cat = tool_args.get("category", "")
        trend_items = [
            {"slug": s, **v}
            for s, v in trend_map.items()
            if products.get(s, {}).get("categoryKey") == cat
        ]
        return {"items": sorted(trend_items, key=lambda x: x.get("son_90_gun", 0), reverse=True)[:5]}

    elif tool_name == "search_products_by_intent":

        if not retrieval or not retrieval.products:
            return {"products": []}
        query = tool_args.get("query", "")
        slot = tool_args.get("slot", "")
        cinsiyet = tool_args.get("cinsiyet")

        exclude_slug = tool_args.get("exclude_slug") or slug

        already_suggested = tool_args.get("_exclude_extra") or []
        top_k = int(tool_args.get("top_k", 3))

        if not query.strip():
            return {"products": []}

        emb = retrieval.encoder.encode([query])[0].tolist()

        where_filter = None
        if cinsiyet in ("erkek", "kadin", "unisex"):
            where_filter = {"cinsiyet": {"$eq": cinsiyet}}

        try:
            res = retrieval.products.query(
                query_embeddings=[emb],
                n_results=top_k + 3,
                where=where_filter,
                include=["documents", "metadatas"],
            )
        except Exception:
            return {"products": []}

        SLOT_PATTERNS = {
            "ust": ["tişört", "gömlek", "kazak", "sweatshirt", "bluz", "triko", "kaşkorse"],
            "alt": ["pantolon", "şort", "etek", "tayt", "jean", "eşofman", "jogger"],
            "ayakkabi": ["ayakkabı", "sneaker", "bot", "terlik", "çizme", "topuk"],
            "aksesuar": ["çanta", "cüzdan", "kemer", "saat", "kolye", "küpe", "yüzük", "bileklik"],
            "dis_giyim": ["mont", "ceket", "kaban", "pardösü", "trençkot", "hırka"],
            "elbise": ["elbise"],
        }
        patterns = SLOT_PATTERNS.get(slot, [])

        items = []

        for tier in (1, 2):
            for i, meta in enumerate(res["metadatas"][0]):
                m_slug = meta.get("slug")
                if not m_slug or m_slug == exclude_slug:
                    continue
                if m_slug in already_suggested:
                    continue
                cat_son = (meta.get("kategori_son") or "").lower()
                title_doc = (res["documents"][0][i] or "").lower()
                if tier == 1 and patterns:
                    if not any(p in cat_son or p in title_doc for p in patterns):
                        continue

                if any(it["slug"] == m_slug for it in items):
                    continue
                items.append({
                    "slug": meta.get("slug"),
                    "brand": meta.get("marka"),
                    "name": (res["documents"][0][i] or "")[:150],
                    "fiyat": float(meta.get("fiyat") or 0),
                    "rating": float(meta.get("rating") or 0),
                    "imageUrl": meta.get("imageUrl") or "",
                    "kategori_son": meta.get("kategori_son"),
                    "cinsiyet": meta.get("cinsiyet"),
                    "href": f"/urun/{meta.get('slug')}",
                })
                if len(items) >= top_k:
                    break
            if len(items) >= top_k:
                break
        return {"products": items, "slot": slot, "cinsiyet": cinsiyet}

    return {"error": f"Bilinmeyen araç: {tool_name}"}

async def stream_chat(
    client: genai.Client,
    slug: str,
    message: str,
    history: list[dict],
    ctx: dict,
) -> AsyncGenerator[tuple[str, dict], None]:

    products = ctx.get("products", {})
    risk_map = ctx.get("risk", {})
    p = products.get(slug, {})
    risk_info = risk_map.get(slug, {})
    desc_short = " ".join(p.get("description", []))[:400]
    audience = ", ".join(p.get("audience", []) or [])
    occasions = ", ".join(p.get("occasions", []) or [])
    care_text = " · ".join(c.get("text", "") for c in p.get("care", []) if isinstance(c, dict))
    specs_str = ", ".join(f"{k}: {v}" for k, v in (p.get("specs", []) or [])[:10])

    urun_context = (
        f"\n\n═══ KULLANICININ AKTİF OLARAK BAKTIĞI ÜRÜN ═══\n"
        f"- Slug: {slug} (tool çağırırken product_id={slug})\n"
        f"- Marka: {p.get('brand', '')}\n"
        f"- Başlık: {p.get('title', '')}\n"
        f"- Kategori: {' › '.join(c.get('label','') for c in p.get('category', [])[:4])}\n"
        f"- Fiyat: {p.get('price', 0):.0f} TL  (eski {p.get('oldPrice', 0):.0f}, %{p.get('discountPercent', 0)} indirim)\n"
        f"- Puan: {p.get('rating', 0)}/5  ({p.get('reviewCount', 0)} yorum, {p.get('salesCount', '?')} oy)\n"
        f"- Kalıp/Kumaş özellikleri: {specs_str}\n"
        f"- AI özet: {p.get('summary', '') or '(yok)'}\n"
        f"- Açıklama: {desc_short or '(yok)'}\n"
        f"- Hedef kitle: {audience or '(genel)'}\n"
        f"- Hangi ortam: {occasions or '(genel)'}\n"
        f"- Bakım: {care_text or '(belirtilmemiş)'}\n"
        f"- Beden seçenekleri: {[s.get('label') for s in p.get('sizes', [])]}\n"
        f"- Renk seçenekleri: {[c.get('name') for c in p.get('colors', [])]}\n"
        f"- İade riski: %{risk_info.get('percent', '?')} ({risk_info.get('levelLabel', '?')}) · "
        f"genel memnuniyet %{risk_info.get('satisfaction', '?')}\n"
        f"- Risk barları: {[(b['label'], b['value']) for b in risk_info.get('bars', [])]}\n"
        "\nBu bilgiler senin ELİNDE. Kullanıcı 'bu ürün nedir' diye sorarsa, bu bilgilerle DOĞRUDAN cevap ver — "
        "tool çağrısına gerek yok. Yorum/risk/beden detayı isterse tool çağır."
    )

    import re as _re
    sticky_bits: list[str] = []
    for h in history:
        c = (h.get("content") or "").lower()
        m_boy = _re.search(r"\b(1[4-9][0-9]|2[0-1][0-9])\s*(cm|santim)?\b", c)
        m_kilo = _re.search(r"\b([3-9][0-9]|1[0-9][0-9])\s*(kg|kilo)\b", c)
        m_combined = _re.search(r"\b(1[4-9][0-9]|2[0-1][0-9])\s*[,\s/]+\s*([3-9][0-9]|1[0-9][0-9])\b", c)
        if m_combined:
            sticky_bits.append(f"kullanıcı boyu={m_combined.group(1)}cm, kilosu={m_combined.group(2)}kg")
        elif m_boy and m_kilo:
            sticky_bits.append(f"kullanıcı boyu={m_boy.group(1)}cm, kilosu={m_kilo.group(1)}kg")

        m_beden = _re.search(r"\b(XS|S|M|L|XL|XXL|3XL|4XL|3[2-9]|4[0-8]|5[0-8])\b", h.get("content", "").upper())
        if m_beden:
            sticky_bits.append(f"konuşmada bahsedilen beden={m_beden.group(1)}")
    sticky_context = ""
    if sticky_bits:

        unique = list(dict.fromkeys(sticky_bits))
        sticky_context = "\n\nÖNCEKİ KONUŞMADAN HATIRLA:\n- " + "\n- ".join(unique[-3:])
    urun_context = urun_context + sticky_context

    def _norm_role(r: str) -> str:
        if r in ("assistant", "bot", "ai"):
            return "model"
        if r in ("system",):
            return "user"
        return r if r in ("user", "model") else "user"

    contents = []
    for h in history:
        content = h.get("content") or ""
        if not content.strip():
            continue
        contents.append(types.Content(
            role=_norm_role(h.get("role", "user")),
            parts=[types.Part(text=content)],
        ))
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    tool_config = types.Tool(function_declarations=_build_declarations())
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT + urun_context,
        tools=[tool_config],
        temperature=0.7,
        max_output_tokens=1024,
    )

    while True:
        used_model, response = await _generate_with_fallback(client, contents, config)
        if not response.candidates:
            yield "token", {"text": "Cevap üretemedim, başka şekilde sorar mısın?"}
            yield "done", {}
            return
        candidate = response.candidates[0]

        parts = (candidate.content.parts if candidate.content else None) or []

        tool_calls = [p for p in parts if getattr(p, "function_call", None)]
        if tool_calls:

            tool_results = []
            for part in parts:
                if not getattr(part, "function_call", None):
                    continue
                fn = part.function_call
                args = dict(fn.args) if fn.args else {}

                event_payload = {"name": fn.name, "args": args}
                _tool_log.append({"type": "tool_call", **event_payload})
                yield "tool_call", event_payload

                result = await _dispatch_tool(fn.name, args, slug, ctx)
                result_payload = {"name": fn.name, "payload": result}
                _tool_log.append({"type": "tool_result", **result_payload})
                yield "tool_result", result_payload

                tool_results.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fn.name,
                            response={"result": result},
                        )
                    )
                )

            contents.append(candidate.content)
            contents.append(types.Content(role="tool", parts=tool_results))
            continue

        full_text = "".join((getattr(p, "text", None) or "") for p in parts)
        if not full_text.strip():
            full_text = "Bunu sormak için elimde yeterli bilgi yok, başka şekilde sorar mısın?"
        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield "token", {"text": chunk}
            await asyncio.sleep(0.01)

        yield "done", {}
        break

async def stream_combo_chat(
    client: genai.Client,
    slug: str,
    ctx: dict,
    extra_user_hint: str = "",
) -> AsyncGenerator[tuple[str, dict], None]:
    products = ctx.get("products", {})
    risk_map = ctx.get("risk", {})
    p = products.get(slug, {})
    risk_info = risk_map.get(slug, {})

    desc_short = " ".join(p.get("description", []))[:400]
    audience = ", ".join(p.get("audience", []) or [])
    occasions = ", ".join(p.get("occasions", []) or [])
    specs_str = ", ".join(f"{k}: {v}" for k, v in (p.get("specs", []) or [])[:10])
    breadcrumb_str = " › ".join(c.get("label", "") for c in p.get("category", [])[:4])

    urun_context = (
        f"\n\n═══ KULLANICININ AKTİF OLARAK BAKTIĞI ANA ÜRÜN ═══\n"
        f"- Slug: {slug}  (search_products_by_intent çağırırken exclude_slug={slug})\n"
        f"- Marka: {p.get('brand', '')}\n"
        f"- Başlık: {p.get('title', '')}\n"
        f"- Kategori (breadcrumb): {breadcrumb_str}\n"
        f"- Fiyat: {p.get('price', 0):.0f} TL\n"
        f"- Kalıp & Kumaş özellikleri: {specs_str}\n"
        f"- AI özet: {p.get('summary', '') or '(yok)'}\n"
        f"- Açıklama: {desc_short or '(yok)'}\n"
        f"- Hedef kitle: {audience or '(genel)'}\n"
        f"- Ortam: {occasions or '(genel)'}\n"
        f"- Beden seçenekleri: {[s.get('label') for s in p.get('sizes', [])][:8]}\n"
        f"- Renk seçenekleri: {[c.get('name') for c in p.get('colors', [])]}\n"
        f"- İade riski: %{risk_info.get('percent', '?')} ({risk_info.get('levelLabel', '?')})\n"
    )

    initial_user = (
        "Bu ürünle uyumlu 3-4 parçalık BİR KOMBİN öner. Önce ana ürünün cinsiyetini, "
        "stilini, mevsimini ve hangi parça olduğunu kararla. Sonra boş slot'lar için "
        "search_products_by_intent tool'unu sırayla çağır. Cinsiyet AYNI olsun. "
        "Tool çağrıları bitince final kombini güzel format ile sun."
    )
    if extra_user_hint and extra_user_hint.strip():
        initial_user += f"\n\nKullanıcı ek olarak şunu belirtti: {extra_user_hint.strip()}"

    contents = [types.Content(role="user", parts=[types.Part(text=initial_user)])]
    tool_config = types.Tool(function_declarations=_build_declarations())
    config = types.GenerateContentConfig(
        system_instruction=COMBO_SYSTEM_PROMPT + urun_context,
        tools=[tool_config],
        temperature=0.7,
        max_output_tokens=2048,
    )

    suggested_slugs: list[str] = [slug]
    MAX_TURNS = 6
    for turn_no in range(MAX_TURNS):
        used_model, response = await _generate_with_fallback(client, contents, config)
        if not response.candidates:
            yield "token", {"text": "Kombin önerisi oluşturamadım, başka şekilde sorar mısın?"}
            yield "done", {}
            return
        candidate = response.candidates[0]
        parts = (candidate.content.parts if candidate.content else None) or []

        tool_calls = [p for p in parts if getattr(p, "function_call", None)]
        if tool_calls and turn_no < MAX_TURNS - 1:
            tool_results = []
            for part in parts:
                if not getattr(part, "function_call", None):
                    continue
                fn = part.function_call
                args = dict(fn.args) if fn.args else {}

                if fn.name == "search_products_by_intent":
                    args["exclude_slug"] = slug
                    args["_exclude_extra"] = list(suggested_slugs)

                event_payload = {"name": fn.name, "args": args}
                _tool_log.append({"type": "tool_call", **event_payload})
                yield "tool_call", event_payload

                result = await _dispatch_tool(fn.name, args, slug, ctx)

                if fn.name == "search_products_by_intent" and isinstance(result, dict):
                    for prod in result.get("products", []) or []:
                        s = prod.get("slug")
                        if s and s not in suggested_slugs:
                            suggested_slugs.append(s)

                result_payload = {"name": fn.name, "payload": result}
                _tool_log.append({"type": "tool_result", **result_payload})
                yield "tool_result", result_payload

                tool_results.append(types.Part(
                    function_response=types.FunctionResponse(
                        name=fn.name, response={"result": result},
                    )
                ))

            contents.append(candidate.content)
            contents.append(types.Content(role="tool", parts=tool_results))
            continue

        full_text = "".join((getattr(p, "text", None) or "") for p in parts)
        if not full_text.strip():
            full_text = "Kombin için yeterli sonuç bulamadım — başka bir ürün denemek ister misin?"
        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            yield "token", {"text": chunk}
            await asyncio.sleep(0.01)
        yield "done", {}
        return

    yield "token", {"text": "Kombin için yeterli araştırma yaptım ama net bir sonuç toplayamadım. Tekrar dener misin?"}
    yield "done", {}

def get_tool_log() -> list[dict]:
    return list(_tool_log)

def init_gemini(api_key: str) -> genai.Client | None:
    if not api_key:
        logger.warning("GOOGLE_API_KEY ayarlanmamış — Gemini devre dışı")
        return None
    return genai.Client(api_key=api_key)
