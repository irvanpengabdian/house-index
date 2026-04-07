# Sprint Plan — House Indexing AI Gateway (Simaster UGM)

**Periode:** 7 hari kerja  
**Tujuan sprint:** MVP dapat menerima foto dari Simaster (upload atau URL), memproses dengan **GPT-4o Vision**, dan mengembalikan **JSON analisis indeks rumah** yang konsisten dan tervalidasi.  
**Lingkungan:** Windows, Python 3.x, venv aktif.  
**Referensi produk:** `prd.md` (alur ingestion → validasi → AI → parsing → delivery).

---

## Definisi MVP (akhir Sprint)

| Kriteria | Deskripsi |
|----------|-----------|
| **API** | Endpoint FastAPI (mis. `POST /api/v1/analyze`) menerima `student_id` + **file upload** dan/atau **URL gambar** (sesuai kesepakatan kontrak dengan tim Simaster). |
| **AI** | Panggilan ke OpenAI **GPT-4o** (mode vision) dengan system prompt IR sesuai PRD (material BPS/PUPR, C1–C6, proksi kekayaan, output **hanya JSON**). |
| **Output** | Respons JSON terstruktur: minimal `house_index_score` (1.0–5.0 atau -1 jika tidak valid), field material/kondisi, `confidence_level`, `verification_notes` bila perlu. |
| **Validasi** | Skema respons divalidasi dengan **Pydantic**; gagal parsing → error terkontrol (bukan raw text ke klien). |
| **Gambar** | **Pillow**: resize/kompresi ringan untuk optimasi token; **strip EXIF** sebelum kirim ke OpenAI (privasi, sesuai PRD). |
| **Operasional** | Konfigurasi lewat **`.env`** (`OPENAI_API_KEY`, timeout); dokumentasi singkat cara menjalankan (`uvicorn`). |

**Di luar MVP sprint ini (backlog):** IP whitelisting penuh, rate limiting produksi, deteksi blur OpenCV/Laplacian, antrian background, rotasi API key terjadwal, UAT 100 sampel.

---

## Arsitektur target (MVP)

```text
Simaster → POST (multipart / JSON+URL) → FastAPI (app/api)
       → validasi & preprocessing (app/services) → OpenAI GPT-4o Vision
       → parse & validate JSON (app/models) → respons ke Simaster
```

**Komponen kode:** `app/main.py`, router di `app/api/`, skema & response model di `app/models/`, logika bisnis & integrasi OpenAI di `app/services/`.

---

## Hari 1 — Bootstrap & kontrak API

**Status:** DONE ✅ (struktur FastAPI, `GET /health`, `.env.example` tersedia)

| Aktivitas | Deliverable |
|-----------|-------------|
| Finalisasi skema request/response (field wajib, opsional, error codes) dengan tim Simaster | Dokumen kontrak API 1 halaman (bisa di `DOCS/` atau komentar OpenAPI) |
| Inisialisasi struktur FastAPI (`app/`, router, `main.py`) | Aplikasi `uvicorn` jalan, health check `GET /health` |
| `.env.example` (tanpa secret) | Variabel: `OPENAI_API_KEY`, `OPENAI_MODEL=gpt-4o`, `REQUEST_TIMEOUT_SECONDS` |
| Spike: satu panggilan manual ke OpenAI vision dengan 1 foto lokal | Script/notebook atau endpoint sementara memverifikasi kunci & model |

**Risiko:** Perbedaan asumsi multipart vs URL — mitigasi: putuskan satu jalur utama untuk MVP (mis. multipart dulu, URL sebagai opsi jika waktu mencukupi).

---

## Hari 2 — Endpoint ingestion & multipart

**Status:** DONE ✅ (endpoint `POST /api/v1/analyze` multipart, menerima beberapa foto via field `files`)

| Aktivitas | Deliverable |
|-----------|-------------|
| `POST` menerima `student_id` (string) + file gambar (`python-multipart`) | Validasi tipe MIME (`image/jpeg`, `image/png`, dll.) dan ukuran maksimum |
| Penolakan jelas: 400/413/415 dengan body error konsisten | Model error Pydantic |
| (Opsional MVP+) Fetch gambar dari URL jika disepakati | Service terpisah, timeout singkat, validasi content-type |

**Kriteria selesai:** Postman/curl dapat mengirim foto dan menerima respons (boleh masih placeholder tanpa AI penuh).

---

## Hari 3 — Preprocessing gambar & privasi

**Status:** DONE ✅ (Pillow resize + re-encode untuk strip EXIF)

| Aktivitas | Deliverable |
|-----------|-------------|
| Resize maks dimensi + kompresi JPEG/WebP sesuai kebijakan token | Modul di `app/services/image_processing.py` |
| Hapus metadata EXIF sebelum encode ke API | Verifikasi dengan satu gambar ber-EXIF GPS |
| Standarisasi format ke bytes/base64 untuk OpenAI | Fungsi tunggal yang dipakai pipeline AI |

**Kriteria selesai:** Gambar besar otomatis diperkecil; tidak ada bocoran lokasi lewat EXIF ke OpenAI.

---

## Hari 4 — Integrasi GPT-4o Vision & prompting

**Status:** DONE ✅ (system prompt dari PRD + panggilan OpenAI GPT-4o Vision; dukung multi-foto dalam 1 request)

| Aktivitas | Deliverable |
|-----------|-------------|
| Port system prompt dari PRD ke konstanta/konfigurasi terpisah | `app/services/prompts.py` atau `app/core/prompts.py` |
| Panggilan `chat.completions` / responses API dengan image URL base64 sesuai SDK OpenAI terbaru | `app/services/openai_client.py` (async disarankan) |
| Parameter: `model=gpt-4o`, batas token respons, **timeout ~30s** (selaras PRD) | Penanganan `504`/timeout ke klien |

**Kriteria selesai:** Satu foto menghasilkan teks JSON mentah dari model (belum wajib lolos skema).

---

## Hari 5 — Parsing JSON & model Pydantic

**Status:** DONE ✅ (extract JSON dari output model + validasi skema `HouseIndexAnalysis`)

| Aktivitas | Deliverable |
|-----------|-------------|
| Ekstraksi JSON dari respons (strip markdown code fence jika ada) | Parser defensif + log untuk respons rusak |
| Definisi `HouseIndexAnalysis` (atau nama setara) dengan field PRD | File di `app/models/` |
| Validasi range `house_index_score`, enum kondisi, null untuk elemen tidak terlihat | Unit test minimal untuk skema |

**Kriteria selesai:** Respons gagal validasi → 422/502 dengan pesan aman (tanpa menyimpan foto).

---

## Hari 6 — Alur lengkap, error handling, & skor

**Status:** DONE ✅ (pipeline end-to-end upload → preprocess → vision → parse → return, dengan error 400/413/415/502/503/504)

| Aktivitas | Deliverable |
|-----------|-------------|
| Rangkai pipeline: upload → preprocess → vision → parse → return | Satu service `analyze_house_image` |
| Mapping kasus: foto tidak rumah (`score: -1`), confidence rendah, elemen null | Sesuai instruksi prompt PRD |
| Logging struktural (tanpa data sensitif berlebihan) | Level INFO untuk request id / student_id hash opsional |

**Kriteria selesai:** Alur end-to-end stabil untuk 5–10 foto uji bervariasi.

---

## Hari 7 — Hardening MVP, dokumentasi, & serah terima

**Status:** IN PROGRESS 🟨 (sudah dibuat: `DOCS/API.md`, `DOCS/SECURITY_CHECKLIST.md`, `DOCS/REGRESSION_TESTS.md`, `.gitignore`; tersisa: uji end-to-end dengan API key + demo/serah terima)

| Aktivitas | Deliverable |
|-----------|-------------|
| OpenAPI/Swagger dari FastAPI diperiksa; contoh request | README atau `DOCS/API.md` singkat |
| Ceklist keamanan MVP: tidak ada API key di repo, `.gitignore` untuk `.env` | Repo bersih |
| Uji regresi manual: error jaringan, timeout, file bukan gambar | Catatan hasil di `DOCS/` atau komentar sprint |
| Demo singkat ke stakeholder (alur Simaster) | Rekaman atau skrip demo |

**Kriteria selesai:** MVP siap diintegrasikan ke lingkungan pengujian Simaster.

---

## Metrik keberhasilan Sprint

| Metrik | Target |
|--------|--------|
| Latensi happy path (tanpa jaringan bermasalah) | \< 30 detik (timeout server selaras PRD) |
| Keluaran JSON valid | ≥ 90% pada set foto uji internal (iterasi prompt jika perlu) |
| Keterlacakan | Setiap error punya kode/pesan yang dapat dijadikan retry policy oleh Simaster |

---

## Dependensi & asumsi

- Akses **OpenAI API** dan kuota untuk **GPT-4o** vision.
- Tim Simaster menyediakan format pasti untuk `student_id` dan batas ukuran file.
- Untuk produksi nanti: HTTPS, autentikasi `X-API-KEY`, dan pembatasan IP sesuai PRD Fase 3.

---

## Owner & ritme (disarankan)

- **Daily sync** 15 menit: bloker teknis (API OpenAI, kontrak Simaster).
- **Backlog pasca-MVP:** blur detection (OpenCV), queue worker, monitoring.

*Dokumen ini selaras dengan roadmap PRD Fase 1 (prototype) dan sebagian Fase 2 (skema & validasi) agar output MVP siap dipakai verifikator.*
