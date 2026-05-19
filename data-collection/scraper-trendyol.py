import argparse
import asyncio
import json
import random
import re
import sys
import traceback
from datetime import datetime
from html import unescape as _html_unescape
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

DEBUG_DIR = Path("debug")
DEBUG_DIR.mkdir(exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]

def dig(obj: Any, *keys, default=None):
    cur = obj
    for k in keys:
        if cur is None:
            return default
        if isinstance(k, int):
            if isinstance(cur, list) and -len(cur) <= k < len(cur):
                cur = cur[k]
            else:
                return default
        else:
            if isinstance(cur, dict) and k in cur:
                cur = cur[k]
            else:
                return default
    return cur if cur is not None else default

DESC_PARAGRAPH_RE = re.compile(
    r'<p[^>]*class="[^"]*product-description-content[^"]*"[^>]*>(.*?)</p>',
    re.DOTALL | re.IGNORECASE,
)
INFO_LIST_LI_RE = re.compile(
    r'<li[^>]*class="[^"]*content-description-item-description[^"]*"[^>]*>(.*?)</li>',
    re.DOTALL | re.IGNORECASE,
)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")

def _strip_html(fragment: str) -> str:
    return _WS_RE.sub(" ", _html_unescape(_TAG_RE.sub("", fragment))).strip()

def extract_extra_info(html_text: str) -> Dict[str, Any]:
    paragraphs = [_strip_html(p) for p in DESC_PARAGRAPH_RE.findall(html_text)]
    paragraphs = [p for p in paragraphs if p]

    info_items: List[str] = []
    seen = set()
    for li in INFO_LIST_LI_RE.findall(html_text):
        text = _strip_html(li)
        if text and text not in seen:
            seen.add(text)
            info_items.append(text)

    return {
        "aciklama": "\n".join(paragraphs),
        "ekBilgiler": info_items,
    }

ATTR_ITEM_RE = re.compile(
    r'<div[^>]*class="[^"]*attribute-item[^"]*"[^>]*>'
    r'\s*<div[^>]*class="name"[^>]*>(.*?)</div>'
    r'.*?<div[^>]*class="value"[^>]*>(.*?)</div>',
    re.DOTALL | re.IGNORECASE,
)

def extract_dom_specs(html_text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for name_raw, val_raw in ATTR_ITEM_RE.findall(html_text):
        name = _strip_html(name_raw)
        val = _strip_html(val_raw)
        if name and val and name not in out:
            out[name] = val
    return out

JSONLD_RE = re.compile(
    r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.DOTALL | re.IGNORECASE,
)

def _iter_jsonld_blocks(html: str):
    for raw in JSONLD_RE.findall(html):
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError:
            continue
        candidates = data if isinstance(data, list) else [data]
        for c in candidates:
            if isinstance(c, dict):
                yield c

def extract_jsonld(html: str) -> Optional[Dict[str, Any]]:
    for c in _iter_jsonld_blocks(html):
        if c.get("@type") in ("ProductGroup", "Product"):
            return c
    return None

def _parse_breadcrumb_items(items: Any) -> List[str]:
    if not isinstance(items, list):
        return []
    chain: List[str] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        nm = _stringify(it.get("name"))
        if not nm and isinstance(it.get("item"), dict):
            nm = _stringify(it["item"].get("name"))
        nm = nm.strip()
        if nm:
            chain.append(nm)
    return chain

def extract_breadcrumb(html: str) -> List[str]:
    for c in _iter_jsonld_blocks(html):

        if c.get("@type") == "BreadcrumbList":
            chain = _parse_breadcrumb_items(c.get("itemListElement"))
            if chain:
                return chain

        bc = c.get("breadcrumb")
        if isinstance(bc, dict) and bc.get("@type") == "BreadcrumbList":
            chain = _parse_breadcrumb_items(bc.get("itemListElement"))
            if chain:
                return chain
    return []

def _stringify(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, list):
        parts: List[str] = []
        for it in v:
            s = _stringify(it).strip()
            if s:
                parts.append(s)
        return "\n".join(parts)
    if isinstance(v, dict):
        for k in ("name", "value", "text", "@value"):
            x = v.get(k)
            if x:
                return _stringify(x)
        return ""
    return str(v)

def _price_to_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None

def _extract_offer(node: Dict) -> Dict[str, Any]:
    offer = node.get("offers") or {}
    if isinstance(offer, list) and offer:
        offer = offer[0]
    if not isinstance(offer, dict):
        return {}
    return {
        "fiyat": _price_to_float(offer.get("price")),
        "paraBirimi": offer.get("priceCurrency") or "TRY",
        "stokta": offer.get("availability") != "https://schema.org/OutOfStock",
    }

def _normalize_image_list(img: Any) -> List[str]:
    out: List[str] = []
    seen: set = set()

    def _add(item: Any) -> None:
        if not item:
            return
        if isinstance(item, str):
            url = item.strip()
            if url and url not in seen:
                seen.add(url)
                out.append(url)
        elif isinstance(item, list):
            for x in item:
                _add(x)
        elif isinstance(item, dict):

            _add(item.get("url"))
            _add(item.get("contentUrl"))

    _add(img)
    return out

def parse_product(pg: Dict) -> Dict:

    name = _stringify(pg.get("name")).strip() or "N/A"

    brand_raw = pg.get("manufacturer") or pg.get("brand")
    brand = _stringify(brand_raw).strip() or None

    root_offer = _extract_offer(pg)
    price_val = root_offer.get("fiyat")
    currency = root_offer.get("paraBirimi")
    in_stock = root_offer.get("stokta", True)
    if price_val is None:
        for v in pg.get("hasVariant") or []:
            v_off = _extract_offer(v or {})
            if v_off.get("fiyat") is not None:
                price_val = v_off["fiyat"]
                currency = currency or v_off.get("paraBirimi")
                break

    images = _normalize_image_list(pg.get("image"))

    rating: Dict[str, Any] = {}
    ar = pg.get("aggregateRating")
    if isinstance(ar, dict):
        rv = _price_to_float(ar.get("ratingValue"))
        rc = ar.get("ratingCount")
        revc = ar.get("reviewCount")
        if rv is not None:
            rating["puan"] = rv
        try:
            if rc is not None:
                rating["puanSayisi"] = int(rc)
        except (TypeError, ValueError):
            pass
        try:
            if revc is not None:
                rating["yorumSayisi"] = int(revc)
        except (TypeError, ValueError):
            pass

    own_color = _stringify(pg.get("color")).strip() or None

    sizes: List[Dict] = []
    seen_sizes: set = set()

    variants: List[Dict] = []
    for v in pg.get("hasVariant") or []:
        if not isinstance(v, dict):
            continue
        v_sizes_raw = v.get("size") or []
        if isinstance(v_sizes_raw, str):
            v_sizes_raw = [v_sizes_raw]
        v_off = _extract_offer(v)
        v_in_stock = v_off.get("stokta", True)
        for s in v_sizes_raw:
            label = str(s).strip()
            if not label or label in seen_sizes:
                continue
            seen_sizes.add(label)
            sizes.append({"beden": label, "stokta": v_in_stock})

        v_color = _stringify(v.get("color")).strip() or None
        v_url = _stringify(v.get("url") or v.get("@id"))
        v_id = v.get("productID") or v.get("sku")
        if not v_id and v_url:
            m_id = re.search(r"-p-(\d+)", v_url)
            if m_id:
                v_id = m_id.group(1)
        v_images = _normalize_image_list(v.get("image"))
        variants.append({
            "ad": v_color,
            "contentId": str(v_id) if v_id else None,
            "url": v_url or None,
            "gorseller": v_images,
            "fiyat": v_off.get("fiyat"),
            "paraBirimi": v_off.get("paraBirimi"),
            "stokta": v_in_stock,
            "bedenler": [str(s).strip() for s in v_sizes_raw if str(s).strip()],
        })

    desc = _stringify(pg.get("description"))
    description = [line.strip() for line in desc.split("\n") if line.strip()]

    features: Dict[str, str] = {}
    for a in pg.get("additionalProperty") or []:
        if not isinstance(a, dict):
            continue
        k_raw = a.get("name") or a.get("propertyID")
        val_raw = a.get("unitText") or a.get("value")
        k = _stringify(k_raw).strip()
        val = _stringify(val_raw).strip()
        if k and val:
            features[k] = val

    content_id = pg.get("productGroupID") or pg.get("sku")
    if not content_id:
        m = re.search(r"-p-(\d+)", _stringify(pg.get("@id")))
        if m:
            content_id = m.group(1)

    out: Dict[str, Any] = {
        "ürünAdı": str(name).strip(),
        "marka": brand,
        "rengi": own_color,
        "fiyat": price_val,
        "paraBirimi": currency or "TRY",
        "stokta": in_stock,
        "gorseller": images,
        "bedenler": sizes,
        "renkVaryantlari": variants,
        "ürünBilgileri": {
            "açıklama": "\n".join(description),
            "özellikler": features,
        },
        "_contentId": content_id,
    }
    if rating:
        out["puanlama"] = rating
    return out

_LOAD_MORE_LABELS = [
    "Daha Fazla Göster",
    "Daha Fazla Yükle",
    "Tümünü Göster",
    "Devamını Gör",
    "Daha Fazla Yorum",
    "Daha Fazla Soru",
]

async def _scroll_until_stable(page: Page, item_selector: str,
                               max_iter: int = 300, pause_ms: int = 700,
                               max_count: Optional[int] = None) -> int:
    prev_count = -1
    prev_height = -1
    stable = 0
    for _ in range(max_iter):
        count = await page.locator(item_selector).count()

        if max_count is not None and count >= max_count:
            return count
        try:
            height = await page.evaluate("document.body.scrollHeight")
        except Exception:
            height = prev_height
        if count == prev_count and height == prev_height:
            stable += 1
            if stable >= 4:
                break
        else:
            stable = 0
        prev_count = count
        prev_height = height
        try:
            await page.evaluate(
                """(labels) => {
                    document.querySelectorAll('button, a, span, div').forEach(b => {
                        if (b.children.length > 0 && b.tagName !== 'BUTTON') return;
                        const t = (b.textContent || '').trim();
                        if (labels.includes(t)) {
                            try {
                                b.scrollIntoView({block: 'center'});
                                b.click();
                            } catch (e) {}
                        }
                    });
                }""",
                _LOAD_MORE_LABELS,
            )
        except Exception:
            pass
        try:
            await page.mouse.wheel(0, 1500)
        except Exception:
            pass
        try:
            await page.evaluate(
                "window.scrollTo(0, document.body.scrollHeight)"
            )
        except Exception:
            pass
        await page.wait_for_timeout(pause_ms)
    return prev_count if prev_count > 0 else 0

async def _click_expand_buttons(page: Page, label: str = "Devamını Oku") -> int:
    return await page.evaluate(
        """(lbl) => {
            const els = Array.from(document.querySelectorAll('button, span, a, div'))
                .filter(el => {
                    if (!el.innerText) return false;
                    const t = el.innerText.trim();
                    if (t !== lbl) return false;
                    return el.children.length === 0 || el.tagName === 'BUTTON';
                });
            let n = 0;
            els.forEach(b => { try { b.click(); n++; } catch (e) {} });
            return n;
        }""",
        label,
    )

def _clean_truncate_suffix(text: str) -> str:
    text = text.strip()
    for suffix in ("Devamını Oku", "Daha Az Göster"):
        while text.endswith(suffix):
            text = text[: -len(suffix)].rstrip(" \n\r\t…")
    return text.strip()

async def fetch_reviews_html(ctx: BrowserContext, product_url: str,
                             max_count: Optional[int] = 2500) -> List[Dict]:
    base = product_url.split("?")[0].rstrip("/")
    url = f"{base}/yorumlar"
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            await page.wait_for_selector("div.review", timeout=10000)
        except Exception:
            print("  ⚠️  yorum: .review öğesi yüklenmedi")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            (DEBUG_DIR / f"reviews_page_{ts}.html").write_text(
                await page.content(), encoding="utf-8"
            )
            return []

        await _scroll_until_stable(page, "div.review", max_count=max_count)

        expanded = await _click_expand_buttons(page, "Devamını Oku")
        if expanded:
            await page.wait_for_timeout(400)
            print(f"  ℹ️  {expanded} yorum genişletildi")

        items = await page.evaluate(
            """() => Array.from(document.querySelectorAll('div.review')).map(r => {
                // Yorum metni — :scope > .review-comment (direct child)
                // İç içe .review-comment var, sadece direkt çocuğu al ki şikayet
                // modal'ının içine sızmayalım.
                const commentEl = r.querySelector(':scope > .review-comment');
                // Şikayet modal text'ini comment kapsamından çıkar
                let text = '';
                if (commentEl) {
                    const clone = commentEl.cloneNode(true);
                    clone.querySelectorAll('.complain-text, ._modal_2c4fc88, ._modal-wrapper_e4b7e83')
                        .forEach(n => n.remove());
                    text = clone.innerText.trim();
                }

                // Boy / Kilo / Beden / vs — TÜM attribute label-value çiftleri
                const attrs = {};
                r.querySelectorAll('.product-attribute-product-attribute').forEach(a => {
                    const k = a.querySelector('.product-attribute-label');
                    const v = a.querySelector('.product-attribute-value');
                    if (k && v) {
                        const kt = k.innerText.trim();
                        const vt = v.innerText.trim();
                        if (kt && vt) attrs[kt] = vt;
                    }
                });

                // Yıldız puanı — Trendyol CSS trick: container'ın width'i 5 yıldız,
                // .star-rating-full-star div'i içinde padding-inline-end ile sağdan
                // boş yıldızlar gizlenir. puan = (1 - padding/containerWidth) * 5
                let puan = null;
                const starCont = r.querySelector('.star-rating-star-container');
                if (starCont) {
                    const fullStar = starCont.querySelector('.star-rating-full-star');
                    if (fullStar) {
                        const w = starCont.clientWidth || starCont.offsetWidth || 0;
                        const padStr = fullStar.style.paddingInlineEnd || '0px';
                        const padPx = parseFloat(padStr) || 0;
                        if (w > 0) {
                            // 0.5 hassasiyetle round
                            puan = Math.round((1 - padPx / w) * 5 * 2) / 2;
                            if (puan < 0) puan = 0;
                            if (puan > 5) puan = 5;
                        }
                    }
                }

                // Tarih (3 span: 12 Mart 2026)
                const dateEl = r.querySelector('.detail-item.date');
                const nameEl = r.querySelector('.detail-item.name');

                // Satıcı — "<strong>X</strong> satıcısından alındı"
                const sellerEl = r.querySelector('.seller-name-wrapper strong');

                return {
                    text: text,
                    attrs: attrs,
                    puan: puan || null,
                    tarih: dateEl ? dateEl.innerText.trim().replace(/\\s+/g,' ') : null,
                    kullanici: nameEl ? nameEl.innerText.trim() : null,
                    satici: sellerEl ? sellerEl.innerText.trim() : null,
                };
            })"""
        )

        out: List[Dict] = []
        seen_texts: set = set()
        for it in items:
            if max_count is not None and len(out) >= max_count:
                break
            text = _clean_truncate_suffix(it.get("text") or "")
            if not text:
                continue

            text_key = text.lower()
            if text_key in seen_texts:
                continue
            seen_texts.add(text_key)

            row: Dict[str, Any] = {"text": text}

            attrs = it.get("attrs") or {}

            label_map = {
                "Boy": "boy",
                "Kilo": "kilo",
                "Beden": "beden",
            }
            for label, key in label_map.items():
                if attrs.get(label):
                    row[key] = attrs[label]

            extras = {k: v for k, v in attrs.items() if k not in label_map}
            if extras:
                row["digerOzellikler"] = extras

            for k in ("puan", "tarih", "kullanici", "satici"):
                v = it.get(k)
                if v not in (None, ""):
                    row[k] = v
            out.append(row)
        return out
    finally:
        await page.close()

_QA_CARD_JS = """() => Array.from(document.querySelectorAll('.question-answer-card')).map(c => {
    const qEl = c.querySelector('.question-answer-card-question-text');
    const aEl = c.querySelector('.seller-answer-content-text');
    const sellerEl = c.querySelector('.seller-answer-content-header-seller-name-bold');
    const dateEls = c.querySelectorAll('.question-answer-card-question-info-left-item');
    let qDate = null;
    dateEls.forEach(el => {
        const t = el.innerText.trim();
        if (t) qDate = t;
    });
    const answerInfoEl = c.querySelector('.seller-answer-content-header-answered-date-message');
    return {
        soru: qEl ? qEl.innerText.trim() : '',
        cevap: aEl ? aEl.innerText.trim() : '',
        satici: sellerEl ? sellerEl.innerText.trim() : null,
        soruTarihi: qDate,
        cevapBilgi: answerInfoEl ? answerInfoEl.innerText.trim() : null,
    };
})"""

async def fetch_qa_html(ctx: BrowserContext, product_url: str,
                        content_id: str,
                        max_count: Optional[int] = 2500) -> List[Dict]:
    base = product_url.split("?")[0].rstrip("/")
    url = f"{base}/saticiya-sor?qaContentId={content_id}"
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=45000)
        try:
            await page.wait_for_selector(".question-answer-card", timeout=10000)
        except Exception:
            print("  ⚠️  Q&A: .question-answer-card öğesi yüklenmedi")
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            (DEBUG_DIR / f"qa_page_{ts}.html").write_text(
                await page.content(), encoding="utf-8"
            )
            return []

        seen: Dict[str, Dict] = {}
        prev_count = -1
        prev_height = -1
        stable = 0
        for _ in range(300):
            try:
                await page.evaluate(
                    """() => {
                        document.querySelectorAll('button, span, a, div').forEach(b => {
                            if (b.children.length > 0 && b.tagName !== 'BUTTON') return;
                            const t = (b.textContent || '').trim();
                            if (t === 'Devamını Oku') {
                                try { b.click(); } catch (e) {}
                            }
                        });
                    }"""
                )
                await page.wait_for_timeout(150)
            except Exception:
                pass

            try:
                batch = await page.evaluate(_QA_CARD_JS)
            except Exception:
                batch = []
            for it in batch:
                k = (it.get("soru") or "").strip()
                if k and k not in seen:
                    seen[k] = it

            if max_count is not None and len(seen) >= max_count:
                break

            try:
                height = await page.evaluate("document.body.scrollHeight")
            except Exception:
                height = prev_height
            count = len(seen)
            if count == prev_count and height == prev_height:
                stable += 1
                if stable >= 5:
                    break
            else:
                stable = 0
            prev_count = count
            prev_height = height

            try:
                await page.mouse.wheel(0, 1500)
            except Exception:
                pass
            try:
                await page.evaluate(
                    "window.scrollTo(0, document.body.scrollHeight)"
                )
            except Exception:
                pass
            await page.wait_for_timeout(900)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        (DEBUG_DIR / f"qa_page_{ts}.html").write_text(
            await page.content(), encoding="utf-8"
        )
        print(f"  ℹ️  Q&A toplam benzersiz kart: {len(seen)}")

        out: List[Dict] = []
        for it in seen.values():
            if max_count is not None and len(out) >= max_count:
                break
            soru = _clean_truncate_suffix(it.get("soru") or "")
            cevap = _clean_truncate_suffix(it.get("cevap") or "")
            if not soru:
                continue
            row: Dict = {"soru": soru, "cevap": cevap}
            for k in ("satici", "soruTarihi", "cevapBilgi"):
                v = it.get(k)
                if v:
                    row[k] = v
            out.append(row)
        return out
    finally:
        await page.close()

class TrendyolScraper:
    def __init__(self, headless: bool = True) -> None:
        self.headless = headless
        self.pw = None
        self.browser: Optional[Browser] = None
        self.ctx: Optional[BrowserContext] = None
        self.current_ua: str = USER_AGENTS[0]

    async def _open_context(self, ua: Optional[str] = None) -> None:
        if self.ctx is not None:
            try:
                await self.ctx.close()
            except Exception:
                pass
            self.ctx = None
        self.current_ua = ua or random.choice(USER_AGENTS)
        assert self.browser is not None
        self.ctx = await self.browser.new_context(
            user_agent=self.current_ua,
            locale="tr-TR",
            extra_http_headers={"Accept-Language": "tr-TR,tr;q=0.9"},
            viewport={"width": 1440, "height": 900},
        )
        await self.ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"
        )

    async def start(self) -> None:
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch(
            headless=self.headless,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        await self._open_context(USER_AGENTS[0])

    async def rotate_ua(self) -> None:
        ua = random.choice([u for u in USER_AGENTS if u != self.current_ua] or USER_AGENTS)
        await self._open_context(ua)

    async def stop(self) -> None:
        if self.ctx:
            await self.ctx.close()
        if self.browser:
            await self.browser.close()
        if self.pw:
            await self.pw.stop()

    async def scrape(self, url: str,
                     max_reviews: Optional[int] = 2500,
                     max_qa: Optional[int] = 2500) -> Dict:
        page = await self.ctx.new_page()
        try:
            print(f"\n🔗 {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass

            html_initial = await page.content()
            jsonld = extract_jsonld(html_initial)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")

            if not jsonld:
                debug_path = DEBUG_DIR / f"failed_html_{ts}.html"
                debug_path.write_text(html_initial, encoding="utf-8")
                return {
                    "error": "JSON-LD ProductGroup bulunamadı — HTML kaydedildi",
                    "debug_file": str(debug_path),
                    "url": url,
                }

            (DEBUG_DIR / f"jsonld_{ts}.json").write_text(
                json.dumps(jsonld, ensure_ascii=False, indent=2), encoding="utf-8"
            )

            parsed = parse_product(jsonld)

            breadcrumb = extract_breadcrumb(html_initial)
            if breadcrumb:
                parsed["kategori"] = breadcrumb

            try:
                dismissed = await page.evaluate(
                    """() => {
                        const els = Array.from(document.querySelectorAll('button, a, div, span'));
                        for (const e of els) {
                            const t = (e.textContent || '').trim();
                            if (t === 'Anladım') {
                                try { e.click(); return true; } catch (err) {}
                            }
                        }
                        return false;
                    }"""
                )
                if dismissed:
                    await page.wait_for_timeout(400)
            except Exception:
                pass

            try:
                scrolled = await page.evaluate(
                    """() => {
                        const sels = [
                            '.product-info-content',
                            '.product-description-section',
                            '.content-description-main-container',
                            '[data-drroot="content-description"]',
                            '.product-attributes-container',
                        ];
                        for (const s of sels) {
                            const el = document.querySelector(s);
                            if (el) {
                                el.scrollIntoView({block: 'center', behavior: 'instant'});
                                return s;
                            }
                        }
                        window.scrollTo(0, document.body.scrollHeight);
                        return null;
                    }"""
                )
                await page.wait_for_timeout(1200)
                if scrolled:
                    print(f"  ℹ️  bilgi bölümü: scroll → {scrolled}")
            except Exception:
                pass

            try:
                try:
                    await page.wait_for_selector(
                        ".show-more-button", timeout=8000
                    )
                except Exception:
                    pass
                btn_count = await page.locator(".show-more-button").count()
                expanded = await page.evaluate(
                    """() => {
                        const labels = ['Daha Fazla Göster', 'Devamını Oku'];
                        const btns = Array.from(document.querySelectorAll('.show-more-button'));
                        let n = 0;
                        btns.forEach(b => {
                            const txt = (b.textContent || '').trim();
                            if (labels.includes(txt)) {
                                try {
                                    b.scrollIntoView({block: 'center'});
                                    b.click();
                                    n++;
                                } catch (e) {}
                            }
                        });
                        return n;
                    }"""
                )
                print(
                    f"  ℹ️  show-more: {btn_count} buton DOM'da, "
                    f"{expanded} tıklandı"
                )
                if expanded:
                    await page.wait_for_timeout(600)
            except Exception as e:
                print(f"  ⚠️  expand hatası: {e!r}")

            html_final = await page.content()
            (DEBUG_DIR / f"product_page_{ts}.html").write_text(
                html_final, encoding="utf-8"
            )

            extras = extract_extra_info(html_final)
            if extras["aciklama"]:
                parsed["ürünBilgileri"]["açıklama"] = extras["aciklama"]
            if extras["ekBilgiler"]:
                parsed["ürünBilgileri"]["ekBilgiler"] = extras["ekBilgiler"]

            dom_specs = extract_dom_specs(html_final)
            if dom_specs:

                merged = {**(parsed["ürünBilgileri"].get("özellikler") or {}), **dom_specs}
                parsed["ürünBilgileri"]["özellikler"] = merged

            price_str = (
                f"{parsed['fiyat']:.2f} {parsed['paraBirimi']}"
                if parsed.get("fiyat") is not None
                else "N/A"
            )
            print(f"  ✅ {parsed['ürünAdı'][:70]}")
            print(f"  ✅ Marka: {parsed.get('marka') or 'N/A'} · Renk: {parsed.get('rengi') or 'N/A'}")
            print(f"  ✅ Fiyat: {price_str}")
            print(f"  ✅ Görsel: {len(parsed.get('gorseller', []))} · Varyant: {len(parsed.get('renkVaryantlari', []))}")
            print(f"  ✅ Beden: {len(parsed['bedenler'])}")
            if parsed.get("puanlama"):
                pl = parsed["puanlama"]
                print(
                    f"  ✅ Puan: {pl.get('puan', '?')} ({pl.get('puanSayisi', '?')} oy / "
                    f"{pl.get('yorumSayisi', '?')} yorum)"
                )
            if parsed.get("kategori"):
                print(f"  ✅ Kategori: {' > '.join(parsed['kategori'])}")
            print(
                f"  ✅ Açıklama: {len(parsed['ürünBilgileri']['açıklama'])} kr "
                f"/ Özellik: {len(parsed['ürünBilgileri']['özellikler'])} "
                f"/ EkBilgi: {len(parsed['ürünBilgileri'].get('ekBilgiler', []))}"
            )

            content_id = parsed.pop("_contentId", None)

            reviews: List[Dict] = []
            qa: List[Dict] = []
            try:
                reviews = await fetch_reviews_html(self.ctx, url, max_count=max_reviews)
            except Exception as e:
                print(f"  ⚠️  Yorum scrape hatası: {e!r}")
            if content_id:
                try:
                    qa = await fetch_qa_html(self.ctx, url, str(content_id), max_count=max_qa)
                except Exception as e:
                    print(f"  ⚠️  Q&A scrape hatası: {e!r}")
            else:
                print("  ⚠️  contentId bulunamadı, Q&A çekilemedi")

            print(f"  ✅ Yorum: {len(reviews)}")
            print(f"  ✅ Soru-Cevap: {len(qa)}")

            return {
                **parsed,
                "değerlendirmeler": reviews,
                "soruCevaplar": qa,
                "url": url,
                "çekilişZamanı": datetime.now().isoformat(),
            }
        finally:
            await page.close()

def _read_urls_file(path: Path) -> List[str]:
    urls: List[str] = []
    seen: set = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "trendyol.com" not in line:
            print(f"⚠️  Geçersiz URL atlandı: {line}")
            continue
        if line in seen:
            continue
        seen.add(line)
        urls.append(line)
    return urls

def _safe_filename(data: Dict, url: str) -> str:
    cid = data.get("_contentId") or data.get("contentId")
    if cid:
        return f"trendyol_{cid}.json"
    m = re.search(r"/([^/]+)-p-(\d+)", url)
    if m:
        return f"trendyol_{m.group(2)}_{m.group(1)[:40]}.json"
    return f"trendyol_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

async def _run_batch(
    scraper: TrendyolScraper,
    urls: List[str],
    out_dir: Path,
    delay: float,
    jitter: float,
    rotate_ua: bool,
    max_reviews: int,
    max_qa: int,
) -> Dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = {"toplam": len(urls), "ok": 0, "hata": 0, "atlandi": 0}

    for i, url in enumerate(urls, start=1):
        fname_guess = _safe_filename({}, url)
        target = out_dir / fname_guess

        if target.exists():
            print(f"\n[{i}/{len(urls)}] ⏭  Zaten var: {target.name}")
            stats["atlandi"] += 1
            continue

        if rotate_ua and i > 1:
            await scraper.rotate_ua()

        print(f"\n[{i}/{len(urls)}] UA: …{scraper.current_ua[-30:]}")
        try:
            data = await scraper.scrape(url, max_reviews=max_reviews, max_qa=max_qa)
        except Exception as e:
            print(f"  ❌ Hata: {e!r}")

            tb_lines = traceback.format_exc().splitlines()
            for line in tb_lines[-6:]:
                print(f"     {line}")
            stats["hata"] += 1
            data = None

        if data:
            fname = _safe_filename(data, url)
            (out_dir / fname).write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"  💾 Kaydedildi: {out_dir / fname}")
            stats["ok"] += 1

        if i < len(urls):
            wait = max(0.0, delay + random.uniform(-jitter, jitter))
            print(f"  ⏳ {wait:.1f}sn bekleniyor (bot engeli için)...")
            await asyncio.sleep(wait)

    return stats

async def _run_interactive(
    scraper: TrendyolScraper, out_dir: Path,
    max_reviews: int, max_qa: int,
) -> None:
    while True:
        url = input("\nÜrün URL (çıkış için boş): ").strip()
        if not url:
            break
        if "trendyol.com" not in url:
            print("Geçersiz URL")
            continue
        try:
            data = await scraper.scrape(url, max_reviews=max_reviews, max_qa=max_qa)
        except Exception as e:
            print(f"Hata: {e}")
            continue
        fname = _safe_filename(data, url)
        (out_dir / fname).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Kaydedildi: {out_dir / fname}")
        if input("Devam? (e/h): ").strip().lower() not in ("e", "evet"):
            break

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="scraper-trendyol",
        description="Trendyol ürün scraper — JSON-LD + Playwright DOM",
    )
    p.add_argument("--urls", type=Path, help="URL listesi (her satır 1 URL, # yorum)")
    p.add_argument("--url", action="append", default=[], help="Tek URL (tekrarlanabilir)")
    p.add_argument(
        "--out",
        type=Path,
        default=Path("data-collection/raw"),
        help="Çıktı klasörü (varsayılan: data-collection/raw)",
    )
    p.add_argument("--delay", type=float, default=8.0, help="Ürün arası bekleme (sn)")
    p.add_argument("--jitter", type=float, default=4.0, help="Bekleme ±jitter (sn)")
    p.add_argument(
        "--max-reviews", type=int, default=2500,
        help="Ürün başına maks yorum sayısı (sayfayı sınırsız scroll etmemek için)",
    )
    p.add_argument(
        "--max-qa", type=int, default=2500,
        help="Ürün başına maks soru-cevap sayısı",
    )
    p.add_argument(
        "--no-rotate-ua",
        action="store_true",
        help="Her ürünün başında User-Agent rotation yapma",
    )
    p.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        default=True,
        help="Tarayıcıyı görünmez koş (varsayılan)",
    )
    p.add_argument(
        "--show-browser",
        dest="headless",
        action="store_false",
        help="Tarayıcıyı göster (debug için)",
    )
    return p.parse_args()

async def main() -> None:
    args = _parse_args()
    print("=" * 70)
    print("Trendyol Scraper")
    print("=" * 70)

    urls: List[str] = []
    if args.urls:
        if not args.urls.exists():
            print(f"❌ URL dosyası bulunamadı: {args.urls}")
            sys.exit(2)
        urls.extend(_read_urls_file(args.urls))
    for u in args.url:
        u = u.strip()
        if "trendyol.com" in u and u not in urls:
            urls.append(u)

    args.out.mkdir(parents=True, exist_ok=True)

    scraper = TrendyolScraper(headless=args.headless)
    await scraper.start()
    try:
        if urls:
            print(
                f"📋 {len(urls)} URL · çıktı: {args.out} · "
                f"delay: {args.delay}±{args.jitter}sn · "
                f"UA rotation: {'kapalı' if args.no_rotate_ua else 'açık'} · "
                f"maks yorum: {args.max_reviews} · maks Q&A: {args.max_qa}"
            )
            stats = await _run_batch(
                scraper,
                urls,
                out_dir=args.out,
                delay=args.delay,
                jitter=args.jitter,
                rotate_ua=not args.no_rotate_ua,
                max_reviews=args.max_reviews,
                max_qa=args.max_qa,
            )
            print("\n" + "=" * 70)
            print(
                f"✅ Bitti — {stats['ok']} başarılı / "
                f"{stats['hata']} hata / "
                f"{stats['atlandi']} atlandı (zaten vardı) / "
                f"{stats['toplam']} toplam"
            )
        else:
            await _run_interactive(scraper, args.out, args.max_reviews, args.max_qa)
    finally:
        await scraper.stop()

if __name__ == "__main__":
    asyncio.run(main())