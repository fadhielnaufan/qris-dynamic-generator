#!/usr/bin/env python3
"""QRIS static -> dynamic CLI.

Contoh:
  # Pakai QRIS string langsung
  python cli.py --qris "00020101021126..." --amount 10000

  # Baca QRIS dari file teks
  python cli.py --file qris.txt --amount 25000 --out bayar.png

  # Ambil QRIS dari gambar (butuh zxing-cpp + pillow)
  python cli.py --image qris.jpg --amount 1 --out bayar.png

  # Mode demo: pakai data contoh bawaan
  python cli.py --demo --amount 10000

  # Cek validitas saja tanpa generate gambar
  python cli.py --qris "00020101021126..." --validate

  # Decode gambar QR jadi teks
  python cli.py --image qris.jpg --decode
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from qris_dynamic import crc16_ccitt, parse_qris, to_dynamic, validate

# Payload contoh (QRIS dinamis milik merchant demo).
DEMO_QRIS = (
    "00020101021226750023ID.CO.BANKSAMPOERNA.WWW01189360052300000186340215ID20260001947850303UBE"
    "51450015ID.OR.GPNQR.WWW0215ID20265354496420303UBE520460105303360540720000005802ID"
    "5923STUDIO KREASI PAYMENT..6015JAKARTA SELATAN610512430623301161791377414931564070944305600763047750"
)


def decode_image(path: str) -> str:
    """Decode gambar QR jadi string."""
    try:
        import zxingcpp
        from PIL import Image
    except ImportError:
        sys.exit(
            "Butuh paket 'zxing-cpp' dan 'pillow' untuk decode gambar.\n"
            "Install: pip install zxing-cpp pillow"
        )

    results = zxingcpp.read_barcodes(Image.open(path))
    if not results:
        sys.exit(f"Tidak ada QR code yang terbaca dari {path}")
    return results[0].text


def get_qris(args) -> str:
    if args.qris:
        return args.qris.strip()
    if args.file:
        return Path(args.file).read_text(encoding="utf-8").strip()
    if args.image:
        return decode_image(args.image)
    if args.demo:
        return DEMO_QRIS
    sys.exit("Pilih sumber QRIS: --qris, --file, --image, atau --demo")


def make_qr_image(payload: str, out_path: str) -> None:
    try:
        import qrcode
    except ImportError:
        sys.exit("Butuh paket 'qrcode'. Install: pip install qrcode[pil]")
    qrcode.make(payload).save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ubah QRIS statis jadi QRIS dinamis (nominal tetap).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    src = parser.add_argument_group("sumber QRIS")
    src.add_argument("--qris", help="string QRIS langsung")
    src.add_argument("--file", help="file teks berisi string QRIS")
    src.add_argument("--image", help="file gambar QR (butuh zxing-cpp + pillow)")
    src.add_argument("--demo", action="store_true", help="pakai data contoh bawaan")

    parser.add_argument("--amount", help="nominal yang mau ditagihkan, contoh: 10000")
    parser.add_argument("--out", help="path gambar QR hasil (default: qris_dynamic_<amount>.png)")
    parser.add_argument("--decode", action="store_true", help="hanya decode gambar QR jadi teks")
    parser.add_argument("--validate", action="store_true", help="hanya cek validitas QRIS")

    args = parser.parse_args()

    if args.decode:
        if not args.image:
            sys.exit("--decode butuh --image")
        print(decode_image(args.image))
        return

    qris = get_qris(args)

    if args.validate:
        result = validate(qris)
        print("valid:", result["valid"])
        for err in result["errors"]:
            print(" -", err)
        print("ringkas:", parse_qris(qris))
        return

    if not args.amount:
        sys.exit("Butuh --amount (nominal). Contoh: --amount 10000")

    dynamic = to_dynamic(qris, args.amount)

    out = args.out or f"qris_dynamic_{args.amount}.png"
    make_qr_image(dynamic, out)

    print("payload :", dynamic)
    print("crc     :", dynamic[-4:], "(cek:", crc16_ccitt(dynamic[:-4]), ")")
    print("ringkas :", parse_qris(dynamic))
    print("tersimpan:", out)


if __name__ == "__main__":
    main()
