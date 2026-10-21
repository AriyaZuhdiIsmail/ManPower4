# Laporan Validasi Revisi Power_updated

Tanggal pemeriksaan: 21 Oktober 2026.

## File yang diubah

- `app.js`: pembacaan `POSITION NAME` / `POSITION NAME DEF`, pemasangan pasangan grade saat ini dan definitif, resolver tingkat jabatan cabang, pemetaan Cabang berdasarkan Position Name, dan tampilan kolom deteksi posisi pada Validasi Mapping SOTK.
- `features.js`: kompatibilitas aturan dengan skema `POSITION_GRADE_RULES` terbaru; tampilan Position Name definitif dan deteksi tingkatnya pada Monitoring Non-Definitif level Cabang.
- `data.js`: dibangun ulang dari master terbaru, termasuk `POSITION`, `POSITION_GRADE_RULES`, dan `POSITION_GRADE_TIER_MAP`.
- `tools/build_data.py`: dibarui agar membaca skema master terbaru, menambahkan kolom tampilan `POSITION`, dan memuat kedua tabel aturan tingkat jabatan.
- `source_data/SOTK_MASTER_REVISI_CABANG_SAJA_POSITION_NAME_GRADE_TIER.xlsx`: salinan sumber master yang digunakan untuk membangun preload.

`index.html`, `styles.css`, logo, dan library tetap sama dengan ZIP sumber. Tidak dilakukan redesign pada layout atau tema.

## Validasi sumber SOTK

- `SOTK_WILAYAH`: 49 baris.
- `SOTK_AREA`: 45 baris.
- `SOTK_CABANG`: 1.784 baris sumber, total 912 formasi.
- `UNIT_MASTER_CABANG`: 394 outlet/unit aktif.
- `POSITION_GRADE_RULES`: 20 baris.
- `POSITION_GRADE_TIER_MAP`: 37 baris.
- Tidak ditemukan baris `Manager Bisnis` pada UPC Mall Basura di master hasil koreksi. File pembanding SOTK cabang yang lebih lama masih menjumlah 919 formasi; master final yang sudah menghapus 7 formasi yang salah di UPC Mall Basura menjadi 912 dan digunakan sebagai acuan aplikasi.
- Dibandingkan dengan preload awal: seluruh nilai dan jumlah baris SOTK Wilayah/Area pada kolom lama identik; hanya kolom tambahan `POSITION` yang ditambahkan sebagai metadata tampilan.

## Pengujian regresi Kantor Wilayah/Area

Dengan dataset uji yang sama, hasil pencocokan 108 karyawan di level Wilayah/Area sebelum dan sesudah revisi dibandingkan berdasarkan status mapping, key formasi, grade, status grade yang mengikuti SOTK, catatan mapping, dan formasi. **Jumlah perbedaan: 0.** Tidak ada error runtime pada kedua versi saat pengujian.

## Pengujian resolver jabatan Cabang

- `JOB CODE = AO`, `POSITION NAME = Senior Account Officer 2`, `KODE JOB GRADE = 7` terdeteksi sebagai `SAO`, tingkat 2, dan dipetakan ke key formasi `12586|SAO` pada kasus uji.
- Dari workbook karyawan, 32 baris aktif memiliki `POSITION NAME DEF` sebagai Senior Account Officer: 25 tingkat 1 dan 7 tingkat 2. Salah satu contoh memiliki `JOB CODE DEF = AO`, nama posisi `Senior Account Officer 2`, dan `JOB GRADE DEF = Grade 7`; hasil pemetaan adalah SAO tingkat 2 dengan grade cocok.
- Pengujian eksplisit juga berhasil untuk AO 3/JG 4, Penaksir Madya 2/JG 9, Penaksir Muda 2/JG 7, Pengelola Agunan 3/JG 4, Pengelola Marhun 3/JG 4, dan AMNG 2/JG 9.
- Kasus sengaja dibuat tidak cocok: nama `Senior Account Officer 2` dengan grade 8 tetap terpetakan sebagai SAO tingkat 2, grade aktual 8 tidak ditimpa, dan konflik ditandai `MISMATCH`.

## Pendidikan, Agama, Person Grade, dan End Status

Hasil uji logika pada 923 baris aktif (identitas disimulasikan hanya di memori pengujian untuk mengatasi kolom identitas kosong pada file yang diberikan):

- Pendidikan terakhir tersedia: 880 baris; 43 baris tidak memiliki jenjang pendidikan.
- Agama tersedia: 923 baris.
- Filter Person Grade tersedia pada Monitoring Karyawan dan benar-benar memfilter data: pada uji level Cabang, data berubah dari 815 baris menjadi 162 baris saat memilih Person Grade 7.
- Karyawan non-definitif: 441 baris; seluruhnya memiliki TMT Position dan berhasil memperoleh End Status.
- Uji kalender: 31 Januari 2026 + 3 bulan = 30 April 2026.
- TMT kosong menghasilkan End Status kosong; karyawan definitif tidak mendapat End Status otomatis.

Grafik Dashboard, kolom pendidikan/agama di Monitoring Karyawan, filter Person Grade, kolom Position, dan kolom deteksi tingkatan pada tampilan Cabang ter-render pada uji browser. Pemeriksaan JavaScript menghasilkan **0 page error dan 0 error console**.

## Batasan pengujian

File `Data karyawan - Copy(1).xlsx` yang diberikan memiliki `NIK PENDEK` kosong pada seluruh baris dan `NAMA` kosong pada seluruh baris. Karena validasi upload pada aplikasi mensyaratkan kedua kolom itu, file persis seperti terlampir akan ditolak ketika diunggah ke website. Validasi ini sengaja tidak dilonggarkan dan nilai identitas tidak diubah pada file sumber. Untuk menguji logika pemetaan pada browser, ID dan nama dummy digunakan hanya di memori pengujian; tidak disimpan ke workbook atau dimasukkan ke website.

Pengujian dilakukan dengan Chromium headless terhadap alur render dan logika utama; screenshot perbandingan visual otomatis untuk setiap menu tidak tersedia. Namun, `index.html` dan `styles.css` tetap identik byte-per-byte dengan ZIP awal.
