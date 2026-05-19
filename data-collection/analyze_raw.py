from __future__ import annotations

import argparse
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

CATEGORY_HINTS: List[Tuple[str, List[str]]] = [
    ("erkek_tisort", ["tisort", "t-shirt", "tshirt"]),
    ("erkek_gomlek", ["gomlek"]),
    ("erkek_pantolon", ["pantolon"]),
    ("erkek_sort", ["sort"]),
    ("erkek_kazak", ["kazak", "triko"]),
    ("erkek_mont", ["mont", "kaban", "ceket", "parka", "blazer", "palto", "trenckot"]),
    ("erkek_sweatshirt", ["sweatshirt", "hoodie"]),
    ("erkek_esofman", ["esofman", "jogger"]),
    ("ayakkabi", ["ayakkabi", "sneaker", "bot", "krampon", "loafer", "cizme", "sandalet"]),
    ("saat", ["saat"]),
    ("kadin_elbise", ["elbise", "abiye", "tunik"]),
    ("kadin_etek", ["etek"]),
    ("kadin_jean", ["jean", "denim"]),
    ("canta", ["canta"]),
    ("taki", ["kolye", "kupe", "bileklik", "yuzuk", "sahmeran", "sahmeran"]),
]

def _normalize_tr(s: str) -> str:
    s = s.lower()
    for tr, en in [("ı","i"), ("ü","u"), ("ö","o"), ("ş","s"), ("ç","c"),
                   ("ğ","g"), ("â","a"), ("î","i"), ("û","u")]:
        s = s.replace(tr, en)
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")

def guess_category(item: Dict[str, Any]) -> str:
    breadcrumb = item.get("kategori") or []
    marka = (item.get("marka") or "").strip().lower()
    GENDER_PREFIX = {"Erkek", "Kadın", "Unisex", "Bebek", "Çocuk"}

    if len(breadcrumb) >= 2:

        for level in reversed(breadcrumb[1:]):
            if not level:
                continue
            words = level.split()
            if not words or words[0] not in GENDER_PREFIX:
                continue

            if marka and marka in level.lower():
                continue
            return _normalize_tr(level)

        for level in reversed(breadcrumb):
            if marka and marka in level.lower():
                continue
            return _normalize_tr(level)

    url = (item.get("url") or "").lower()
    for cat, keywords in CATEGORY_HINTS:
        for k in keywords:
            if re.search(rf"\b{re.escape(k)}\b", url) or k in url:
                return cat
    return "diger"

def _is_filled(v: Any) -> bool:
    if v is None:
        return False
    if isinstance(v, (list, dict, str)) and len(v) == 0:
        return False
    return True

def field_coverage(items: List[Dict]) -> Dict[str, Dict[str, Any]]:
    coverage: Dict[str, Dict[str, int]] = defaultdict(lambda: {"dolu": 0, "bos": 0, "yok": 0})
    all_keys = set()
    for it in items:
        all_keys.update(it.keys())

    for it in items:
        for k in all_keys:
            if k not in it:
                coverage[k]["yok"] += 1
            elif _is_filled(it[k]):
                coverage[k]["dolu"] += 1
            else:
                coverage[k]["bos"] += 1

    total = len(items)
    out = {}
    for k, c in coverage.items():
        out[k] = {**c, "dolu_pct": round(100 * c["dolu"] / max(1, total), 1)}
    return out

def nested_coverage(items: List[Dict], path: List[str]) -> Dict[str, Any]:
    total = len(items)
    sub_keys: Counter = Counter()
    filled: Counter = Counter()
    for it in items:
        cur = it
        for p in path:
            cur = cur.get(p) if isinstance(cur, dict) else None
            if cur is None:
                break
        if isinstance(cur, dict):
            for k, v in cur.items():
                sub_keys[k] += 1
                if _is_filled(v):
                    filled[k] += 1
    return {
        "toplam_anahtar_sayisi": len(sub_keys),
        "anahtarlar": {
            k: {"goruldu": sub_keys[k], "dolu": filled[k], "dolu_pct": round(100 * filled[k] / max(1, sub_keys[k]), 1)}
            for k in sorted(sub_keys, key=lambda x: -sub_keys[x])
        },
    }

def _safe_int(v: Any) -> int | None:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None

def list_len_stats(items: List[Dict], key: str) -> Dict[str, Any]:
    lengths = []
    for it in items:
        v = it.get(key)
        if isinstance(v, list):
            lengths.append(len(v))
    if not lengths:
        return {"sayi": 0}
    return {
        "sayi": len(lengths),
        "min": min(lengths),
        "max": max(lengths),
        "ortalama": round(statistics.mean(lengths), 1),
        "medyan": statistics.median(lengths),
    }

def size_format_distribution(items: List[Dict]) -> Dict[str, int]:
    classes: Counter = Counter()
    PATTERNS = {
        "alfabetik": re.compile(r"^(XXS|XS|S|M|L|XL|2XL|3XL|4XL|5XL)$", re.I),
        "numara": re.compile(r"^\d{2,3}(/\d{2,3})?$"),
        "tek_beden": re.compile(r"^(Tek\s*Beden|Standart|Standard)$", re.I),
        "ayakkabi_numara": re.compile(r"^\d{2}([.,]\d)?$"),
    }
    for it in items:
        beden_list = it.get("bedenler") or []
        if not beden_list:
            classes["bedensiz"] += 1
            continue
        labels = [b.get("beden", "") if isinstance(b, dict) else str(b) for b in beden_list]
        matched = False
        for cname, pat in PATTERNS.items():
            if any(pat.match(lbl.strip()) for lbl in labels):
                classes[cname] += 1
                matched = True
                break
        if not matched:
            classes["diger"] += 1
    return dict(classes)

def review_attribute_distribution(items: List[Dict]) -> Dict[str, Any]:
    total_with_reviews = 0
    total_reviews = 0
    with_boy = 0
    with_kilo = 0
    with_beden = 0
    with_puan = 0
    for it in items:
        revs = it.get("değerlendirmeler") or []
        if revs:
            total_with_reviews += 1
        for r in revs:
            total_reviews += 1
            if r.get("boy"):
                with_boy += 1
            if r.get("kilo"):
                with_kilo += 1
            if r.get("beden"):
                with_beden += 1
            if r.get("puan") is not None:
                with_puan += 1
    return {
        "yorumlu_urun_sayisi": total_with_reviews,
        "toplam_yorum": total_reviews,
        "boy_orani": round(100 * with_boy / max(1, total_reviews), 1),
        "kilo_orani": round(100 * with_kilo / max(1, total_reviews), 1),
        "beden_orani": round(100 * with_beden / max(1, total_reviews), 1),
        "puan_orani": round(100 * with_puan / max(1, total_reviews), 1),
    }

def feature_key_frequency(items: List[Dict], top_n: int = 30) -> List[Tuple[str, int]]:
    c: Counter = Counter()
    for it in items:
        feats = (it.get("ürünBilgileri") or {}).get("özellikler") or {}
        if isinstance(feats, dict):
            for k in feats.keys():
                c[k] += 1
    return c.most_common(top_n)

def per_category_breakdown(items: List[Dict]) -> Dict[str, Dict[str, Any]]:
    by_cat: Dict[str, List[Dict]] = defaultdict(list)
    for it in items:
        by_cat[guess_category(it)].append(it)

    out = {}
    for cat, group in by_cat.items():
        feats: Counter = Counter()
        for it in group:
            feats.update((it.get("ürünBilgileri") or {}).get("özellikler", {}).keys())
        out[cat] = {
            "urun_sayisi": len(group),
            "ortalama_gorsel": round(statistics.mean([len(it.get("gorseller") or []) for it in group]) if group else 0, 1),
            "ortalama_yorum": round(statistics.mean([len(it.get("değerlendirmeler") or []) for it in group]) if group else 0, 1),
            "ortalama_qa": round(statistics.mean([len(it.get("soruCevaplar") or []) for it in group]) if group else 0, 1),
            "ortalama_varyant": round(statistics.mean([len(it.get("renkVaryantlari") or []) for it in group]) if group else 0, 1),
            "puanli_orani": round(100 * sum(1 for it in group if _is_filled(it.get("puanlama"))) / max(1, len(group)), 1),
            "marka_orani": round(100 * sum(1 for it in group if _is_filled(it.get("marka"))) / max(1, len(group)), 1),
            "kategori_orani": round(100 * sum(1 for it in group if _is_filled(it.get("kategori"))) / max(1, len(group)), 1),
            "rengi_orani": round(100 * sum(1 for it in group if _is_filled(it.get("rengi"))) / max(1, len(group)), 1),
            "bedensiz_sayisi": sum(1 for it in group if not (it.get("bedenler") or [])),
            "en_yaygin_5_ozellik": feats.most_common(5),
        }
    return out

def analyze(in_dir: Path) -> Dict[str, Any]:
    files = sorted(in_dir.glob("trendyol_*.json"))
    items = []
    error_files = []
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  okunamadı: {f.name} — {e!r}")
            continue

        if d.get("error"):
            error_files.append({"file": f.name, "url": d.get("url"), "error": d["error"]})
            continue
        items.append(d)
    return {
        "dosya_sayisi": len(files),
        "gecerli_urun": len(items),
        "hatali_dosya": error_files,
        "kapsam": field_coverage(items),
        "urunBilgileri": nested_coverage(items, ["ürünBilgileri"]),
        "puanlama": nested_coverage(items, ["puanlama"]),
        "gorsel_uzunluk": list_len_stats(items, "gorseller"),
        "yorum_uzunluk": list_len_stats(items, "değerlendirmeler"),
        "qa_uzunluk": list_len_stats(items, "soruCevaplar"),
        "varyant_uzunluk": list_len_stats(items, "renkVaryantlari"),
        "beden_formati": size_format_distribution(items),
        "yorum_attribute": review_attribute_distribution(items),
        "en_yaygin_ozellikler": feature_key_frequency(items, top_n=30),
        "kategori_bazli": per_category_breakdown(items),
    }

def render_markdown(report: Dict[str, Any]) -> str:
    out: List[str] = []
    out.append(
        f"# Raw Veri Analizi — {report['gecerli_urun']} geçerli ürün "
        f"({report['dosya_sayisi']} dosya, {len(report['hatali_dosya'])} hatalı)\n"
    )
    if report["hatali_dosya"]:
        out.append("## Hatalı dosyalar (JSON-LD bulunamadı)\n")
        for e in report["hatali_dosya"]:
            out.append(f"- `{e['file']}` — {e.get('url','?')}")
        out.append("")

    out.append("## 1. Üst-seviye alan kapsamı\n")
    out.append("| Alan | Dolu | Boş | Yok | Dolu % |")
    out.append("|---|---|---|---|---|")
    for k in sorted(report["kapsam"].keys(), key=lambda x: -report["kapsam"][x]["dolu"]):
        c = report["kapsam"][k]
        out.append(f"| `{k}` | {c['dolu']} | {c['bos']} | {c['yok']} | {c['dolu_pct']}% |")
    out.append("")

    out.append("## 2. Liste uzunluk istatistikleri\n")
    for k in ("gorsel_uzunluk", "yorum_uzunluk", "qa_uzunluk", "varyant_uzunluk"):
        s = report[k]
        if s.get("sayi"):
            out.append(
                f"- **{k}**: ürün={s['sayi']}, min={s['min']}, max={s['max']}, "
                f"ortalama={s['ortalama']}, medyan={s['medyan']}"
            )
    out.append("")

    out.append("## 3. Beden formatı dağılımı\n")
    for k, v in report["beden_formati"].items():
        out.append(f"- `{k}`: {v}")
    out.append("")

    out.append("## 4. Yorum profil dağılımı\n")
    ya = report["yorum_attribute"]
    out.append(f"- Yorumlu ürün: {ya['yorumlu_urun_sayisi']}")
    out.append(f"- Toplam yorum: {ya['toplam_yorum']}")
    out.append(f"- Boy bilgisi içeren yorum oranı: {ya['boy_orani']}%")
    out.append(f"- Kilo bilgisi içeren yorum oranı: {ya['kilo_orani']}%")
    out.append(f"- Beden bilgisi içeren yorum oranı: {ya['beden_orani']}%")
    out.append(f"- Yıldız (puan) içeren yorum oranı: {ya['puan_orani']}%")
    out.append("")

    out.append("## 5. `ürünBilgileri` alt-anahtarları\n")
    ui = report["urunBilgileri"]
    for k, v in ui["anahtarlar"].items():
        out.append(f"- `{k}`: görüldü={v['goruldu']}, dolu={v['dolu']} ({v['dolu_pct']}%)")
    out.append("")

    out.append("## 6. En yaygın `özellikler` key'leri\n")
    for k, n in report["en_yaygin_ozellikler"]:
        out.append(f"- `{k}` × {n}")
    out.append("")

    out.append("## 7. Kategori bazlı kıyas\n")
    out.append("| Kategori | N | Marka% | Kategori% | Renk% | Puanlı% | Ø Görsel | Ø Yorum | Ø Q&A | Ø Varyant | Bedensiz |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for cat, c in sorted(report["kategori_bazli"].items(), key=lambda x: -x[1]["urun_sayisi"]):
        out.append(
            f"| {cat} | {c['urun_sayisi']} | {c['marka_orani']}% | {c['kategori_orani']}% | "
            f"{c['rengi_orani']}% | {c['puanli_orani']}% | {c['ortalama_gorsel']} | "
            f"{c['ortalama_yorum']} | {c['ortalama_qa']} | {c['ortalama_varyant']} | {c['bedensiz_sayisi']} |"
        )
    out.append("")
    out.append("### Kategori başı en yaygın 5 özellik\n")
    for cat, c in sorted(report["kategori_bazli"].items()):
        keys = ", ".join(f"{k}({n})" for k, n in c["en_yaygin_5_ozellik"])
        out.append(f"- **{cat}**: {keys or '—'}")
    out.append("")

    return "\n".join(out)

def main():
    p = argparse.ArgumentParser(description="Raw scrape analizi")
    p.add_argument("--dir", type=Path, default=Path("data-collection/raw"))
    p.add_argument("--out", type=Path, default=Path("reports/raw_analysis.md"))
    p.add_argument("--json", type=Path, help="Ham analiz JSON çıktısı (opsiyonel)")
    args = p.parse_args()

    if not args.dir.exists():
        raise SystemExit(f"❌ Klasör yok: {args.dir}")

    report = analyze(args.dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(render_markdown(report), encoding="utf-8")
    print(f"✅ Markdown rapor: {args.out}")

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"✅ JSON rapor: {args.json}")

if __name__ == "__main__":
    main()
