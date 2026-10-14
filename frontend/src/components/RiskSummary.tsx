import { FC } from 'react';
import { formatINR } from '../utils/formatINR';

interface RiskSummaryProps {
  /** The volatility the shown results were produced with, as a percentage (15 means 15%). */
  volatilityPct: number;
  worst: number;
  best: number;
  median: number;
}

/**
 * One-sentence reading of a Monte Carlo result.
 *
 * Plain text on purpose: this page has no math renderer, so "$\sigma = 15\%$" was shown to people exactly as written.
 * The spaces around the figures are real spaces (not margins), so the sentence also reads correctly to a screen reader.
 */
const RiskSummary: FC<RiskSummaryProps> = ({ volatilityPct, worst, best, median }) => (
  <p style={{ marginTop: '1rem', lineHeight: '1.8', color: 'var(--text-main)' }}>
    Across 1,000 stochastic market realizations with annual standard deviation σ = {Number(volatilityPct.toFixed(1))}%, terminal
    portfolio wealth spans from <strong style={{ color: 'var(--danger)' }}>{formatINR(worst)}</strong> to{' '}
    <strong style={{ color: 'var(--success)' }}>{formatINR(best)}</strong>. The 50th percentile (median) expectation is{' '}
    <strong style={{ color: 'var(--accent-primary)' }}>{formatINR(median)}</strong>.
  </p>
);

export default RiskSummary;
