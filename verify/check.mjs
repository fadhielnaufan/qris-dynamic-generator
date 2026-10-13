/**
 * Cross-check: membandingkan output convertQRIS (paket npm referensi)
 * dengan output converter Python. Dipakai untuk memastikan hasil identik.
 *
 * Pakai:
 *   node verify/check.mjs <amount>
 *   node verify/check.mjs <amount> "<python_output_payload>"
 *
 * Contoh: node verify/check.mjs 10000 "00020101021226..."
 */
import { convertQRIS, validateQRIS, parseQRIS } from "@nurafandito/qris-static-dynamic-core";

// Payload contoh (QRIS dinamis merchant demo).
const SRC =
  "00020101021226750023ID.CO.BANKSAMPOERNA.WWW01189360052300000186340215ID20260001947850303UBE" +
  "51450015ID.OR.GPNQR.WWW0215ID20265354496420303UBE520460105303360540720000005802ID" +
  "5923STUDIO KREASI PAYMENT..6015JAKARTA SELATAN610512430623301161791377414931564070944305600763047750";

const amount = Number(process.argv[2] ?? 10000);
const pythonOutput = process.argv[3];

const reference = convertQRIS(SRC, { amount });

console.log("SRC valid     :", JSON.stringify(validateQRIS(SRC)));
console.log("REF (npm)     :", reference);
console.log("REF valid     :", JSON.stringify(validateQRIS(reference)));
console.log("REF parse     :", JSON.stringify(parseQRIS(reference)));

if (pythonOutput) {
  console.log("PY  (python)  :", pythonOutput);
  console.log("IDENTIK       :", pythonOutput === reference ? "YA ✅" : "TIDAK ❌");
  if (pythonOutput !== reference) process.exitCode = 1;
}
