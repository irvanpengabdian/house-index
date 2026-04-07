# Security Checklist (MVP)

Checklist ini fokus pada kontrol minimum agar integrasi Simaster → Gateway aman untuk tahap MVP.

## Secrets & konfigurasi

- [x] Tidak ada API key yang di-hardcode di kode
- [x] `.env` diabaikan oleh VCS via `.gitignore`
- [ ] `.env.example` tersedia dan tidak memuat secret
- [ ] Rotasi API key (prosedur operasional) terdokumentasi

## Privasi data foto

- [x] Metadata **EXIF** dihapus sebelum mengirim gambar ke OpenAI (re-encode)
- [ ] Tidak menyimpan file upload di disk (MVP sebaiknya in-memory)
- [ ] Log tidak memuat isi foto/base64, dan tidak memuat API key

## Autentikasi antar layanan (Simaster → Gateway)

- [ ] `X-API-KEY` (atau mTLS) untuk request dari Simaster
- [ ] IP allowlist untuk origin Simaster (jika memungkinkan)

## Ketahanan & penyalahgunaan

- [ ] Rate limiting (mis. per IP / per API key internal)
- [ ] Batas ukuran file dan jumlah foto per request ditetapkan (sudah ada, pastikan nilainya disepakati)
- [ ] Timeout request ke OpenAI (sudah ada; sesuaikan untuk 4–5 foto)

## Observability

- [ ] Request ID / correlation ID untuk tracing
- [ ] Error response konsisten (tanpa detail internal sensitif)

