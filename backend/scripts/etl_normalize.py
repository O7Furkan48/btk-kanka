import hashlib
import html
import json
import logging
import os
import random
import re
import sys
from pathlib import Path

def _html_unescape_deep(text: str, max_iter: int = 10) -> str:
    prev = ""
    out = text
    for _ in range(max_iter):
        if prev == out:
            break
        prev = out
        out = html.unescape(out)

    out = re.sub(r"\b(amp\s+){2,}", "", out, flags=re.I)
    return out

import pandas as pd
from tqdm import tqdm

BACKEND_DIR = Path(__file__).parent.parent
RAW_DIR = BACKEND_DIR.parent / "data-collection" / "raw"
OUT_DIR = BACKEND_DIR / "app" / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(BACKEND_DIR.parent / "data-collection"))
try:
    from analyze_raw import guess_category  # type: ignore
except ImportError:
    def guess_category(item: dict) -> str:  # type: ignore[misc]
        cats = item.get("kategori", [])
        if isinstance(cats, list) and cats:
            return cats[-1]
        return "Diğer"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("etl")

RENK_HEX: dict[str, tuple[str, str]] = {
    "beyaz": ("#FAFAFA", "#E2E8F0"),
    "siyah": ("#0F172A", "#0F172A"),
    "lacivert": ("#1E2E55", "#1E2E55"),
    "mavi": ("#2563EB", "#2563EB"),
    "kırmızı": ("#EF4444", "#EF4444"),
    "pembe": ("#EC4899", "#EC4899"),
    "mor": ("#8B5CF6", "#8B5CF6"),
    "yeşil": ("#10B981", "#10B981"),
    "haki": ("#78716C", "#78716C"),
    "kahverengi": ("#92400E", "#92400E"),
    "taba": ("#B45309", "#B45309"),
    "bej": ("#D4B896", "#D4B896"),
    "krem": ("#FFFBEB", "#E2E8F0"),
    "gri": ("#6B7280", "#6B7280"),
    "antrasit": ("#374151", "#374151"),
    "sarı": ("#F59E0B", "#F59E0B"),
    "turuncu": ("#F97316", "#F97316"),
    "ekru": ("#FAF0E6", "#D4B896"),
    "gold": ("#D4AF37", "#D4AF37"),
    "gümüş": ("#C0C0C0", "#C0C0C0"),
    "bordo": ("#800020", "#800020"),
    "fuşya": ("#FF0090", "#FF0090"),
    "denim": ("#1560BD", "#1560BD"),
}

CARE_ICON_MAP = {
    "yıkama": "wash",
    "derecede": "wash",
    "elde yıka": "wash",
    "ütü": "iron",
    "ütüleme": "iron",
    "depolama": "shield",
    "kargo": "truck",
    "teslimat": "truck",
}

CAT_KEY_MAP_ORDERED: list[tuple[str, str]] = [

    ("takım elbise", "shirt"),
    ("trençkot", "shirt"),
    ("pardösü", "shirt"),
    ("pardosu", "shirt"),

    ("sweatshirt", "shirt"),
    ("gömlek", "shirt"),
    ("tişört", "shirt"),
    ("kazak", "shirt"),
    ("hırka", "shirt"),
    ("bluz", "shirt"),
    ("ceket", "shirt"),
    ("mont", "shirt"),
    ("kaban", "shirt"),

    ("pantolon", "shirt"),
    ("şort", "shirt"),
    ("şort", "shirt"),
    ("eşofman", "shirt"),
    ("tayt", "shirt"),
    ("jean", "shirt"),

    ("etek", "dress"),
    ("elbise", "dress"),

    ("sneaker", "shoe"),
    ("ayakkabı", "shoe"),
    ("bot", "shoe"),
    ("terlik", "shoe"),
    ("çizme", "shoe"),

    ("bileklik", "bag"),
    ("kolye", "bag"),
    ("küpe", "bag"),
    ("yüzük", "bag"),
    ("saat", "bag"),
    ("çanta", "bag"),
    ("cüzdan", "bag"),
    ("kemer", "bag"),
    ("aksesuar", "bag"),

    ("kozmetik", "cosmetics"),
    ("cilt", "cosmetics"),
    ("parfüm", "cosmetics"),
    ("makyaj", "cosmetics"),

    ("teknoloji", "tech"),
    ("bilgisayar", "tech"),
    ("telefon", "tech"),

    ("spor", "sport"),
    ("yoga", "sport"),

    ("bebek", "baby"),
    ("çocuk", "baby"),

    ("ev", "home"),
    ("mutfak", "home"),
    ("dekorasyon", "home"),
    ("yaşam", "home"),
]

PH_BG_COUNT = 8

rng_global = random.Random(2026)

def _slug(url: str, filename: str) -> str:
    m = re.search(r"trendyol\.com/[^/]+/([^/?\s]+)", url or "")
    if m:
        return m.group(1)[:80]

    name = Path(filename).stem.replace("trendyol_", "")
    parts = name.split("_", 1)
    return parts[1] if len(parts) > 1 else parts[0]

def _color_to_hex(name: str) -> tuple[str, str]:
    lower = name.lower()
    for key, val in RENK_HEX.items():
        if key in lower:
            return val
    return ("#94A3B8", "#94A3B8")

def _parse_colors(item: dict) -> list[dict]:
    variants = item.get("renkVaryantlari") or []
    seen = set()
    colors = []
    for v in variants:
        ad = v.get("ad") or item.get("rengi") or "Standart"
        if ad in seen:
            continue
        seen.add(ad)
        hex_val, border = _color_to_hex(ad)
        colors.append({"name": ad.capitalize(), "hex": hex_val, "border": border})
    if not colors:
        renk = item.get("rengi") or "Standart"
        hex_val, border = _color_to_hex(renk)
        colors.append({"name": renk.capitalize(), "hex": hex_val, "border": border})
    return colors

def _clean_beden_label(label: str) -> str:
    s = label.strip()

    m = re.match(r"^(\d{2,3})\s*[-/]\s*\d{1,2}\s*Drop\b", s, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    m = re.match(r"^(\d{2,3})\s+Drop\b", s, flags=re.IGNORECASE)
    if m:
        return m.group(1)

    s = re.sub(r"\s+drop\b", "", s, flags=re.IGNORECASE).strip()
    return s

def _parse_sizes(item: dict) -> list[dict]:
    bedenler = item.get("bedenler") or []
    if not bedenler:
        for v in (item.get("renkVaryantlari") or []):
            bedenler = v.get("bedenler") or []
            if bedenler:
                break

    out = []
    seen = set()
    for b in bedenler:
        if isinstance(b, dict):
            label = str(b.get("beden") or b.get("label") or "").strip()
            available = bool(b.get("stokta", True))
        else:
            label = str(b).strip()
            available = True
        label = _clean_beden_label(label)
        if not label or label in seen:
            continue
        seen.add(label)
        out.append({"label": label, "risk": "low", "available": available})
    return out

def _parse_care(specs: dict) -> list[dict]:
    care = []
    for key, val in specs.items():
        lower_key = key.lower()
        icon = "check"
        for kw, ic in CARE_ICON_MAP.items():
            if kw in lower_key or kw in val.lower():
                icon = ic
                break
        if any(kw in lower_key for kw in ("yıkama", "ütü", "depolama", "kargo", "teslimat", "bakım")):
            care.append({"icon": icon, "text": val})
    return care[:5]

def _parse_specs(specs: dict) -> list[list[str]]:
    skip = {"yıkama talimatları", "kargo", "teslimat", "bakım"}
    return [
        [k, v]
        for k, v in specs.items()
        if k.lower() not in skip and v
    ][:15]

def _parse_description(raw: str | list | None) -> list[str]:
    if not raw:
        return []
    if isinstance(raw, list):
        raw = " ".join(str(x) for x in raw)

    raw = _html_unescape_deep(str(raw))

    raw = re.sub(r"\s+", " ", raw).strip()
    paras = [p.strip() for p in re.split(r"\n{2,}|\r\n\r\n", raw) if p.strip()]
    return paras[:5] or [raw[:500]]

def _cat_key(kategori: list[str]) -> str:
    full = " ".join(kategori).lower()
    for word, key in CAT_KEY_MAP_ORDERED:
        if word in full:
            return key
    return "shirt"

def _format_price(price: float) -> str:
    return f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _build_summary(item: dict, kategori: list[str], özellikler: dict, puanlama: dict) -> str:
    marka = (item.get("marka") or "").strip()

    parca_tipi = kategori[-1] if kategori else ""
    if marka and parca_tipi:
        parca_tipi = parca_tipi.replace(marka, "").strip()

    for prefix in ("Kadın", "Erkek", "Unisex", "Çocuk", "Bebek"):
        if parca_tipi.startswith(prefix):
            parca_tipi = parca_tipi[len(prefix):].strip()
    parca_tipi = parca_tipi.lower() or "ürün"

    def _norm(v) -> str:
        if not v:
            return ""
        s = str(v).strip()
        return s if len(s) <= 60 else ""

    kalip = _norm(özellikler.get("Kalıp") or özellikler.get("Kesim"))
    kumas = _norm(özellikler.get("Kumaş Tipi") or özellikler.get("Materyal") or özellikler.get("Materyal Bileşeni"))
    renk = _norm(özellikler.get("Renk"))
    ortam = _norm(özellikler.get("Ortam") or özellikler.get("Kullanım Alanı"))
    persona = _norm(özellikler.get("Persona") or özellikler.get("Hedef"))

    lead_parts = []
    if kalip:
        lead_parts.append(kalip.lower())
    if kumas:
        lead_parts.append(kumas.lower())
    if renk and renk.lower() not in " ".join(lead_parts).lower():
        lead_parts.append(renk.lower())

    lead = " ".join(lead_parts).strip()
    if lead:
        s1 = f"{lead.capitalize()} bir {parca_tipi}"
    else:
        s1 = parca_tipi.capitalize() if parca_tipi else "Ürün"

    if marka:
        s1 += f"; {marka} markasının öne çıkan bir parçası."
    else:
        s1 += " — şık, kullanışlı ve günlük tarza yakın."

    s2 = ""
    s2_bits: list[str] = []
    if persona:
        s2_bits.append(f"{persona.lower()} tarzını tercih edenler için")
    if ortam:
        s2_bits.append(f"{ortam.lower()} ortamlara uygun")
    if s2_bits:
        s2 = (" ve ".join(s2_bits)).capitalize() + ", konforu ve şıklığı bir arada sunuyor."

    s3 = ""
    puan = puanlama.get("puan") or 0
    yorum_n = puanlama.get("yorumSayisi") or 0
    if puan and yorum_n >= 30:
        pct = int(round(float(puan) * 20))
        s3 = f"{yorum_n:,} kullanıcı yorumunda ortalama {float(puan):.1f}/5 puan ile %{pct} memnuniyet sağlamış.".replace(",", ".")

    return " ".join(s for s in [s1, s2, s3] if s).strip()

def _build_gallery(item: dict, slug: str) -> list[dict]:
    images = item.get("gorseller") or []
    ph_idx = (abs(hash(slug)) % PH_BG_COUNT) + 1
    slides = []
    for i, img in enumerate(images[:6]):
        if isinstance(img, str):
            url = img
        elif isinstance(img, dict):
            url = img.get("url") or img.get("contentUrl") or ""
        else:
            url = ""
        label = ["Ön", "Arka", "Detay", "Yan", "Model", "Kutu"][i] if i < 6 else f"Görsel {i+1}"
        slides.append({
            "bg": f"ph-bg-{ph_idx}",
            "label": label,
            "imageUrl": url if url.startswith("http") else None,
        })
    if not slides:
        slides.append({"bg": f"ph-bg-{ph_idx}", "label": "Ürün", "imageUrl": None})
    return slides

def normalize_product(item: dict, filename: str) -> dict | None:
    url = item.get("url", "")
    slug = _slug(url, filename)
    if not slug:
        return None

    ürün_bilgi = item.get("ürünBilgileri") or {}
    özellikler: dict = ürün_bilgi.get("özellikler") or {}
    açıklama = ürün_bilgi.get("açıklama") or ""
    puanlama = item.get("puanlama") or {}
    kategori: list[str] = item.get("kategori") or []

    price = float(item.get("fiyat") or 0)
    old_price = round(price * rng_global.uniform(1.20, 1.45), 2)
    disc = int(round((old_price - price) / old_price * 100))

    review_count = puanlama.get("yorumSayisi") or len(item.get("değerlendirmeler") or [])

    rating_voters = int(puanlama.get("puanSayisi") or 0)
    if rating_voters >= 1000:
        sales_str = f"{rating_voters // 1000}.{(rating_voters % 1000) // 100}k oy" if rating_voters % 1000 else f"{rating_voters // 1000}k oy"
    elif rating_voters >= 100:
        sales_str = f"{rating_voters} oy"
    else:
        sales_str = ""

    raw_rating = float(puanlama.get("puan") or 4.0)
    rating = round(max(1.0, min(5.0, raw_rating)), 1)

    sizes = _parse_sizes(item)
    colors = _parse_colors(item)
    gallery = _build_gallery(item, slug)
    care = _parse_care(özellikler)
    specs = _parse_specs(özellikler)
    description = _parse_description(açıklama)

    audience = []
    if özellikler.get("Persona"):
        audience = [p.strip() for p in str(özellikler["Persona"]).split(",")]
    occasions = []
    if özellikler.get("Ortam"):
        occasions = [o.strip() for o in str(özellikler["Ortam"]).split(",")]

    cat_links = [{"label": c, "href": f"/kategori/{c.lower().replace(' ', '-')}"} for c in kategori[1:]]

    summary = _build_summary(item, kategori, özellikler, puanlama)

    kalip = özellikler.get("Kalıp") or özellikler.get("Kumaş Tipi") or ""
    renk_str = colors[0]["name"] if colors else ""
    placeholder = f"{item.get('ürünAdı', '')[:30]} · {kalip} · {renk_str}".strip(" ·")

    return {
        "slug": slug,
        "brand": item.get("marka") or "",
        "title": item.get("ürünAdı") or "",
        "category": cat_links,
        "categoryKey": _cat_key(kategori),
        "rating": rating,
        "reviewCount": review_count,
        "salesCount": sales_str,
        "price": price,
        "oldPrice": old_price,
        "discountPercent": disc,
        "risk": {
            "level": "low",
            "percent": 0,
            "levelLabel": "Düşük",
            "reviewCount": review_count,
            "satisfaction": 85,
            "bars": [],
        },
        "colors": colors,
        "defaultColorIndex": 0,
        "sizes": sizes,
        "defaultSizeIndex": 0,
        "adviceBySize": {},
        "gallery": gallery,
        "summary": summary,
        "audience": audience,
        "occasions": occasions,
        "description": description,
        "care": care,
        "specs": specs,
        "reviews": [],
        "reviewCounts": {"all": review_count, "positive": 0, "negative": 0, "matchedToMe": 0},
        "qa": [],
        "qaMeta": {"total": 0, "avgResponse": ""},
        "similar": [],
        "bg": f"ph-bg-{(abs(hash(slug)) % PH_BG_COUNT) + 1}",
        "placeholder": placeholder,
        "imageUrl": (gallery[0].get("imageUrl") if gallery else None),
    }

def normalize_reviews(item: dict, slug: str) -> list[dict]:
    rows = []
    for rev in item.get("değerlendirmeler") or []:
        text = str(rev.get("text") or "").strip()
        if len(text) < 5:
            continue

        boy_raw = str(rev.get("boy") or "").strip()
        kilo_raw = str(rev.get("kilo") or "").strip()

        boy: int | None = None
        kilo: int | None = None
        m = re.search(r"\d+", boy_raw)
        if m:
            boy = int(m.group())
        m = re.search(r"\d+", kilo_raw)
        if m:
            kilo = int(m.group())

        boy_bin = (boy // 5) * 5 if boy else None
        kilo_bin = (kilo // 10) * 10 if kilo else None

        rid = hashlib.md5(f"{slug}|{text[:50]}|{rev.get('tarih','')}".encode()).hexdigest()[:16]

        rows.append({
            "id": rid,
            "urun_slug": slug,
            "yorum_metni": text,
            "beden": str(rev.get("beden") or ""),
            "boy": boy,
            "kilo": kilo,
            "boy_bin": boy_bin,
            "kilo_bin": kilo_bin,
            "tarih": str(rev.get("tarih") or ""),
            "kullanici": str(rev.get("kullanici") or ""),
            "satici": str(rev.get("satici") or ""),
        })
    return rows

def normalize_qa(item: dict, slug: str) -> list[dict]:
    rows = []
    for qa in item.get("soruCevaplar") or []:
        soru = str(qa.get("soru") or "").strip()
        cevap = str(qa.get("cevap") or "").strip()
        if not soru or not cevap:
            continue
        rows.append({
            "urun_slug": slug,
            "soru": soru,
            "cevap": cevap,
            "satici": str(qa.get("satici") or ""),
            "soru_tarihi": str(qa.get("soruTarihi") or ""),
            "cevap_bilgi": str(qa.get("cevapBilgi") or ""),
        })
    return rows

def main():
    raw_files = sorted(RAW_DIR.glob("trendyol_*.json"))
    log.info(f"{len(raw_files)} ham dosya bulundu")

    products: list[dict] = []
    all_reviews: list[dict] = []
    all_qa: list[dict] = []
    skipped = 0

    for fpath in tqdm(raw_files, desc="ETL"):
        try:
            with open(fpath, encoding="utf-8") as f:
                item = json.load(f)
        except Exception as e:
            log.warning(f"Okuma hatası {fpath.name}: {e}")
            skipped += 1
            continue

        if "error" in item and len(item) <= 3:
            skipped += 1
            continue

        prod = normalize_product(item, fpath.name)
        if not prod:
            skipped += 1
            continue

        slug = prod["slug"]
        products.append(prod)
        all_reviews.extend(normalize_reviews(item, slug))
        all_qa.extend(normalize_qa(item, slug))

    by_slug: dict[str, dict] = {}
    for p in products:
        s = p["slug"]
        if s not in by_slug or p["reviewCount"] > by_slug[s]["reviewCount"]:
            by_slug[s] = p
    dedup_count = len(products) - len(by_slug)
    products = list(by_slug.values())

    log.info(f"{len(products)} ürün normalize edildi (dedup: {dedup_count}), {skipped} atlandı")
    log.info(f"{len(all_reviews):,} yorum, {len(all_qa):,} Q&A")

    products_path = OUT_DIR / "products.json"
    with open(products_path, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    log.info(f"Yazıldı: {products_path}")

    reviews_df = pd.DataFrame(all_reviews)
    reviews_path = OUT_DIR / "reviews.parquet"
    reviews_df.to_parquet(reviews_path, index=False)
    log.info(f"Yazıldı: {reviews_path} ({len(reviews_df):,} satır)")

    qa_df = pd.DataFrame(all_qa)
    qa_path = OUT_DIR / "qa.parquet"
    qa_df.to_parquet(qa_path, index=False)
    log.info(f"Yazıldı: {qa_path} ({len(qa_df):,} satır)")

    print(f"\n{'='*50}")
    print(f"Ürün sayısı       : {len(products)}")
    print(f"Toplam yorum      : {len(all_reviews):,}")
    print(f"Boy dolu yorumlar : {reviews_df['boy'].notna().sum():,} (%{reviews_df['boy'].notna().mean()*100:.1f})")
    print(f"Kilo dolu         : {reviews_df['kilo'].notna().sum():,} (%{reviews_df['kilo'].notna().mean()*100:.1f})")
    print(f"Toplam Q&A        : {len(all_qa):,}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
