export type CurrencyUnit = "toman" | "rial";
export function formatMoney(value: number | string | null | undefined, unit: CurrencyUnit = (document.documentElement.dataset.currencyUnit as CurrencyUnit) || "toman") {
  const amount = Number(value ?? 0);
  const shown = Math.round((Number.isFinite(amount) ? amount : 0) * (unit === "rial" ? 10 : 1));
  return `${shown.toLocaleString("fa-IR")} ${unit === "rial" ? "ریال" : "تومان"}`;
}
export function currencyInputValue(storedToman: number | null | undefined, unit: CurrencyUnit) {
  const value = Number(storedToman ?? 0);
  return unit === "rial" ? value * 10 : value;
}
export function currencyStorageValue(displayed: number, unit: CurrencyUnit) {
  if (!Number.isFinite(displayed) || !Number.isInteger(displayed)) return null;
  if (unit === "rial" && displayed % 10 !== 0) return null;
  return unit === "rial" ? displayed / 10 : displayed;
}
export function currencyLabel(unit: CurrencyUnit) { return unit === "rial" ? "ریال" : "تومان"; }
