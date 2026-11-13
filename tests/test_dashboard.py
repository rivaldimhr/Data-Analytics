"""Test dashboard di browser (Playwright).

Dashboard memakai Plotly, PapaParse, dan Tailwind dari CDN, jadi test ini butuh internet.
Jika pustaka itu tidak bisa dimuat (mis. di komputer tanpa internet), test dilewati, bukan gagal.
"""
import functools
import os
import http.server
import threading

import pandas as pd
import pytest

from build_site import ROOT, build

pw = pytest.importorskip("playwright.sync_api")

CHART_IDS = ["overview-chart", "explorer-chart", "top-10-chart", "yearly-total-chart", "dominasi-chart",
             "profil-wisatawan-chart", "hotel-trend-chart", "hotel-seasonal-chart", "forecast-chart",
             "map-chart", "model-mae-chart"]


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@pytest.fixture(scope="session")
def site_url(tmp_path_factory, browser):
    site = build(tmp_path_factory.mktemp("site") / "site", pdf=True, browser=browser)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(site)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/"
    srv.shutdown()


@pytest.fixture(scope="session")
def browser():
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def _open(browser, url, **ctx):
    context = browser.new_context(**ctx)
    page = context.new_page()
    page.errors = []
    page.on("pageerror", lambda e: page.errors.append(str(e)))
    page.goto(url, wait_until="networkidle")
    if not page.evaluate("typeof window.Plotly !== 'undefined' && typeof window.Papa !== 'undefined'"):
        context.close()
        msg = "Pustaka CDN (Plotly/PapaParse) tidak bisa dimuat; butuh internet"
        if os.environ.get("REQUIRE_CDN"):
            pytest.fail(msg)
        pytest.skip(msg)
    page.wait_for_function("document.querySelectorAll('.js-plotly-plot').length >= 11", timeout=20000)
    page.wait_for_function("document.querySelectorAll('#dq-table tbody tr').length > 0", timeout=20000)
    return context, page


@pytest.fixture
def page(browser, site_url):
    context, pg = _open(browser, site_url, viewport={"width": 1280, "height": 900})
    yield pg
    errors = pg.errors
    context.close()
    assert not errors, f"Error JavaScript: {errors}"


@pytest.fixture(scope="module")
def dishut():
    return pd.read_csv(ROOT / "data/clean/dishut_clean_v2.csv")


def _top(df):
    return df.groupby("pengelola_kawasan").jumlah_wisatawan.sum().sort_values(ascending=False)


def _pct(a, b):
    return f"{a / b * 100:.1f}%"


def test_semua_grafik_tampil(page):
    for cid in CHART_IDS:
        assert page.locator(f"#{cid}.js-plotly-plot").count() == 1, f"Grafik {cid} tidak tampil"


def test_angka_kunci_dihitung_dari_data(page, dishut):
    top = _top(dishut)
    total = top.sum()
    assert page.text_content("#stat-top1-share") == _pct(top.iloc[0], total)
    assert page.text_content("#stat-top5-share") == _pct(top.iloc[:5].sum(), total)
    assert page.text_content("#stat-zero") == str((top == 0).sum())
    for el in page.locator('[data-stat="kawasan"]').all():
        assert el.text_content() == str(dishut.pengelola_kawasan.nunique())


def _overview_total(page):
    return page.evaluate("document.getElementById('overview-chart').data.slice(0,2).reduce((a,t)=>a+t.y.reduce((x,y)=>x+y,0),0)")


def test_filter_tipe_pengelola_mengubah_grafik_dan_angka(page, dishut):
    page.select_option("#f-tipe", "TN")
    tn = dishut[dishut.tipe_pengelola == "TN"]
    top = _top(tn)
    assert _overview_total(page) == tn.jumlah_wisatawan.sum()
    assert page.text_content("#stat-top1-share") == _pct(top.iloc[0], top.sum())
    assert "Filter aktif" in page.text_content("#f-summary")
    bars = page.evaluate("document.getElementById('top-10-chart').data[0].y")
    assert set(bars) <= set(tn.pengelola_kawasan)


def test_filter_tahun_dan_tanpa_2020(page, dishut):
    page.select_option("#f-from", "2017")
    page.select_option("#f-to", "2021")
    page.uncheck("#f-2020")
    x = page.evaluate("document.getElementById('overview-chart').data[0].x")
    assert x == [2017, 2018, 2019, 2021]
    exp = dishut[dishut.tahun.isin([2017, 2018, 2019, 2021])].jumlah_wisatawan.sum()
    assert _overview_total(page) == exp


def test_reset_filter_mengembalikan_semua_data(page, dishut):
    page.select_option("#f-tipe", "TWA")
    page.click("#f-reset")
    assert _overview_total(page) == dishut.jumlah_wisatawan.sum()
    assert "seluruh data" in page.text_content("#f-summary")


def test_tabel_perbandingan_model(page):
    m = pd.read_csv(ROOT / "outputs/model_results/model_comparison.csv")
    rows = page.locator("#model-table tbody tr")
    assert rows.count() == len(m)
    assert m.model.iloc[0] in rows.first.text_content()
    assert "lebih kecil" in page.text_content("#model-compare-text")


def test_peta_menampilkan_kawasan_berkoordinat(page):
    k = pd.read_csv(ROOT / "data/reference/koordinat_kawasan.csv")
    n = page.evaluate("document.getElementById('map-chart').data.reduce((a,t)=>a+t.lat.length,0)")
    assert n == len(k)
    assert f"{len(k)} dari" in page.text_content("#map-note")


def test_kualitas_data_kartu_cari_dan_unduh(page):
    q = pd.read_csv(ROOT / "outputs/model_results/data_quality.csv").fillna({"kemungkinan_nama_ganda": ""})
    for cat, n in q.kategori.value_counts().items():
        assert page.text_content(f'[data-dq-cat="{cat}"]') == str(n)
    page.check("#dq-dup-only")
    assert page.locator("#dq-table tbody tr").count() == min(25, (q.kemungkinan_nama_ganda != "").sum())
    page.uncheck("#dq-dup-only")
    page.fill("#dq-search", "gede")
    assert page.locator("#dq-table tbody tr").count() == q.kawasan.str.contains("GEDE").sum()
    page.fill("#dq-search", "")
    page.click("#dq-more")
    assert page.locator("#dq-table tbody tr").count() == len(q)
    href = page.get_attribute("#dq-download", "href")
    assert page.request.get(page.url + href).ok


def test_ringkasan_pdf_bisa_diunduh(page):
    resp = page.request.get(page.url + "ringkasan-kebijakan.pdf")
    assert resp.ok and resp.body()[:4] == b"%PDF"


def test_tampilan_ponsel_tanpa_gulir_horizontal(browser, site_url):
    context, pg = _open(browser, site_url, viewport={"width": 390, "height": 844})
    overflow = pg.evaluate("document.documentElement.scrollWidth - document.documentElement.clientWidth")
    context.close()
    assert overflow <= 1, f"Halaman melebar {overflow}px di layar 390px"
