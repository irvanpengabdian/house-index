# House Indexing AI Gateway (Simaster UGM) — MVP

API Gateway berbasis **FastAPI** untuk menerima 4–5 foto rumah dari Simaster dan mengembalikan **JSON analisis indeks rumah** menggunakan **GPT-4o Vision**.

## Fitur (MVP)

- `POST /api/v1/analyze` menerima **1–5 foto** untuk 1 `student_id` (field multipart `files` diulang)
- Autentikasi internal: header **`X-API-KEY`** (diset via `SIMASTER_API_KEY`)
- Preprocessing gambar: resize + **strip EXIF**
- Integrasi OpenAI GPT-4o Vision (multi-foto dalam 1 request)
- Output JSON tervalidasi (Pydantic)

## Prasyarat

- **Lokal (tanpa Docker)**: Windows/Linux + Python 3.x
- **Dengan Docker (disarankan untuk deploy)**: Docker Engine + Docker Compose

## Setup

### Setup lokal (Windows)

Install dependency:

```powershell
Set-Location "d:\Project AI\House Index"
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Konfigurasi environment:

```powershell
Copy-Item .env.example .env
```

Isi `.env` minimal:

```env
SIMASTER_API_KEY=isi_kunci_internal_simaster
OPENAI_API_KEY=isi_openai_api_key
```

### System prompt (tanpa ubah kode)

Teks system prompt untuk GPT-4o dibaca dari file **`config/system_prompt.txt`** (UTF-8). Untuk mengganti atau mengoptimasi prompt, edit file itu lalu **restart** server (atau redeploy container).

Opsional di `.env`:

```env
SYSTEM_PROMPT_FILE=config/system_prompt.txt
```

Bisa juga path **absolut** (mis. volume mount di Docker). Jika file tidak ada atau kosong, aplikasi memakai **prompt cadangan** di kode dan menulis peringatan di log.

### Keamanan (ringkas)

- **Validasi file**: magic bytes JPEG/PNG/WebP + harus cocok dengan `Content-Type`; batas piksel decode (`MAX_DECODED_PIXELS`) untuk mitigasi decompression bomb.
- **Rate limit**: `RATE_LIMIT_ANALYZE_PER_MINUTE` per hash `X-API-KEY` + IP (in-memory; untuk multi-replica gunakan limiter terpusat di proxy/Redis).
- **Docs**: set `DOCS_ENABLED=false` di production untuk menyembunyikan `/docs` dan `/redoc`.
- **Docker**: container berjalan sebagai user non-root (`appuser`).

### Menjalankan server (Windows)

```powershell
Set-Location "d:\Project AI\House Index"
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: `GET http://127.0.0.1:8000/health`
- Swagger UI: `GET http://127.0.0.1:8000/docs`

### Menjalankan server (Linux/macOS)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Deploy dengan Docker

1) Buat file `.env` dari contoh:

```bash
cp .env.example .env
```

2) Isi minimal:

```env
SIMASTER_API_KEY=...
OPENAI_API_KEY=...
```

3) Build & run:

```bash
docker compose up --build
```

Server akan tersedia di:
- `http://localhost:8000/health`
- `http://localhost:8000/docs`

## Contoh request (PowerShell + curl.exe)

Catatan: di PowerShell, gunakan **`curl.exe`** (bukan `curl` yang alias ke `Invoke-WebRequest`).

```powershell
curl.exe -X POST "http://127.0.0.1:8000/api/v1/analyze" `
  -H "X-API-KEY: <SIMASTER_API_KEY>" `
  -F "student_id=TEST001" `
  -F "files=@C:\path\foto1.jpg;type=image/jpeg" `
  -F "files=@C:\path\foto2.jpg;type=image/jpeg"
```

## Testing

Jalankan unit test (OpenAI dimock, jadi tidak butuh internet/billing):

```powershell
Set-Location "d:\Project AI\House Index"
.\venv\Scripts\python.exe -m unittest -v
```

## Dokumentasi

- API contract: `DOCS/API.md`
- Panduan integrasi PHP (Simaster): `DOCS/SIMASTER_PHP_INTEGRATION.md`
- Regression tests manual: `DOCS/REGRESSION_TESTS.md`
- Security checklist: `DOCS/SECURITY_CHECKLIST.md`

