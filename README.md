# Sentiment POSPAY

Project ini mengambil review aplikasi, melakukan transformasi + enrichment sentimen, lalu menyimpan hasilnya ke CSV.

## Menjalankan pipeline

```bash
python main.py
```

Output utama:
- `data/raw/reviews_raw.csv`
- `data/processed/reviews.csv`

## Dashboard Executive Summary

Dashboard interaktif tersedia di `dashboard_executive.py` dengan flow:
1. Executive overview (distribusi sentimen + KPI)
2. Zoom in ke sentimen (`positive`, `neutral`, `negative`)
3. Zoom in ke issue untuk melihat rekapan isu paling krusial
4. Lihat daftar review detail pada filter terpilih

Jalankan dengan:

```bash
streamlit run dashboard_executive.py
```

> Jika `streamlit` belum terpasang, install dulu:
>
> ```bash
> pip install streamlit
> ```
