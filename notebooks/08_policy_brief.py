"""
08 — Ringkasan kebijakan satu halaman (HTML siap cetak A4; CI mengubahnya menjadi PDF).

Semua angka dihitung ulang dari data di sini, jadi ringkasan tidak bisa berbeda dengan dashboard.
Jalankan setelah 06_model_comparison.py dan 07_data_quality.py.

Keluaran: outputs/reports/ringkasan-kebijakan.html
"""
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/reports/ringkasan-kebijakan.html"
BULAN = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]


def pct(x, d=1):
    return f"{x:.{d}f}".replace(".", ",") + "%"


def pretty(name):
    """Nama kawasan dari data (huruf kapital, singkatan beragam) menjadi enak dibaca."""
    import re
    n = re.sub(r"\bTN\.?\s*GN\.?\s*", "TN Gunung ", name.upper())
    n = re.sub(r"\bGN\.\s*", "Gunung ", n)
    n = n.replace("GEDEPANGRANGO", "GEDE PANGRANGO").replace("HALIMUN-SALAK", "HALIMUN SALAK")
    n = n.title()
    for a, b in [("Twa ", "TWA "), ("Tn ", "TN "), ("Tahura ", "Tahura "), ("Ir. H.", "Ir. H.")]:
        n = n.replace(a, b)
    return n


def num(x):
    return f"{x:,.0f}".replace(",", ".")


# --- wisata alam ---
d = pd.read_csv(ROOT / "data/clean/dishut_clean_v2.csv")
total = d.jumlah_wisatawan.sum()
by_k = d.groupby("pengelola_kawasan").jumlah_wisatawan.sum().sort_values(ascending=False)
top1_name, top1 = by_k.index[0], by_k.iloc[0]
top5 = by_k.iloc[:5].sum()
wisman = d.loc[d.jenis_wisatawan == "WISATAWAN MANCANEGARA", "jumlah_wisatawan"].sum()

# --- kualitas data ---
q = pd.read_csv(ROOT / "outputs/model_results/data_quality.csv").fillna({"kemungkinan_nama_ganda": ""})
n_kawasan = len(q)
cats = ["Baik", "Sedang", "Buruk", "Tidak pernah melapor"]
cat_n = {c: int((q.kategori == c).sum()) for c in cats}
copied = int(q.data_2020_sama_dengan_2019.sum())
dups = q[q.kemungkinan_nama_ganda != ""]
groups = {"|".join(sorted([r.kawasan, *r.kemungkinan_nama_ganda.split("; ")])) for r in dups.itertuples()}

# --- kelompok kawasan ---
cl = pd.read_csv(ROOT / "outputs/model_results/wisata_alam_clustered.csv")
hidden = cl[cl.cluster == 3].sort_values("avg_pengunjung", ascending=False)
tw = d[d.pengelola_kawasan == "TWA TELAGAWARNA"].groupby("jenis_wisatawan").jumlah_wisatawan.sum()
tw_share = tw.get("WISATAWAN MANCANEGARA", 0) / tw.sum() * 100

# --- hotel ---
h = pd.read_csv(ROOT / "data/processed/hotel_clean.csv")
star = h[h.jenis_hotel == "1. Hotel Berbintang Total"].groupby("tahun").tpk.mean()
# Sama dengan dashboard: TPK gabungan yang kosong diisi rata-rata hotel berbintang & non-bintang bulan itu
t = h[h.jenis_hotel.str.match(r"^[123]\. ")].pivot_table(index=["tahun", "bulan"], columns="jenis_hotel", values="tpk", aggfunc="first")
gab = t["3. Hotel Berbintang dan NonBintang Total"].fillna(
    ((t["1. Hotel Berbintang Total"] + t["2. Hotel NonBintang Total"]) / 2).round(1))
month = gab.groupby(level="bulan").mean()
peak, low = month.idxmax(), month.idxmin()
m = pd.read_csv(ROOT / "outputs/model_results/model_comparison.csv")
best = m.iloc[0]
naive = m[m.model.str.startswith("Musiman naif")].iloc[0]
gain = (1 - best.MAE / naive.MAE) * 100

# --- grafik SVG: kualitas pelaporan 296 nama kawasan ---
colors = {"Baik": "#10B981", "Sedang": "#F59E0B", "Buruk": "#EF4444", "Tidak pernah melapor": "#94A3B8"}
W, x, bar = 640, 0, ""
for c in cats:
    w = cat_n[c] / n_kawasan * W
    bar += f'<rect x="{x:.1f}" y="0" width="{w:.1f}" height="34" fill="{colors[c]}"/>'
    if w > 40:
        bar += f'<text x="{x + w / 2:.1f}" y="22" text-anchor="middle" font-size="13" font-weight="700" fill="#fff">{cat_n[c]}</text>'
    x += w
legend = "".join(
    f'<span><i style="background:{colors[c]}"></i>{c} ({cat_n[c]})</span>' for c in cats)

html = f"""<!DOCTYPE html>
<html lang="id"><head><meta charset="utf-8">
<title>Ringkasan kebijakan: Pariwisata Alam Jawa Barat</title>
<style>
@page {{ size: A4; margin: 11mm 13mm; }}
* {{ box-sizing: border-box; }}
body {{ font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; color: #1e293b; margin: 0; font-size: 9.6pt; line-height: 1.38; }}
.page {{ max-width: 184mm; margin: 0 auto; }}
header {{ border-bottom: 3px solid #0C4A6E; padding-bottom: 8px; margin-bottom: 12px; }}
h1 {{ font-size: 17pt; margin: 0; color: #0C4A6E; }}
.sub {{ color: #64748b; font-size: 9.5pt; margin-top: 2px; }}
h2 {{ font-size: 11pt; margin: 10px 0 5px; color: #0C4A6E; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
ol {{ margin: 0; padding-left: 18px; }}
li {{ margin-bottom: 4px; }}
b {{ color: #0f172a; }}
.box {{ background: #f1f5f9; border-radius: 8px; padding: 10px 12px; }}
.rec li::marker {{ color: #0C4A6E; font-weight: 700; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 12px; font-size: 9pt; color: #475569; margin-top: 6px; }}
.legend i {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 4px; vertical-align: -1px; }}
footer {{ margin-top: 14px; border-top: 1px solid #cbd5e1; padding-top: 6px; font-size: 8.5pt; color: #64748b; }}
</style></head>
<body><div class="page">
<header>
  <h1>Pariwisata Alam Jawa Barat: Ringkasan untuk Pembuat Kebijakan</h1>
  <div class="sub">Data kunjungan {n_kawasan} nama kawasan wisata alam (2016–2022) dan hunian hotel (2019–2025) · Open Data Jawa Barat &amp; BPS</div>
</header>

<h2>Tiga temuan</h2>
<ol>
  <li><b>Angka kunjungan lebih mencerminkan kepatuhan melapor daripada jumlah pengunjung.</b>
      {cat_n["Tidak pernah melapor"]} dari {n_kawasan} nama kawasan ({pct(cat_n["Tidak pernah melapor"] / n_kawasan * 100, 0)}) tidak pernah mencatat satu pengunjung pun.
      Data 2020 di {copied} kawasan sama persis dengan 2019, dan {len(groups)} kawasan tercatat dengan beberapa nama berbeda ({len(dups)} nama).</li>
  <li><b>Kunjungan sangat terpusat.</b> {pretty(top1_name)} menyumbang {pct(top1 / total * 100)} dari {num(total)} kunjungan tercatat,
      dan 5 kawasan teratas {pct(top5 / total * 100)}. Wisatawan mancanegara hanya {pct(wisman / total * 100)}.</li>
  <li><b>Hotel belum pulih penuh dan sangat musiman.</b> Rata-rata hunian hotel berbintang turun dari {pct(star[2019])} (2019) ke {pct(star[2020])} (2020)
      dan baru {pct(star[2025])} pada 2025. Hunian tertinggi pada {peak} ({pct(month[peak])}), terendah pada {low} ({pct(month[low])}).
      Model prediksi hunian meleset rata-rata {str(round(best.MAE, 1)).replace(".", ",")} poin pada 2025, {gain:.0f}% lebih akurat daripada tebakan "bulan yang sama tahun lalu".</li>
</ol>

<h2>Kualitas pelaporan {n_kawasan} nama kawasan</h2>
<svg viewBox="0 0 {W} 34" width="100%" role="img" aria-label="Sebaran kategori kualitas data">{bar}</svg>
<div class="legend">{legend}</div>
<div class="sub" style="margin-top:4px">Skor = persentase tahun (tanpa 2020) yang mencatat pengunjung, dikurangi 10 bila nama terindikasi ganda. Baik ≥ 50, Sedang 25–49, Buruk 1–24.</div>

<h2>Tiga rekomendasi</h2>
<div class="cols">
  <ol class="rec">
    <li><b>Kode kawasan baku dan pelaporan digital bulanan.</b> Satu kode untuk tiap kawasan menghapus nama ganda; formulir daring dengan validasi
        (tidak boleh kosong, tidak boleh sama persis dengan tahun lalu) mencegah data disalin. Ukuran keberhasilan: kawasan kategori "Tidak pernah melapor" turun setiap tahun.</li>
    <li><b>Kembangkan kelompok "Potensi tersembunyi".</b> {len(hidden)} kawasan seperti {", ".join(pretty(n) for n in hidden.pengelola_kawasan.head(3))}
        cukup ramai saat melapor, tetapi jarang tercatat. Perbaiki pelaporannya dulu, lalu jadikan alternatif agar kunjungan tidak bertumpu pada satu kawasan.</li>
  </ol>
  <ol class="rec" start="3">
    <li><b>Atur promosi mengikuti musim dan ceruk internasional.</b> Dorong kunjungan pada bulan sepi (April–Mei) dengan paket wisata alam dan hotel.
        TWA Telagawarna mencatat {pct(tw_share)} wisatawan mancanegara, jauh di atas rata-rata; pelajari dan tiru pendekatannya di kawasan sejenis.</li>
  </ol>
</div>
<div class="box" style="margin-top:12px"><b>Keterbatasan.</b> Angka kunjungan bergantung pada laporan pengelola. TPK hotel 2022 hanya lengkap untuk hotel berbintang dan 2023 hanya 4 bulan.
  Lokasi pada peta di dashboard adalah perkiraan manual.</div>

<footer>Dashboard interaktif: rivaldimhr.github.io/jabar-tourism · Kode &amp; data: github.com/rivaldimhr/Data-Analytics ·
Tugas Besar II4013 Data Analitik ITB, Kelompok 12 · Dibuat otomatis dari data, {date.today():%d-%m-%Y}</footer>
</div></body></html>
"""
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html, encoding="utf-8")
print(f"Ringkasan ditulis ke {OUT.relative_to(ROOT)}")
print(f"Top1 {pct(top1 / total * 100)}, top5 {pct(top5 / total * 100)}, wisman {pct(wisman / total * 100)}, "
      f"puncak {peak}, terendah {low}, hotel bintang 2019/2020/2025 {star[2019]:.1f}/{star[2020]:.1f}/{star[2025]:.1f}")
