# Power — hasil revisi SOTK dan monitoring karyawan

## Menjalankan website

Buka `index.html` melalui mekanisme hosting lokal/static hosting yang biasa digunakan pada proyek. Seluruh library yang dibutuhkan tersedia di folder `lib/`.

Login lokal yang tersedia pada source saat ini:
- Username: `admin`
- Password: `admin123`

## Sumber data

`data.js` dibangun dari `source_data/SOTK_MASTER_REVISI_CABANG_SAJA_POSITION_NAME_GRADE_TIER.xlsx` menggunakan `tools/build_data.py`.

Contoh perintah untuk membuat ulang preload:

```bash
python tools/build_data.py source_data/SOTK_MASTER_REVISI_CABANG_SAJA_POSITION_NAME_GRADE_TIER.xlsx data.js
```

Jangan mengganti workbook sumber dengan master lama bila ingin mempertahankan 912 formasi Cabang dan 394 unit aktif.

## Perbaikan penting dalam versi ini

- Kode organisasi yang diberi nol di depan oleh data karyawan dinormalisasi hanya untuk lookup (mis. `001080103` → `1080103`), sehingga pencocokan SOTK Kantor Wilayah dan Area tidak gagal hanya karena format kode berbeda.
- Monitoring Karyawan memiliki kolom Job Code, Position Name, Job Code Def, dan Position Name Def.
- Keluarga jabatan pada Cabang terutama ditentukan oleh `JOB CODE` current. `Position Name` (awalan 3–5 kata sesuai nama jabatan) dipakai untuk mendeteksi tingkat dan memvalidasi grade dari pasangan kolom yang sama; teks lokasi/unit setelah nama jabatan tidak ikut menentukan tier. Senior Account Officer adalah pengecualian karena menggunakan kode AO: hanya dipetakan ke SAO bila `JOB CODE` current = AO, grade current > 6, dan awalan `Position Name` mengonfirmasi `Senior Account Officer`. AO ber-grade tinggi tanpa konfirmasi nama tetap AO. Grade 8 mengacu pada tingkat 1 dan grade 7 pada tingkat 2.
- Di seluruh tab Monitoring SDM pada level Cabang, filter Jabatan menyediakan satu pilihan `Senior Account Officer`, tanpa opsi tingkat 1/2 atau opsi nama posisi per outlet yang terlalu rinci.
- Pasangan current (`JOB CODE`, `POSITION NAME`, `KODE JOB GRADE`) dan definitif (`JOB CODE DEF`, `POSITION NAME DEF`, `JOB GRADE DEF`) diproses terpisah. Penentuan posisi current dan Vacancy Priority tidak menggunakan jabatan definitif asal untuk menggantikan posisi saat ini.
- Vacancy Priority menghitung keterisian dari seluruh karyawan aktif berdasarkan penempatan sekarang (`JOB CODE` + `POSITION NAME` + kode organisasi), termasuk penugasan/non-definitif. Aktual definitif pada Gap Formasi tetap seperti sebelumnya.
- Ringkasan SDM menambahkan distribusi Pendidikan Terakhir dan Agama; statistik mengikuti level/filter/pencarian yang aktif.
- Data SOTK Wilayah dan Area dipertahankan; `POSITION` merupakan metadata tambahan.

Lihat `QA_REPORT_REVISI_JOB_CODE_POSITION_NAME.md` untuk aturan matching terbaru dan hasil uji logika.
