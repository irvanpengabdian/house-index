# Integrasi Simaster (PHP) — Contoh Pemakaian API

Dokumen ini berisi contoh implementasi pemanggilan **House Indexing AI Gateway** dari aplikasi PHP (Simaster).

## Ringkasan

- **Endpoint**: `POST /api/v1/analyze`
- **Auth**: header **`X-API-KEY`** (harus sama dengan `SIMASTER_API_KEY` di server gateway)
- **Payload**: `multipart/form-data`
  - `student_id` (string)
  - `files[]` *tidak dipakai* — yang dipakai adalah **field bernama `files` yang diulang** (bukan array JSON)
- **Jumlah foto**: default 1–5 (konfigurasi server)

## Konfigurasi (di sisi Simaster)

Simpan konfigurasi ini di env/config aplikasi Simaster:

- `HOUSE_INDEX_GATEWAY_BASE_URL` (mis. `https://gateway.domain.ac.id`)
- `HOUSE_INDEX_GATEWAY_API_KEY` (nilai untuk header `X-API-KEY`)
- Timeout rekomendasi: 45–60 detik untuk 4–5 foto (tergantung jaringan dan beban)

## 1) Contoh PHP murni (cURL)

Contoh ini mengirim **4 foto** untuk 1 mahasiswa.

```php
<?php

$baseUrl = rtrim(getenv('HOUSE_INDEX_GATEWAY_BASE_URL'), '/');
$apiKey  = getenv('HOUSE_INDEX_GATEWAY_API_KEY');

$studentId = '1234567890';
$photoPaths = [
  __DIR__ . '/foto1.jpg',
  __DIR__ . '/foto2.jpg',
  __DIR__ . '/foto3.jpg',
  __DIR__ . '/foto4.jpg',
];

$url = $baseUrl . '/api/v1/analyze';

$postFields = [
  'student_id' => $studentId,
];

// Field harus bernama "files" dan diulang untuk setiap foto.
// Di PHP cURL, kita bisa membuat key unik tapi dengan nama field yang sama memakai "files[0]" dkk
// dan server FastAPI akan tetap membaca sebagai list UploadFile jika field name-nya "files".
// Namun untuk aman, kita pakai "files" berulang dengan array syntax yang akan dikirim sebagai "files".
foreach ($photoPaths as $i => $path) {
  if (!file_exists($path)) {
    throw new RuntimeException("File not found: " . $path);
  }
  $postFields["files[$i]"] = new CURLFile($path, mime_content_type($path), basename($path));
}

$ch = curl_init($url);
curl_setopt_array($ch, [
  CURLOPT_POST => true,
  CURLOPT_POSTFIELDS => $postFields,
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_HTTPHEADER => [
    'X-API-KEY: ' . $apiKey,
  ],
  CURLOPT_TIMEOUT => 60,
]);

$raw = curl_exec($ch);
if ($raw === false) {
  $err = curl_error($ch);
  curl_close($ch);
  throw new RuntimeException("cURL error: " . $err);
}

$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
curl_close($ch);

$data = json_decode($raw, true);
if (!is_array($data)) {
  throw new RuntimeException("Invalid JSON response (HTTP $httpCode): " . $raw);
}

if ($httpCode !== 200) {
  $detail = $data['detail'] ?? '(no detail)';
  throw new RuntimeException("Gateway error HTTP $httpCode: " . $detail);
}

// Sukses
// Contoh akses:
// $data['house_index_score'], $data['confidence_level'], dst.
print_r($data);
```

### Catatan penting tentang nama field `files`

FastAPI menerima parameter `files: list[UploadFile] = File(...)` yang akan membaca beberapa part dengan nama field **`files`**.

Beberapa library PHP mengirim `files[0]`, `files[1]` sebagai field name yang berbeda. Jika itu terjadi dan server tidak menerimanya, gunakan pendekatan yang memastikan nama field-nya **benar-benar `files`** (lihat contoh Guzzle di bawah), atau sesuaikan sisi gateway untuk juga menerima `files[]`.

## 2) Contoh Guzzle (disarankan untuk Laravel)

```php
<?php

use GuzzleHttp\Client;

$baseUrl = rtrim(env('HOUSE_INDEX_GATEWAY_BASE_URL'), '/');
$apiKey  = env('HOUSE_INDEX_GATEWAY_API_KEY');

$studentId = '1234567890';
$photoPaths = [
  storage_path('app/foto1.jpg'),
  storage_path('app/foto2.jpg'),
  storage_path('app/foto3.jpg'),
  storage_path('app/foto4.jpg'),
];

$multipart = [
  [
    'name' => 'student_id',
    'contents' => $studentId,
  ],
];

foreach ($photoPaths as $path) {
  $multipart[] = [
    'name' => 'files', // IMPORTANT: repeated field name
    'contents' => fopen($path, 'r'),
    'filename' => basename($path),
    'headers' => [
      'Content-Type' => mime_content_type($path) ?: 'image/jpeg',
    ],
  ];
}

$client = new Client([
  'base_uri' => $baseUrl,
  'timeout'  => 60,
]);

$response = $client->post('/api/v1/analyze', [
  'headers' => [
    'X-API-KEY' => $apiKey,
  ],
  'multipart' => $multipart,
]);

$body = (string) $response->getBody();
$data = json_decode($body, true);
if (!is_array($data)) {
  throw new RuntimeException('Invalid JSON response: ' . $body);
}

return $data;
```

## 3) Mapping error untuk Simaster (rekomendasi)

- **401**: Simaster tidak mengirim `X-API-KEY` → perbaiki konfigurasi header
- **403**: `X-API-KEY` salah → sinkronisasi secret Simaster ↔ Gateway
- **413**: ukuran file terlalu besar → kompres/resize sebelum upload atau atur limit server
- **415**: format file tidak didukung → pastikan hanya JPEG/PNG/WebP
- **502**: output AI tidak sesuai skema / gagal parsing → retry (mis. 1–2 kali) lalu fallback ke verifikasi manual
- **504**: timeout → retry dengan backoff

## 4) Best practice integrasi

- Gunakan timeout **60 detik** untuk 4–5 foto pada tahap awal.
- Pastikan foto yang dikirim sudah dipilih yang paling informatif (fasilitasi skor lebih stabil).
- Jangan log file/foto ke log aplikasi Simaster.

