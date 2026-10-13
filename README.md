# QRIS Dynamic Generator

Ubah **QRIS statis** (tanpa nominal) jadi **QRIS dinamis** (nominal tetap) — tinggal scan, langsung muncul jumlah yang harus dibayar.

Cocok buat toko, booth, atau penjual online yang pengen checkout lebih cepat dan bebas salah ketik nominal.

---

## Apa yang dilakuin

QRIS itu sebenernya cuma **teks panjang** yang disusun dari potongan-potongan kecil dengan format:

```
[2 digit tag][2 digit panjang][isi]
```

Contoh tag `54` (nominal) sebesar `10000` ditulis: `5405 10000` — tag `54`, panjang `05`, isi `10000`.

Tool ini:
1. **Membaca** struktur QRIS dari string, file, atau gambar QR
2. **Mengubah** tipe statis (`11`) jadi dinamis (`12`)
3. **Menyisipkan** nominal (tag `54`)
4. **Menghitung ulang CRC** supaya QR tetap valid
5. **Membuat gambar QR baru** siap pakai

---

## Instalasi

```bash
git clone https://github.com/<username>/qris-dynamic.git
cd qris-dynamic
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Cara pakai

### Pakai QRIS string langsung

```bash
python cli.py --qris "00020101021126..." --amount 10000
```

### Baca QRIS dari file teks

```bash
python cli.py --file qris.txt --amount 25000 --out bayar.png
```

### Ambil QRIS dari gambar (butuh zxing-cpp + pillow)

```bash
python cli.py --image qris.jpg --amount 1 --out bayar.png
```

### Mode demo (pakai data contoh bawaan)

```bash
python cli.py --demo --amount 10000
```

### Cek validitas tanpa generate gambar

```bash
python cli.py --qris "00020101021126..." --validate
```

### Decode gambar QR jadi teks

```bash
python cli.py --image qris.jpg --decode
```

---

## Opsi

| Opsi | Keterangan |
|---|---|
| `--qris` | String QRIS langsung |
| `--file` | File teks berisi string QRIS |
| `--image` | File gambar QR (butuh `zxing-cpp` + `pillow`) |
| `--demo` | Pakai data contoh bawaan |
| `--amount` | Nominal yang mau ditagihkan, contoh `10000` |
| `--out` | Path gambar hasil (default: `qris_dynamic_<amount>.png`) |
| `--decode` | Hanya decode gambar QR jadi teks |
| `--validate` | Hanya cek validitas struktur + CRC |

---

## Pakai sebagai modul

```python
from qris_dynamic import to_dynamic, validate, parse_qris

qris_statis = "00020101021126..."

# Ubah jadi dinamis
dinamis = to_dynamic(qris_statis, 10000)

# Cek validitas
print(validate(dinamis))
# {'valid': True, 'errors': []}

# Lihat ringkasan
print(parse_qris(dinamis))
# {'method': 'dinamis', 'amount': '10000', 'merchant_name': '...', ...}
```

---

## Struktur project

```
qris-dynamic/
├── cli.py              # Command line interface
├── qris_dynamic.py     # Core: parser TLV, CRC16, konversi, validasi
├── requirements.txt
└── verify/
    └── check.mjs       # Cross-check hasil vs paket npm referensi
```

---

## Verifikasi

Hasil konversi dicek dengan membandingkan **byte-per-byte** terhadap paket npm referensi [`@nurafandito/qris-static-dynamic-core`](https://github.com/nurafandito/qris-static-dynamic-core).

```bash
cd verify
npm install
python ../cli.py --demo --amount 1 --out /tmp/out.png   # lihat payload
node check.mjs 1 "<payload_dari_python>"
```

Kalau output ditandai `IDENTIK ✅`, hasil converter ini sama persis dengan referensi.

---

## Catatan penting ⚠️

- Tool ini **mengubah nominal**, **bukan mengubah tujuan pembayaran**. Dana tetap masuk ke merchant yang tertera di QRIS asli.
- **Jangan pernah push** gambar QRIS asli atau hasil generate ke repo publik — itu data pembayaran. Sudah ditutup oleh `.gitignore` (`*.png`, `*.jpg`, `*.txt`).
- Pakai hanya untuk keperluan yang sah: QRIS milik sendiri, testing, atau simulasi.

---

## Lisensi

MIT
