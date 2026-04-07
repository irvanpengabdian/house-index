# API — House Indexing AI Gateway (MVP)

## Base URL (local)

- `http://127.0.0.1:8000`

## Swagger / OpenAPI

- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`

## Health

### `GET /health`

**Response 200**

```json
{ "status": "ok" }
```

## Analisis Indeks Rumah

### `POST /api/v1/analyze`

Menerima **1–5 foto** rumah untuk **1 mahasiswa**, lalu mengembalikan **1 objek JSON** analisis indeks rumah (agregasi dari semua foto).

#### Request

- **Content-Type**: `multipart/form-data`
- **Auth**: wajib header `X-API-KEY`
- **Fields**
  - **`student_id`**: string (wajib)
  - **`files`**: file gambar (wajib). Untuk banyak foto, ulangi field `files` beberapa kali.
    - MIME yang didukung: `image/jpeg`, `image/png`, `image/webp`
- **Headers**
  - **`X-API-KEY`**: wajib, harus sama dengan `SIMASTER_API_KEY` di server

#### Contoh (curl, 4 foto)

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/analyze" ^
  -H "X-API-KEY: <SIMASTER_API_KEY>" ^
  -F "student_id=1234567890" ^
  -F "files=@foto1.jpg;type=image/jpeg" ^
  -F "files=@foto2.jpg;type=image/jpeg" ^
  -F "files=@foto3.jpg;type=image/jpeg" ^
  -F "files=@foto4.jpg;type=image/jpeg"
```

#### Response 200 (skema ringkas)

```json
{
  "student_id": "1234567890",
  "house_index_score": 3.7,
  "confidence_level": 0.82,
  "materials": {
    "atap": { "terlihat": true, "kategori": "LAYAK", "kondisi": "C3" },
    "dinding": null,
    "lantai": { "terlihat": true, "kategori": "LAYAK", "kondisi": "C2" }
  },
  "wealth_proxies": {
    "ac_outdoor_terdeteksi": false,
    "garasi_atau_parkir_tertutup": true,
    "plafon_interior_mewah": false,
    "furnitur_berkualitas": false,
    "estimasi_luas_ruang": "sedang"
  },
  "verification_notes": null
}
```

#### Error codes (MVP)

- **400**: input tidak valid (mis. jumlah foto di luar batas)
- **401**: header `X-API-KEY` tidak ada
- **403**: `X-API-KEY` salah
- **413**: ukuran file melebihi limit
- **415**: tipe file tidak didukung
- **422**: field wajib tidak ada / format form-data tidak sesuai
- **502**: respons AI tidak valid / gagal divalidasi
- **503**: `OPENAI_API_KEY` belum dikonfigurasi
- **503**: `SIMASTER_API_KEY` belum dikonfigurasi (server tidak akan menerima request tanpa kunci internal)
- **504**: timeout dari layanan AI

## Konfigurasi `.env`

Minimal:

```env
SIMASTER_API_KEY=...
OPENAI_API_KEY=...
```

## Contoh integrasi PHP (Simaster)

Lihat: `DOCS/SIMASTER_PHP_INTEGRATION.md`

Opsional:

```env
OPENAI_MODEL=gpt-4o
REQUEST_TIMEOUT_SECONDS=30
MIN_IMAGES_PER_REQUEST=1
MAX_IMAGES_PER_REQUEST=5
MAX_IMAGE_BYTES=10485760
MAX_IMAGE_SIDE=2048
JPEG_QUALITY=85
```

