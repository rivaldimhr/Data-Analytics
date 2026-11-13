"""Buka dashboard hasil build, kumpulkan error console, dan ambil screenshot."""
import sys
from playwright.sync_api import sync_playwright

url, out = sys.argv[1], sys.argv[2]
errors = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.on("console", lambda m: m.type == "error" and errors.append(f"console: {m.text}"))
    pg.goto(url, wait_until="networkidle")
    pg.wait_for_timeout(4000)
    pg.screenshot(path=f"{out}/hero.png")
    # gulir pelan agar semua section (fade-in) muncul
    h = pg.evaluate("document.body.scrollHeight")
    for y in range(0, h, 600):
        pg.evaluate(f"window.scrollTo(0,{y})"); pg.wait_for_timeout(150)
    pg.wait_for_timeout(1500)
    pg.screenshot(path=f"{out}/full.png", full_page=True)
    charts = pg.evaluate("[...document.querySelectorAll('.js-plotly-plot')].length")
    # potret tiap bagian baru untuk README
    for sel, name in [("#peta", "peta"), ("#model-compare", "model-compare"), ("#kualitas-data", "kualitas-data")]:
        el = pg.locator(sel)
        el.scroll_into_view_if_needed(); pg.wait_for_timeout(800)
        el.screenshot(path=f"{out}/{name}.png")
    pg.select_option("#f-tipe", "TN"); pg.wait_for_timeout(800)
    pg.locator("#overview-chart").scroll_into_view_if_needed(); pg.wait_for_timeout(500)
    pg.screenshot(path=f"{out}/filter-tn.png")
    pg.select_option("#f-tipe", "all")
    m = b.new_page(viewport={"width": 390, "height": 844})
    m.goto(url, wait_until="networkidle"); m.wait_for_timeout(3000)
    m.screenshot(path=f"{out}/mobile.png")
    b.close()
print("plotly charts rendered:", charts)
print("\n".join(errors) or "no errors")
