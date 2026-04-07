# House Indexing AI Gateway (Simaster UGM) — MVP

API Gateway berbasis **FastAPI** untuk menerima 4–5 foto rumah dari Simaster dan mengembalikan **JSON analisis indeks rumah** menggunakan **GPT-4o Vision**.

## Fitur (MVP)

- `POST /api/v1/analyze` menerima **1–5 foto** untuk 1 `student_id` (field multipart `files` diulang)
- Autentikasi internal: header **`X-API-KEY`** (diset via `SIMASTER_API_KEY`)
- Preprocessing gambar: resize + **strip EXIF**
- Integrasi OpenAI GPT-4o Vision (multi-foto dalam 1 request)
- Output JSON tervalidasi (Pydantic)

## Prasyarat

- Windows
- Python 3.x
- venv aktif (atau gunakan `.\venv\Scripts\python.exe`)

## Setup

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

## Menjalankan server

```powershell
Set-Location "d:\Project AI\House Index"
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

- Health: `GET http://127.0.0.1:8000/health`
- Swagger UI: `GET http://127.0.0.1:8000/docs`

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

