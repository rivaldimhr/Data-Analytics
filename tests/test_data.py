"""Test data & hasil analisis: kolom wajib, nilai wajar, hasil bisa diulang, dan angka yang ditampilkan sesuai data."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DASH = (ROOT / "dashboard/dashboard.html").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dishut():
    return pd.read_csv(ROOT / "data/clean/dishut_clean_v2.csv")


REQUIRED = {
    "data/clean/dishut_clean_v2.csv": ["pengelola_kawasan", "jenis_wisatawan", "jumlah_wisatawan", "tahun", "data_flag", "tipe_pengelola"],
    "data/processed/hotel_clean.csv": ["tahun", "bulan", "jenis_hotel", "tpk"],
    "data/preprocessed/hotel_tpk_predicted.csv": ["tahun", "bulan_num", "tpk_aktual", "tpk_prediksi", "split"],
    "outputs/model_results/wisata_alam_clustered.csv": ["pengelola_kawasan", "tipe_pengelola", "avg_pengunjung", "years_active", "rasio_wisman", "cluster"],
    "outputs/model_results/model_comparison.csv": ["peringkat", "model", "MAE", "RMSE", "MAPE_%", "R2", "MAE_tanpa_Mar"],
    "outputs/model_results/data_quality.csv": ["kawasan", "tipe_pengelola", "skor_kualitas", "kategori", "data_2020_sama_dengan_2019", "kemungkinan_nama_ganda"],
    "data/reference/koordinat_kawasan.csv": ["pengelola_kawasan", "lat", "lon", "wilayah"],
}


@pytest.mark.parametrize("path,cols", REQUIRED.items(), ids=list(REQUIRED))
def test_kolom_wajib_ada(path, cols):
    df = pd.read_csv(ROOT / path)
    missing = [c for c in cols if c not in df.columns]
    assert not missing, f"{path} kehilangan kolom {missing}"
    assert len(df) > 0


def test_jumlah_wisatawan_tidak_negatif_dan_bulat(dishut):
    assert (dishut.jumlah_wisatawan >= 0).all()
    assert (dishut.jumlah_wisatawan % 1 == 0).all()
    assert dishut.tahun.between(2016, 2022).all()


def test_tpk_dalam_rentang_persen():
    h = pd.read_csv(ROOT / "data/processed/hotel_clean.csv")
    assert h.tpk.dropna().between(0, 100).all()
    p = pd.read_csv(ROOT / "data/preprocessed/hotel_tpk_predicted.csv")
    assert p.tpk_aktual.between(0, 100).all()
    assert set(p.split) == {"train", "test"}
    assert p.loc[p.split == "test", "tahun"].eq(2025).all(), "Data uji harus tahun 2025 saja"


@pytest.mark.parametrize("script,output", [
    ("notebooks/06_model_comparison.py", "outputs/model_results/model_comparison.csv"),
    ("notebooks/07_data_quality.py", "outputs/model_results/data_quality.csv"),
])
def test_skrip_menghasilkan_ulang_output_yang_sama(script, output):
    before = (ROOT / output).read_bytes()
    subprocess.run([sys.executable, str(ROOT / script)], check=True, capture_output=True)
    assert (ROOT / output).read_bytes() == before, f"Menjalankan ulang {script} mengubah {output}"


def test_regresi_sama_dengan_hasil_notebook_04():
    nb = json.loads((ROOT / "notebooks/04_model.ipynb").read_text(encoding="utf-8"))
    text = "".join("".join(o.get("text", [])) for c in nb["cells"] for o in c.get("outputs", []))
    mae_nb = float(re.search(r"MAE\s+\(test\):\s*([\d.]+)", text).group(1))
    m = pd.read_csv(ROOT / "outputs/model_results/model_comparison.csv")
    mae = m.loc[m.model.str.startswith("Regresi"), "MAE"].iloc[0]
    assert abs(mae - mae_nb) < 0.001


def test_peringkat_model_urut_berdasarkan_mae():
    m = pd.read_csv(ROOT / "outputs/model_results/model_comparison.csv")
    assert m.MAE.is_monotonic_increasing
    assert list(m.peringkat) == list(range(1, len(m) + 1))


def test_koordinat_berada_di_jawa_barat_dan_nama_cocok():
    k = pd.read_csv(ROOT / "data/reference/koordinat_kawasan.csv")
    c = pd.read_csv(ROOT / "outputs/model_results/wisata_alam_clustered.csv")
    assert k.lat.between(-7.9, -5.9).all() and k.lon.between(106.3, 108.9).all()
    assert not k.pengelola_kawasan.duplicated().any()
    unknown = set(k.pengelola_kawasan) - set(c.pengelola_kawasan)
    assert not unknown, f"Nama di file koordinat tidak ada di data kelompok: {unknown}"


def test_kualitas_data_konsisten_dengan_data_mentah(dishut):
    q = pd.read_csv(ROOT / "outputs/model_results/data_quality.csv")
    assert len(q) == dishut.pengelola_kawasan.nunique()
    assert q.skor_kualitas.between(0, 100).all()
    totals = dishut.groupby("pengelola_kawasan").jumlah_wisatawan.sum()
    assert (q.kategori == "Tidak pernah melapor").sum() == (totals == 0).sum()


def _share(a, b):
    return round(a / b * 100, 1)


def test_angka_tertulis_di_dashboard_sesuai_data(dishut):
    total = dishut.jumlah_wisatawan.sum()
    wisman = dishut.loc[dishut.jenis_wisatawan == "WISATAWAN MANCANEGARA", "jumlah_wisatawan"].sum()
    expected = [
        f"{_share(total - wisman, total)}%",            # porsi wisatawan nusantara di judul bagian 05
        f"{wisman:,}",                                  # jumlah wisman
        f"({_share(wisman, total)}%)",                  # porsi wisman
        f"{round(total / 1e6, 1)} juta",                # total kunjungan
    ]
    for text in expected:
        assert text in DASH, f"Dashboard tidak memuat angka yang benar: {text}"


def test_tidak_ada_angka_lama_yang_salah():
    # 75.6% dan "Lainnya (305)" pernah ditulis manual dan tidak cocok dengan data
    assert "75.6%" not in DASH
    assert "Lainnya (305)" not in DASH


def test_ringkasan_kebijakan_memakai_angka_dari_data(dishut):
    subprocess.run([sys.executable, str(ROOT / "notebooks/08_policy_brief.py")], check=True, capture_output=True)
    brief = (ROOT / "outputs/reports/ringkasan-kebijakan.html").read_text(encoding="utf-8")
    total = dishut.jumlah_wisatawan.sum()
    top = dishut.groupby("pengelola_kawasan").jumlah_wisatawan.sum().sort_values(ascending=False)
    assert f"{_share(top.iloc[0], total)}%".replace(".", ",") in brief
    assert f"{_share(top.iloc[:5].sum(), total)}%".replace(".", ",") in brief
    q = pd.read_csv(ROOT / "outputs/model_results/data_quality.csv")
    assert f"{(q.kategori == 'Tidak pernah melapor').sum()} dari {len(q)} nama kawasan" in brief
