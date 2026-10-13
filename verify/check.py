#!/usr/bin/env python3
"""Verifikasi mandiri QRIS — tanpa dependensi eksternal.

Mengecek payload QRIS (statis maupun dinamis) secara menyeluruh:
  1. Header "000201" (Payload Format Indicator)
  2. Tag wajib ada
  3. Nilai tag penting valid (Point of Initiation, MCC 4 digit)
  4. Ada Merchant Account Information (tag 26-51)
  5. CRC16 cocok
  6. Round-trip: konversi lalu decode balik masih konsisten

Pakai:
  python verify/check.py --demo --amount 1
  python verify/check.py --qris "00020101021226..."
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# biar bisa import core dari root project
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qris_dynamic import crc16_ccitt, parse_qris, parse_tlv, to_dynamic, validate  # noqa: E402

# Payload contoh (QRIS dinamis milik merchant demo).
DEMO_QRIS = (
    "00020101021226750023ID.CO.BANKSAMPOERNA.WWW01189360052300000186340215ID20260001947850303UBE"
    "51450015ID.OR.GPNQR.WWW0215ID20265354496420303UBE520460105303360540720000005802ID"
    "5923STUDIO KREASI PAYMENT..6015JAKARTA SELATAN610512430623301161791377414931564070944305600763047750"
)


def check(qris: str) -> list[str]:
    """Jalankan semua cek, kembalikan daftar masalah (kosong = lolos)."""
    problems: list[str] = []

    # 1. header
    if not qris.startswith("000201"):
        problems.append('header harus diawali "000201"')

    elements = parse_tlv(qris)
    tags = {tag: value for tag, value in elements}

    # 2. tag wajib
    for req in ["00", "01", "52", "53", "58", "59", "60", "63"]:
        if req not in tags:
            problems.append(f"tag wajib {req} tidak ada")

    # 3. nilai tag penting
    if tags.get("01") not in ("11", "12", None):
        problems.append(f'Point of Initiation Method tidak valid: "{tags["01"]}"')
    mcc = tags.get("52")
    if mcc is not None and not (len(mcc) == 4 and mcc.isdigit()):
        problems.append(f'Merchant Category Code tidak valid: "{mcc}"')

    # 4. merchant account info
    if not any(26 <= int(t) <= 51 for t, _ in elements if t.isdigit()):
        problems.append("tidak ada Merchant Account Information (tag 26-51)")

    # 5. CRC
    if crc16_ccitt(qris[:-4]) != qris[-4:].upper():
        problems.append(f"CRC tidak cocok (tertulis {qris[-4:].upper()}, "
                        f"seharusnya {crc16_ccitt(qris[:-4])})")

    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description="Verifikasi mandiri payload QRIS.")
    parser.add_argument("--qris", help="string QRIS langsung")
    parser.add_argument("--file", help="file teks berisi string QRIS")
    parser.add_argument("--demo", action="store_true", help="pakai data contoh bawaan")
    parser.add_argument("--amount", default="1",
                        help="nominal untuk uji round-trip (default: 1)")
    args = parser.parse_args()

    if args.qris:
        qris = args.qris.strip()
    elif args.file:
        qris = Path(args.file).read_text(encoding="utf-8").strip()
    elif args.demo:
        qris = DEMO_QRIS
    else:
        parser.error("pilih sumber: --qris, --file, atau --demo")

    print("=== payload awal ===")
    print(qris)

    problems = check(qris)
    print("\n=== cek struktur & CRC ===")
    if problems:
        for p in problems:
            print(" ❌", p)
    else:
        print(" ✅ struktur, tag wajib, MCC, dan CRC semua valid")

    print("\n=== ringkasan ===")
    print(" ", parse_qris(qris))
    print("  validate() :", validate(qris))

    # round-trip: konversi ke nominal target lalu cek hasilnya
    dynamic = to_dynamic(qris, args.amount)
    print(f"\n=== round-trip (amount={args.amount}) ===")
    print(dynamic)
    rt_problems = check(dynamic)
    rt = parse_qris(dynamic)
    ok = not rt_problems and rt["amount"] == str(args.amount)
    if rt_problems:
        for p in rt_problems:
            print(" ❌", p)
    print(" nominal hasil :", rt["amount"])
    print(" ROUND-TRIP    :", "LOLOS ✅" if ok else "GAGAL ❌")

    sys.exit(0 if not problems and ok else 1)


if __name__ == "__main__":
    main()
