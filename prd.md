## **PRD: House Indexing AI Gateway (Simaster UGM)**

### **1\. Ringkasan Proyek**

Membangun _middleware_ (API Gateway) yang menjembatani platform Simaster dengan LLM Vision (GPT-4o/Claude 3.5 Sonnet) untuk mengekstraksi data kemiskinan/kekayaan secara objektif dari foto rumah tinggal calon mahasiswa.

### **2\. Alur Kerja Sistem (System Workflow)**

- **Ingestion:** Simaster mengirimkan POST request berisi student*id dan \_binary* atau _URL_ foto.
- **Validation & Pre-processing:** Gateway memvalidasi format foto dan melakukan kompresi otomatis (optimasi biaya token).
- **AI Orchestration:** Gateway mengirimkan _System Prompt_ khusus dan foto ke LLM Vision.
- **Parsing & Scoring:** Gateway menerima respon teks, memastikan format JSON valid, dan menghitung house_index_score.
- **Delivery:** Hasil dikirimkan kembali ke UI Verifikator di Simaster.

## **3\. Rekomendasi Tech Stack**

| **Komponen**  | **Python (FastAPI) - Rekomendasi Utama**                                                                                          | **PHP (Laravel) - Alternatif Integrasi**                                                                        |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| **Alasan**    | Sangat efisien untuk tugas _asynchronous_. Library AI (OpenAI/Anthropic SDK) paling _up-to-date_ di Python.                       | Memudahkan integrasi jika tim IT UGM sudah sangat familiar dengan ekosistem PHP/Simaster.                       |
| ---           | ---                                                                                                                               | ---                                                                                                             |
| **Kelebihan** | **Pydantic v2** untuk validasi skema JSON sangat ketat dan cepat. Native _async_ memudahkan menangani _timeout_ LLM (5-15 detik). | **Laravel Job/Queue** sangat matang untuk menangani pemrosesan foto di _background_ agar Simaster tidak _hang_. |
| ---           | ---                                                                                                                               | ---                                                                                                             |
| **Library**   | FastAPI, Pydantic, httpx, Pillow (image processing).                                                                              | Laravel 11, Guzzle, Spatie Media Library.                                                                       |
| ---           | ---                                                                                                                               | ---                                                                                                             |

**Keputusan Arsitektur:** Gunakan **Python (FastAPI)** jika performa dan latensi adalah prioritas, karena penanganan stream data dan integrasi SDK AI jauh lebih _seamless_ dibanding PHP.

## **4\. Sistem Prompting (System Message Draft)**

Untuk mendapatkan akurasi "C1-C4", AI harus diberikan konteks sosiodemografis Indonesia.

**Prompt Message:**

## **\[ROLE & OBJECTIVE\]**

Anda adalah **Senior Building Inspector UGM UKT Verification System**. Tugas utama Anda adalah mengekstraksi data visual dari foto rumah menjadi **Indeks Rumah (IR)** numerik yang objektif. Data ini akan diintegrasikan ke dalam perhitungan **Indeks Kemampuan Ekonomi (IKE)** calon mahasiswa.

## **\[ANALISIS DATA VISUAL\]**

### \*\*1\. Kriteria Material (Standar BPS/PUPR)

**Tentukan apakah material termasuk kategori LAYAK atau TIDAK **LAYAK\*\*:

- **ATAP:**
  - **Layak:** Beton, Genteng, Seng, Kayu/Sirap.
  - **Tidak Layak:** Asbes, Bambu, Rumbia.
- **DINDING:**
  - **Layak:** Tembok diplester, Kayu berkualitas, Batang kayu.
  - **Tidak Layak:** Anyaman bambu, Seng bekas.
- **LANTAI:**
  - **Layak:** Marmer/Granit, Keramik, Ubin, Semen Rapi.
  - **Tidak Layak:** Tanah, Bambu.

### **2\. Skala Kondisi (Maintenance & Finishing)**

Berikan label kondisi untuk setiap elemen material:

- **C1:** Sangat Baik / Mewah
- **C2:** Baik
- **C3:** Cukup
- **C4:** Kurang
- **C5:** Buruk
- **C6:** Rusak Berat

### **3\. Proksi Kekayaan (Wealth Proxies)**

Identifikasi keberadaan aset berikut:

- Unit AC luar ruang (_outdoor unit_).
- Garasi mobil / area parkir tertutup.
- Plafon interior (Gypsum/PVC).
- Kualitas furnitur (kayu solid, sofa, dll).
- Estimasi luas ruang.

## **\[FORMULASI SKORING\]**

Hasilkan house_index_score dengan skala **1.0 - 5.0** berdasarkan pembobotan:

- **Kualitas Material (Atap, Dinding, Lantai):** 40%
- **Kondisi & Finishing (C1-C6):** 40%
- **Proksi Aset Tersier (AC, Garasi, Furnitur):** 20%

**Interpretasi Skor:**

- **Skor 5.0:** Rumah Mewah/Sangat Layak (Kuintil 5 - UKT Unggul).
- **Skor 1.0:** Rumah Sangat Sederhana/Tidak Layak (Kuintil 1 - Subsidi 100%).

## **\[OUTPUT INSTRUCTIONS\]**

- **Output HANYA berupa JSON.**
- Jangan berikan teks pembuka, penutup, atau penjelasan di luar blok JSON.
- Jika foto buram atau gelap, berikan confidence_level rendah (<0.5).

Jika elemen (Atap/Dinding/Lantai) tidak terlihat dalam foto, berikan nilai null pada field tersebut dan turunkan confidence_level.

## **5\. Pertimbangan Keamanan & Privasi**

- **Data Sanitization:** Gateway harus menghapus _EXIF Metadata_ (GPS, tanggal, tipe HP) dari foto sebelum dikirim ke OpenAI/Anthropic untuk menjaga privasi lokasi mahasiswa.
- **API Key Management:** Gunakan _Environment Variables_ atau _Secret Manager_ (seperti HashiCorp Vault). Jangan pernah melakukan _hardcode_ API Key dalam kode.
- **Internal Authentication:** API Gateway hanya boleh menerima request dari IP Server Simaster (IP Whitelisting) dan menggunakan X-API-KEY untuk autentikasi antar-layanan.
- **Image Expiry:** Foto yang di-_upload_ ke Gateway harus dihapus segera setelah analisis selesai atau disimpan dalam _bucket_ terenkripsi dengan akses terbatas.

## **6\. Handling: Kegagalan & Error Management**

- **Blur & Low Quality Detection:  
   **Gunakan library (seperti OpenCV di Python) untuk mengecek skor _Laplacian variance_. Jika di bawah ambang batas (terlalu blur), Gateway langsung mengembalikan error: 422 Unprocessable Entity - Image too blurry.
- **Irrelevant Image Detection:  
   **Jika AI mendeteksi foto bukan rumah (misal: foto selfie atau dokumen), sistem prompt akan menginstruksikan AI untuk mengisi house_index_score: -1 dan verification_notes: "Foto yang diunggah tidak valid/bukan foto rumah".
- **Rate Limiting & Timeout:  
   **Terapkan _timeout_ 30 detik. Jika API AI tidak merespon, kirim balik status 504 Gateway Timeout agar Simaster dapat melakukan _retry_ secara otomatis.

## **7\. Rencana Pengembangan (Roadmap)**

| **Tahap**              | **Aktivitas**                                                             | **Durasi** |
| ---------------------- | ------------------------------------------------------------------------- | ---------- |
| **Fase 1: Prototype**  | Setup FastAPI, Integrasi API GPT-4o, dan Testing Prompting Manual.        | 1 Minggu   |
| ---                    | ---                                                                       | ---        |
| **Fase 2: Refinement** | Implementasi skema JSON, validasi Pydantic, dan penanganan foto blur.     | 1 Minggu   |
| ---                    | ---                                                                       | ---        |
| **Fase 3: Security**   | Implementasi IP Whitelisting, API Key rotation, dan pembersihan Metadata. | 1 Minggu   |
| ---                    | ---                                                                       | ---        |
| **Fase 4: UAT**        | Uji coba dengan 100 sampel foto asli dari tim verifikator UGM.            | 1 Minggu   |
| ---                    | ---                                                                       | ---        |