"""
07 — Skor kualitas data pelaporan per kawasan wisata alam.

Temuan utama proyek: angka kunjungan lebih mencerminkan siapa yang rajin melapor daripada siapa yang berkunjung.
Skrip ini membuat skor sederhana yang bisa dicek ulang per kawasan.

Aturan skor (0–100):
  - Tahun yang dinilai: 2016–2022, KECUALI 2020 (data 2020 identik dengan 2019, ditandai SUSPECT_COPY) = 6 tahun.
  - kelengkapan = tahun dengan pengunjung > 0 / 6. Kawasan yang tidak tercantum di suatu tahun dihitung tidak melapor,
    karena nama yang hilang dari daftar juga berarti tidak ada laporan.
  - skor = round(100 * kelengkapan), dikurangi 10 bila nama kawasan mirip kawasan lain (kemungkinan tercatat ganda).
  - Kategori: Baik (≥ 50), Sedang (25–49), Buruk (1–24), Tidak pernah melapor (tidak ada tahun dengan pengunjung).

Keluaran: outputs/model_results/data_quality.csv
"""
from pathlib import Path
import re

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/clean/dishut_clean_v2.csv"
OUT = ROOT / "outputs/model_results/data_quality.csv"
EXCLUDED_YEAR = 2020
YEARS = [y for y in range(2016, 2023) if y != EXCLUDED_YEAR]

d = pd.read_csv(SRC)
per_year = (d.groupby(["pengelola_kawasan", "tipe_pengelola", "tahun"], as_index=False)
              .agg(total=("jumlah_wisatawan", "sum")))

# Data 2020 disalin dari 2019?
pivot = per_year.pivot_table(index="pengelola_kawasan", columns="tahun", values="total")
copied_2020 = (pivot.get(2019) == pivot.get(2020)) & pivot.get(2019).notna() & (pivot.get(2019) > 0)

# Kemungkinan nama ganda: samakan nama setelah membuang awalan pengelola & tanda baca
PREFIX = r"^(BALAI BESAR|BALAI|TWA|WH|BUPER|TN|TAHURA|BP|TB|LHI)\b\.?\s*"
def norm(name):
    n = name.upper()
    for _ in range(3):
        n = re.sub(PREFIX, "", n).strip()
    n = re.sub(r"\b(GN|GUNUNG)\b\.?", "GUNUNG", n)
    return re.sub(r"[^A-Z]", "", n)

names = pd.Series(d.pengelola_kawasan.unique())
keys = names.map(norm)
dup_groups = names.groupby(keys).apply(list)
dup_map = {n: g for g in dup_groups if len(g) > 1 for n in g}

rows = []
for (kawasan, tipe), g in per_year.groupby(["pengelola_kawasan", "tipe_pengelola"]):
    scored = g[g.tahun != EXCLUDED_YEAR]
    years_visit = sorted(scored.loc[scored.total > 0, "tahun"].tolist())
    completeness = len(years_visit) / len(YEARS)
    dup = [n for n in dup_map.get(kawasan, []) if n != kawasan]
    score = max(0, round(100 * completeness) - (10 if dup else 0))
    if not years_visit:
        cat = "Tidak pernah melapor"
    elif score >= 50:
        cat = "Baik"
    elif score >= 25:
        cat = "Sedang"
    else:
        cat = "Buruk"
    rows.append({
        "kawasan": kawasan,
        "tipe_pengelola": tipe,
        "tahun_tercantum": int(scored.tahun.nunique()),
        "tahun_ada_pengunjung": len(years_visit),
        "daftar_tahun_ada_pengunjung": " ".join(map(str, years_visit)),
        "total_pengunjung_2016_2022": int(g.total.sum() - g.loc[g.tahun == EXCLUDED_YEAR, "total"].sum()),
        "data_2020_sama_dengan_2019": bool(copied_2020.get(kawasan, False)),
        "kemungkinan_nama_ganda": "; ".join(dup),
        "skor_kualitas": score,
        "kategori": cat,
    })

out = pd.DataFrame(rows).sort_values(["skor_kualitas", "total_pengunjung_2016_2022"], ascending=False)
OUT.parent.mkdir(parents=True, exist_ok=True)
out.to_csv(OUT, index=False)

print(f"{len(out)} kawasan dinilai")
print(out.kategori.value_counts().to_string())
print("Data 2020 identik dengan 2019:", int(out.data_2020_sama_dengan_2019.sum()), "kawasan (dengan pengunjung > 0)")
print("Kemungkinan nama ganda:", int((out.kemungkinan_nama_ganda != "").sum()), "kawasan")
print(out[out.kemungkinan_nama_ganda != ""][["kawasan", "kemungkinan_nama_ganda"]].to_string(index=False))
