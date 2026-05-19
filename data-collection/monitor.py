from __future__ import annotations

import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL_LIST = ROOT / "kiyafetler.txt"
RAW_DIR = ROOT / "data" / "raw"
LOG_FILE = ROOT / "logs" / "full_scrape.log"

def _count_urls(p: Path) -> int:
    if not p.exists():
        return 0
    return sum(
        1 for ln in p.read_text(encoding="utf-8").splitlines()
        if "trendyol.com" in ln and not ln.strip().startswith("#")
    )

def _list_files(p: Path):
    return sorted(p.glob("trendyol_*.json")) if p.exists() else []

def _classify_files(files):
    ok, errs = [], []
    for f in files:
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            if d.get("error"):
                errs.append((f, d))
            else:
                ok.append((f, d))
        except Exception:
            errs.append((f, {"error": "parse failed"}))
    return ok, errs

def _scrape_durations_from_log(log_path: Path):
    if not log_path.exists():
        return []
    text = log_path.read_text(encoding="utf-8", errors="ignore")

    return text.splitlines()

def main():
    total = _count_urls(URL_LIST)
    files = _list_files(RAW_DIR)
    ok, errs = _classify_files(files)
    n_ok, n_err = len(ok), len(errs)
    n_total = total or "?"

    pct = (100 * (n_ok + n_err) / total) if total else 0

    print("=" * 70)
    print(f"📊 Trendyol scrape — {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 70)
    print(f"İlerleme : {n_ok + n_err} / {n_total}  ({pct:.1f}%)")
    print(f"Başarılı : {n_ok}")
    print(f"Hatalı   : {n_err}")
    print(f"Klasör   : {RAW_DIR.relative_to(ROOT)}")

    if files:
        total_bytes = sum(f.stat().st_size for f in files)
        print(f"Toplam   : {total_bytes / 1024 / 1024:.1f} MB ({total_bytes // max(1,len(files)) // 1024} KB ort./ürün)")

    if ok:
        print("\n📦 Son 5 ürün:")
        for f, d in ok[-5:]:
            n = (d.get("ürünAdı") or "?")[:55]
            yrm = len(d.get("değerlendirmeler") or [])
            qa = len(d.get("soruCevaplar") or [])
            print(f"   • {n:<55}  yorum={yrm:>4}  qa={qa:>3}")

    if errs:
        print("\n⚠️  Hatalı dosyalar:")
        for f, d in errs[-3:]:
            print(f"   • {f.name} — {d.get('error', '?')}")

    if LOG_FILE.exists() and (n_ok + n_err) > 0 and total:
        first_t = files[0].stat().st_mtime
        last_t = files[-1].stat().st_mtime if files else time.time()
        elapsed = last_t - first_t
        done = n_ok + n_err
        if done > 1:
            avg = elapsed / done
            remaining = total - done
            eta = timedelta(seconds=int(avg * remaining))
            print(f"\n⏱  Ortalama: {avg:.1f}sn/ürün · ETA: {eta} ({remaining} ürün kaldı)")

    if LOG_FILE.exists():
        print("\n📜 Log son 5 satır:")
        lines = LOG_FILE.read_text(encoding="utf-8", errors="ignore").splitlines()
        for ln in lines[-5:]:
            print(f"   {ln}")
    else:
        print(f"\n⚠️  Log dosyası henüz yok: {LOG_FILE}")

if __name__ == "__main__":
    main()
