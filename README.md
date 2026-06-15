# Analisis Strategis Pariwisata Jawa Barat (Kelompok 12)

Proyek ini merupakan sistem analitik data komprehensif yang dirancang untuk menganalisis tren pariwisata di Jawa Barat, khususnya pada sektor Wisata Alam (ODTW) dan Tingkat Penghunian Kamar (TPK) Hotel. Menggunakan kerangka kerja OSEMN, proyek ini menghasilkan pengelompokkan kawasan wisata (Clustering) dan prediksi hunian hotel (Regression) untuk mendukung pengambilan keputusan berbasis data.

## 📂 Struktur Folder
Penyusunan folder mengikuti standar manajemen proyek data analitik agar setiap tahap dapat ditelusuri (*traceable*):
- `data/raw/` : Koleksi dataset mentah asli (format .csv).
- `data/processed/` : Data hasil tahap awal pembersihan.
- `data/clean/` : Dataset final yang siap digunakan oleh model.
- `notebooks/` : Pipeline utama pengerjaan (01 - 05).
- `outputs/figures/` : Galeri visualisasi hasil analisis dan pemodelan.
- `outputs/model_results/` : File CSV hasil output model (Clustering & Prediksi).
- `dashboard/` : Antarmuka interaktif untuk penyajian wawasan.
- `slides/` : Materi presentasi kelompok.

## 🚀 Panduan Menjalankan Sistem
Untuk mereproduksi hasil analisis, jalankan file di folder `notebooks/` secara berurutan sesuai penomoran berikut:

1.  **`01_obtain_data.py`**
    Mengambil data mentah dari folder `raw`, melakukan pemeriksaan kualitas awal, dan memberikan flag pada data yang tidak konsisten.
2.  **`02_scrub_final.ipynb`**
    Melakukan pembersihan mendalam, menangani *missing values*, melakukan integrasi (*merging*) antar dataset, dan rekayasa fitur (*feature engineering*).
3.  **`03_explore_viz.py`**
    Menghasilkan visualisasi eksploratif untuk memahami tren historis dan dampak pandemi terhadap pariwisata.
4.  **`04_model.ipynb`**
    Tahap inti pemodelan menggunakan K-Means Clustering untuk segmentasi kawasan dan Linear Regression untuk prediksi TPK Hotel.
5.  **`05_interpret.ipynb`**
    Evaluasi performa model dan ekstraksi wawasan strategis sebagai dasar rekomendasi.

**Akses Dashboard:**
Setelah seluruh pipeline dijalankan, hasil akhir dapat dilihat secara interaktif dengan membuka file `dashboard/dashboard.html` langsung melalui peramban web (*browser*).

## 🛠️ Dependensi (Requirements)
Sistem ini dikembangkan menggunakan Python 3.x dengan beberapa pustaka utama:
- `pandas` & `numpy` (Olah data)
- `matplotlib` & `seaborn` (Visualisasi statis)
- `plotly` (Visualisasi interaktif dashboard)
- `scikit-learn` (Pemodelan Machine Learning)

## 👥 Kontribusi Tim
- **Bastian Natanael Sibarani**: Integrasi sistem, logika dashboard, dan visualisasi data.
- **Gabriel Marcellino**: Inisialisasi proyek, *data scrubbing*, dan eksplorasi data hotel.
- **Faishal**: Narasi teknis, pengembangan model ML, dan visualisasi tren.
- **Gymnastiar**: Pengolahan dataset *processed* dan analisis awal.
- **Rivaldi**: Penyusunan materi presentasi dan asistensi desain dashboard.

---
*Proyek ini disusun sebagai Tugas Besar Mata Kuliah II4013 Data Analitik - Senin, 15 Juni 2026.*
