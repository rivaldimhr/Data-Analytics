"""Susun situs statis (folder site/) dari dashboard + data yang dibutuhkannya.

Dashboard di repo membaca CSV lewat path relatif ../data/... dan ../outputs/...;
di situs semua CSV ditaruh di site/data/ supaya path-nya pendek dan bisa diunduh.

  python scripts/build_site.py [folder_tujuan] [--pdf]
"""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = [
    "data/clean/dishut_clean_v2.csv",
    "data/processed/hotel_clean.csv",
    "data/preprocessed/hotel_tpk_predicted.csv",
    "data/reference/koordinat_kawasan.csv",
    "outputs/model_results/wisata_alam_clustered.csv",
    "outputs/model_results/model_comparison.csv",
    "outputs/model_results/forecast_2025_models.csv",
    "outputs/model_results/data_quality.csv",
]
PREFIXES = ["../data/clean/", "../data/processed/", "../data/preprocessed/", "../data/reference/", "../outputs/model_results/"]


def build(dest: Path, pdf: bool = False, browser=None) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "data").mkdir(parents=True)
    html = (ROOT / "dashboard/dashboard.html").read_text(encoding="utf-8")
    for p in PREFIXES:
        html = html.replace(p, "data/")
    (dest / "index.html").write_text(html, encoding="utf-8")
    for f in FILES:
        shutil.copy(ROOT / f, dest / "data" / Path(f).name)
    brief = ROOT / "outputs/reports/ringkasan-kebijakan.html"
    shutil.copy(brief, dest / "ringkasan-kebijakan.html")
    (dest / ".nojekyll").touch()
    if pdf:
        def _pdf(b):
            page = b.new_page()
            page.goto(brief.resolve().as_uri())
            page.pdf(path=str(dest / "ringkasan-kebijakan.pdf"), format="A4", print_background=True)
            page.close()
        if browser is not None:
            _pdf(browser)
        else:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                b = p.chromium.launch()
                _pdf(b)
                b.close()
    return dest


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = build(Path(args[0]) if args else ROOT / "site", pdf="--pdf" in sys.argv)
    print(f"Situs disusun di {out}")
