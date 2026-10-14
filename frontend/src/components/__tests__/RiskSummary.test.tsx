import { render } from '@testing-library/react';
import RiskSummary from '../RiskSummary';

describe('RiskSummary', () => {
  const props = { volatilityPct: 15, worst: 1_176_000, best: 19_200_000, median: 4_625_000 };

  it('writes the volatility as plain text, not as raw math notation', () => {
    const { container } = render(<RiskSummary {...props} />);
    const text = container.textContent ?? '';
    expect(text).toContain('σ = 15%');
    expect(text).not.toContain('$');
    expect(text).not.toContain('\\sigma');
    expect(text).not.toContain('\\%');
  });

  it('shows the worst case, the best case and the median in rupees', () => {
    const { container } = render(<RiskSummary {...props} />);
    const text = container.textContent ?? '';
    expect(text).toContain('₹11.76L');
    expect(text).toContain('₹1.92Cr');
    expect(text).toContain('₹46.25L');
  });

  it('keeps real spaces around the figures', () => {
    const { container } = render(<RiskSummary {...props} />);
    expect(container.textContent).toContain('spans from ₹11.76L to ₹1.92Cr.');
    expect(container.textContent).toContain('expectation is ₹46.25L.');
  });

  it('keeps one decimal when the volatility is not a whole percentage', () => {
    const { container } = render(<RiskSummary {...props} volatilityPct={12.5} />);
    expect(container.textContent).toContain('σ = 12.5%');
  });

  it('does not show a long tail of decimals for a floating-point percentage', () => {
    // 0.15 * 100 is 15.000000000000002 in floating point.
    const { container } = render(<RiskSummary {...props} volatilityPct={0.15 * 100} />);
    expect(container.textContent).toContain('σ = 15%');
    expect(container.textContent).not.toContain('15.0');
  });
});
