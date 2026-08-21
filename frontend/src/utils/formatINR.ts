/**
 * Financial formatter for Indian Rupee (INR) denomination standards:
 * - Thousands (K): ₹1.2K
 * - Lakhs (L): ₹1.23L
 * - Crores (Cr): ₹1.23Cr
 */

export function formatINR(value: number | null | undefined): string {
  if (value == null || isNaN(Number(value))) return '₹0';

  const num = Number(value);
  const abs = Math.abs(num);
  const sign = num < 0 ? '-' : '';

  if (abs >= 1_00_00_000) {
    return `${sign}₹${(abs / 1_00_00_000).toFixed(2)}Cr`;
  }
  if (abs >= 1_00_000) {
    return `${sign}₹${(abs / 1_00_000).toFixed(2)}L`;
  }
  if (abs >= 1_000) {
    return `${sign}₹${(abs / 1_000).toFixed(1)}K`;
  }
  return `${sign}₹${Math.round(abs).toLocaleString('en-IN')}`;
}

/**
 * Axis tick formatter providing short, readable labels for charts
 */
export function formatINRAxis(value: number | string | null | undefined): string {
  if (value == null || isNaN(Number(value))) return '₹0';

  const num = Number(value);
  const abs = Math.abs(num);
  const sign = num < 0 ? '-' : '';

  if (abs >= 1_00_00_000) {
    return `${sign}₹${(abs / 1_00_00_000).toFixed(1)}Cr`;
  }
  if (abs >= 1_00_000) {
    return `${sign}₹${(abs / 1_00_000).toFixed(1)}L`;
  }
  if (abs >= 1_000) {
    return `${sign}₹${(abs / 1_000).toFixed(1)}K`;
  }
  return `${sign}₹${Math.round(abs)}`;
}
