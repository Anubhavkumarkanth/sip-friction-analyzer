/**
 * Smart Indian Rupee formatter
 * ₹1,23,456 → ₹1.23L
 * ₹1,23,45,678 → ₹1.23Cr
 */
export function formatINR(value: number): string {
  if (value == null || isNaN(value)) return '₹0';

  const abs = Math.abs(value);
  const sign = value < 0 ? '-' : '';

  if (abs >= 1_00_00_000) {
    return `${sign}₹${(abs / 1_00_00_000).toFixed(2)}Cr`;
  }
  if (abs >= 1_00_000) {
    return `${sign}₹${(abs / 1_00_000).toFixed(2)}L`;
  }
  if (abs >= 1_000) {
    return `${sign}₹${(abs / 1_000).toFixed(1)}K`;
  }
  return `${sign}₹${Math.round(abs)}`;
}

/**
 * Compact axis label (no ₹ prefix, shorter)
 */
export function formatINRAxis(value: number | string | null | undefined): string {
  if (value == null || isNaN(Number(value))) return '₹0';

  const numValue = Number(value);
  const abs = Math.abs(numValue);
  const sign = numValue < 0 ? '-' : '';

  if (abs >= 1_00_00_000) {
    return `${sign}₹${(abs / 1_00_00_000).toFixed(1)}Cr`;
  }
  if (abs >= 1_00_000) {
    return `${sign}₹${(abs / 1_00_000).toFixed(1)}L`;
  }
  if (abs >= 1_000) {
    return `${sign}${(abs / 1_000).toFixed(1)}K`;
  }
  return `${sign}₹${Math.round(abs)}`;
}
