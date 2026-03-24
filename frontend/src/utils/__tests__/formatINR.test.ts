import { formatINR, formatINRAxis } from '../formatINR';

describe('formatINR', () => {
  it('should format thousands with K', () => {
    expect(formatINR(1000)).toBe('₹1.0K');
    expect(formatINR(5500)).toBe('₹5.5K');
  });

  it('should format lakhs with L', () => {
    expect(formatINR(100000)).toBe('₹1.00L');
    expect(formatINR(123456)).toBe('₹1.23L');
  });

  it('should format crores with Cr', () => {
    expect(formatINR(10000000)).toBe('₹1.00Cr');
    expect(formatINR(123456789)).toBe('₹1.23Cr');
  });

  it('should handle small values without suffix', () => {
    expect(formatINR(500)).toBe('₹500');
    expect(formatINR(999)).toBe('₹999');
  });

  it('should handle negative values', () => {
    expect(formatINR(-10000)).toBe('-₹10.0K');
    expect(formatINR(-1000000)).toBe('-₹10.00L');
  });

  it('should handle zero', () => {
    expect(formatINR(0)).toBe('₹0');
  });

  it('should handle null and NaN', () => {
    expect(formatINR(null as any)).toBe('₹0');
    expect(formatINR(NaN)).toBe('₹0');
  });

  it('should handle decimal values', () => {
    expect(formatINR(1234.56)).toBe('₹1.23K');
    expect(formatINR(1234567.89)).toBe('₹12.35L');
  });
});

describe('formatINRAxis', () => {
  it('should format for axis labels', () => {
    expect(formatINRAxis(100000)).toBe('₹1.0L');
    expect(formatINRAxis(1000000)).toBe('₹10.0L');
  });

  it('should handle string inputs', () => {
    expect(formatINRAxis('100000')).toBe('₹1.0L');
    expect(formatINRAxis('1000')).toBe('1.0K');
  });

  it('should handle null and undefined', () => {
    expect(formatINRAxis(null)).toBe('₹0');
    expect(formatINRAxis(undefined)).toBe('₹0');
  });
});
