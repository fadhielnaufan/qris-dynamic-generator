"""Inti konversi QRIS statis -> dinamis.

QRIS mengikuti standar EMVCo TLV:
    [2 digit tag][2 digit panjang][isi]

Modul ini menyediakan:
  - parse_tlv / build_tlv  : baca & susun ulang struktur TLV
  - crc16_ccitt            : checksum CRC16-CCITT (poly 0x1021, init 0xFFFF)
  - to_dynamic             : ubah QRIS statis jadi dinamis dengan nominal tetap
  - validate               : cek struktur + CRC
"""
from __future__ import annotations

__all__ = ["parse_tlv", "build_tlv", "crc16_ccitt", "to_dynamic", "validate", "parse_qris"]

# Tag yang dikelola saat konversi: dihapus dulu lalu disisipkan ulang.
MANAGED_TAGS = {"54", "55", "56", "57", "63"}


def crc16_ccitt(text: str) -> str:
    """CRC16-CCITT (poly 0x1021, init 0xFFFF) sebagai string hex 4 digit.

    Dihitung per byte UTF-8, sesuai definisi EMVCo.
    """
    crc = 0xFFFF
    for b in text.encode("utf-8"):
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f"{crc:04X}"


def parse_tlv(data: str) -> list[tuple[str, str]]:
    """Ubah string TLV jadi daftar (tag, value).

    Berhenti kalau menemukan data yang tidak sesuai format (tidak melempar error),
    supaya sisa payload yang valid tetap terbaca.
    """
    elements: list[tuple[str, str]] = []
    i = 0
    while i + 4 <= len(data):
        tag = data[i:i + 2]
        length_str = data[i + 2:i + 4]
        if not (tag.isdigit() and length_str.isdigit()):
            break
        length = int(length_str)
        value = data[i + 4:i + 4 + length]
        elements.append((tag, value))
        i += 4 + length
    return elements


def build_tlv(elements: list[tuple[str, str]]) -> str:
    """Susun daftar (tag, value) jadi string TLV. Panjang dihitung per byte."""
    parts = []
    for tag, value in elements:
        byte_len = len(value.encode("utf-8"))
        if byte_len > 99:
            raise ValueError(f"Tag {tag} sepanjang {byte_len} byte melebihi batas 99")
        parts.append(f"{tag}{byte_len:02d}{value}")
    return "".join(parts)


def to_dynamic(qris: str, amount) -> str:
    """Ubah QRIS statis jadi dinamis dengan nominal tetap.

    Langkah:
      1. Parse TLV
      2. Tag 01: "11" (statis) -> "12" (dinamis)
      3. Sisip tag 54 (nominal) sebelum tag 58 (Country Code)
      4. Hitung ulang CRC
    """
    amount_str = str(amount)
    if not amount_str or _to_number(amount_str) <= 0:
        raise ValueError("nominal harus berupa angka positif")

    elements = parse_tlv(qris)
    if not any(tag == "01" for tag, _ in elements):
        raise ValueError("bukan QRIS yang valid (tag 01 tidak ditemukan)")

    result: list[tuple[str, str]] = []
    amount_inserted = False

    for tag, value in elements:
        if tag in MANAGED_TAGS:
            continue
        if tag == "01":
            result.append(("01", "12"))          # statis -> dinamis
            continue
        if tag == "58" and not amount_inserted:  # sisip sebelum Country Code
            result.append(("54", amount_str))
            amount_inserted = True
        result.append((tag, value))

    if not amount_inserted:  # jaga-jaga kalau tag 58 tidak ada
        result.append(("54", amount_str))

    without_crc = build_tlv(result)
    crc_input = without_crc + "6304"
    return crc_input + crc16_ccitt(crc_input)


def validate(qris: str) -> dict:
    """Cek struktur & CRC sebuah string QRIS. Kembalikan dict {valid, errors}."""
    errors: list[str] = []
    qris = (qris or "").strip()

    if not qris:
        return {"valid": False, "errors": ["string QRIS kosong"]}
    if not qris.startswith("000201"):
        errors.append('harus diawali "000201" (Payload Format Indicator)')
    if len(qris) < 20:
        return {"valid": False, "errors": errors + ["string QRIS terlalu pendek"]}

    declared = qris[-4:].upper()
    calculated = crc16_ccitt(qris[:-4])
    if declared != calculated:
        errors.append(f"CRC tidak cocok: seharusnya {calculated}, tertulis {declared}")

    elements = parse_tlv(qris)
    if not elements:
        return {"valid": False, "errors": errors + ["gagal parse TLV"]}

    tags = {tag: value for tag, value in elements}
    for req in ["00", "01", "52", "53", "58", "59", "60", "63"]:
        if req not in tags:
            errors.append(f"tag wajib {req} tidak ditemukan")

    if tags.get("01") not in (None, "11", "12"):
        errors.append(f'Point of Initiation Method tidak valid: "{tags["01"]}"')

    mcc = tags.get("52")
    if mcc is not None and not (len(mcc) == 4 and mcc.isdigit()):
        errors.append(f'Merchant Category Code tidak valid: "{mcc}"')

    if not any(26 <= int(tag) <= 51 for tag, _ in elements if tag.isdigit()):
        errors.append("tidak ada Merchant Account Information (tag 26-51)")

    return {"valid": not errors, "errors": errors}


def parse_qris(qris: str) -> dict:
    """Ringkas field penting dari payload QRIS jadi dict yang mudah dibaca."""
    tags = {tag: value for tag, value in parse_tlv(qris)}
    method = tags.get("01")
    return {
        "method": "dinamis" if method == "12" else "statis",
        "amount": tags.get("54"),
        "currency": tags.get("53"),
        "merchant_name": tags.get("59"),
        "merchant_city": tags.get("60"),
        "postal_code": tags.get("61"),
        "country": tags.get("58"),
        "mcc": tags.get("52"),
        "crc": tags.get("63"),
    }


def _to_number(s: str) -> float:
    try:
        return float(s)
    except (TypeError, ValueError):
        return 0.0
