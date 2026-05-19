export function formatTRY(value: number): string {
  return (
    value.toLocaleString("tr-TR", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }) + " ₺"
  );
}

export function formatPercent(value: number, fractionDigits = 0): string {
  return (
    "%" +
    value.toLocaleString("tr-TR", {
      minimumFractionDigits: fractionDigits,
      maximumFractionDigits: fractionDigits,
    })
  );
}
