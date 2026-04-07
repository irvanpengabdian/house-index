# Regression Tests (Manual) — MVP

Dokumen ini untuk uji manual setelah perubahan kode/prompt, terutama menjelang demo/UAT.

## Prasyarat

- Server berjalan:

```powershell
Set-Location "d:\Project AI\House Index"
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 127.0.0.1 --port 8000
```

- (Untuk end-to-end nyata) `.env` berisi:
  - `OPENAI_API_KEY`
  - `SIMASTER_API_KEY` (karena endpoint butuh header `X-API-KEY`)

## 1) Health check

```bash
curl "http://127.0.0.1:8000/health"
```

Ekspektasi: `200` dengan `{"status":"ok"}`.

## 2) Upload 1 foto (happy path)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/analyze" ^
  -H "X-API-KEY: <SIMASTER_API_KEY>" ^
  -F "student_id=TEST001" ^
  -F "files=@foto1.jpg;type=image/jpeg"
```

Ekspektasi:
- `200`
- body JSON valid (punya `student_id`, `house_index_score`, `confidence_level`)

## 3) Upload 4–5 foto (happy path)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/analyze" ^
  -H "X-API-KEY: <SIMASTER_API_KEY>" ^
  -F "student_id=TEST002" ^
  -F "files=@foto1.jpg;type=image/jpeg" ^
  -F "files=@foto2.jpg;type=image/jpeg" ^
  -F "files=@foto3.jpg;type=image/jpeg" ^
  -F "files=@foto4.jpg;type=image/jpeg"
```

Ekspektasi:
- `200`
- satu objek JSON agregat (bukan array)

## 4) Tipe file tidak didukung

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/analyze" ^
  -H "X-API-KEY: <SIMASTER_API_KEY>" ^
  -F "student_id=TEST003" ^
  -F "files=@file.txt;type=text/plain"
```

Ekspektasi: `415`.

## 5) Terlalu banyak foto

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/analyze" ^
  -H "X-API-KEY: <SIMASTER_API_KEY>" ^
  -F "student_id=TEST004" ^
  -F "files=@1.jpg;type=image/jpeg" ^
  -F "files=@2.jpg;type=image/jpeg" ^
  -F "files=@3.jpg;type=image/jpeg" ^
  -F "files=@4.jpg;type=image/jpeg" ^
  -F "files=@5.jpg;type=image/jpeg" ^
  -F "files=@6.jpg;type=image/jpeg"
```

Ekspektasi: `400` dengan pesan maksimal foto.

## 6) Tanpa API key (kontrol konfigurasi)

- Hapus/komentari `OPENAI_API_KEY` di `.env`, restart server.
- Lakukan request happy path.

Ekspektasi: `503` dengan detail konfigurasi.

