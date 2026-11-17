# Reddit Israel–Palestine Sentiment Analytics API

## Struktur
```
app/
  main.py            # create_app, lifespan, CORS, registrasi router
  constants.py       # daftar tabel wajib, definisi tema keyword
  core/              # config (.env), koneksi DuckDB, error handler
  schemas/common.py  # envelope {data, meta}, pagination, enum, SafeJSONResponse
  utils/             # sanitasi NaN/Inf/Decimal/tanggal -> JSON valid
  repositories/      # SEMUA SQL (satu file per kelompok analisis)
  routers/           # definisi endpoint + validasi parameter
scripts/make_sample_db.py   # DB sintetis untuk uji coba tanpa file asli
tests/test_api.py           # 48 tes (semua endpoint, JSON ketat, paginasi, validasi)
```

## Menjalankan
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # lalu isi DUCKDB_PATH
uvicorn app.main:app --reload --port 8000
```
Swagger: http://localhost:8000/docs