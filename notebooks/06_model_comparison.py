"""
06 — Bandingkan model prediksi TPK hotel dengan baseline sederhana.

Pertanyaan: apakah regresi linear di 04_model lebih baik daripada tebakan sederhana?
Semua model dilatih pada 2019–2024 dan diuji pada 12 bulan 2025 (tanpa mengintip data 2025).

Keluaran:
  outputs/model_results/model_comparison.csv   metrik tiap model
  outputs/model_results/forecast_2025_models.csv  prediksi per bulan tiap model
Hanya butuh pandas + numpy.
"""
from pathlib import Path
import itertools

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/preprocessed/hotel_tpk_predicted.csv"
OUT = ROOT / "outputs/model_results"

df = pd.read_csv(SRC).sort_values(["tahun", "bulan_num"]).reset_index(drop=True)
train = df[df.split == "train"].reset_index(drop=True)
test = df[df.split == "test"].reset_index(drop=True)
y_train = train.tpk_aktual.to_numpy()
y_test = test.tpk_aktual.to_numpy()
H = len(test)
COVID_YEARS = {2020, 2021}


def holt_winters_additive(y, season=12, horizon=12, damped=False):
    """Holt-Winters aditif; parameter dipilih lewat grid search pada error satu-langkah di data latih.
    damped=True meredam tren (phi < 1) agar tidak terus naik/turun saat diproyeksikan."""
    best = None
    grid = np.round(np.arange(0.05, 1.0, 0.1), 2)
    phis = [0.8, 0.9, 0.95] if damped else [1.0]
    for a, b, g, phi in itertools.product(grid, [0.01, 0.05, 0.1, 0.2], grid, phis):
        level = y[:season].mean()
        trend = (y[season:2 * season].mean() - y[:season].mean()) / season if len(y) >= 2 * season else 0.0
        seas = list(y[:season] - level)
        sse = 0.0
        for t in range(season, len(y)):
            pred = level + phi * trend + seas[t - season]
            sse += (y[t] - pred) ** 2
            new_level = a * (y[t] - seas[t - season]) + (1 - a) * (level + phi * trend)
            trend = b * (new_level - level) + (1 - b) * phi * trend
            seas.append(g * (y[t] - new_level) + (1 - g) * seas[t - season])
            level = new_level
        if best is None or sse < best[0]:
            fc = [level + sum(phi ** i for i in range(1, h + 2)) * trend + seas[len(y) - season + (h % season)]
                  for h in range(horizon)]
            best = (sse, (a, b, g, phi), np.array(fc))
    return best[2], best[1]


preds = {}
notes = {}

# 1. Naif: semua bulan 2025 = nilai bulan terakhir yang diketahui (Des 2024)
preds["Naif (nilai bulan terakhir)"] = np.repeat(y_train[-1], H)
notes["Naif (nilai bulan terakhir)"] = "Semua bulan 2025 ditebak sama dengan Desember 2024."

# 2. Musiman naif: bulan yang sama tahun lalu
last_year = train[train.tahun == train.tahun.max()].set_index("bulan_num").tpk_aktual
preds["Musiman naif (bulan sama tahun lalu)"] = test.bulan_num.map(last_year).to_numpy()
notes["Musiman naif (bulan sama tahun lalu)"] = "Januari 2025 = Januari 2024, dan seterusnya."

# 3. Rata-rata bulan yang sama di tahun normal (tanpa 2020–2021)
normal = train[~train.tahun.isin(COVID_YEARS)].groupby("bulan_num").tpk_aktual.mean()
preds["Rata-rata bulan yang sama (tanpa masa COVID)"] = test.bulan_num.map(normal).to_numpy()
notes["Rata-rata bulan yang sama (tanpa masa COVID)"] = "Rata-rata tiap bulan pada 2019 dan 2022–2024."

# 4. Regresi linear dari 04_model (tren + sin/cos bulan + penanda COVID)
preds["Regresi linear + musim (04_model)"] = test.tpk_prediksi.to_numpy()
notes["Regresi linear + musim (04_model)"] = "Model awal proyek: tren tahun, pola bulan (sin/cos), penanda COVID."

# 5–6. Holt-Winters aditif, dilatih pada data setelah COVID (2022–2024).
# Catatan: sebagian besar TPK 2022–2023 di seri ini hasil interpolasi (data asli 2022 kosong, 2023 hanya 4 bulan),
# jadi model deret waktu murni belajar dari garis buatan. Hasilnya dilaporkan apa adanya.
post = train[~train.tahun.isin(COVID_YEARS | {2019})].tpk_aktual.to_numpy()
hw, params = holt_winters_additive(post, horizon=H)
preds["Holt-Winters (latih 2022–2024)"] = hw
notes["Holt-Winters (latih 2022–2024)"] = (f"Pemulusan eksponensial musiman; alpha={params[0]}, beta={params[1]}, gamma={params[2]}. "
                                          "Tren naik 2024 terbawa terus ke 2025.")
hwd, params = holt_winters_additive(post, horizon=H, damped=True)
preds["Holt-Winters tren diredam (latih 2022–2024)"] = hwd
notes["Holt-Winters tren diredam (latih 2022–2024)"] = (f"Sama, tetapi tren diredam (phi={params[3]}); "
                                                       f"alpha={params[0]}, beta={params[1]}, gamma={params[2]}.")


def metrics(y, p):
    err = y - p
    return {
        "MAE": np.mean(np.abs(err)),
        "RMSE": np.sqrt(np.mean(err ** 2)),
        "MAPE_%": np.mean(np.abs(err) / y) * 100,
        "R2": 1 - np.sum(err ** 2) / np.sum((y - y.mean()) ** 2),
    }


rows = [{"model": m, **metrics(y_test, p), "keterangan": notes[m]} for m, p in preds.items()]
res = pd.DataFrame(rows).sort_values("MAE").reset_index(drop=True)
res.insert(0, "peringkat", range(1, len(res) + 1))
res[["MAE", "RMSE", "MAPE_%", "R2"]] = res[["MAE", "RMSE", "MAPE_%", "R2"]].round(3)

# Analisis tambahan: Maret 2025 jatuh ke 24% (anomali). Berapa MAE tanpa bulan itu?
mask = ~((test.bulan_num == 3).to_numpy())
res["MAE_tanpa_Mar"] = [round(float(np.mean(np.abs(y_test[mask] - preds[m][mask]))), 3) for m in res.model]

OUT.mkdir(parents=True, exist_ok=True)
res.to_csv(OUT / "model_comparison.csv", index=False)
fc = test[["tahun", "bulan_num", "tpk_aktual"]].copy()
for m, p in preds.items():
    fc[m] = np.round(p, 2)
fc.to_csv(OUT / "forecast_2025_models.csv", index=False)

pd.set_option("display.width", 200)
print(res.drop(columns="keterangan").to_string(index=False))
