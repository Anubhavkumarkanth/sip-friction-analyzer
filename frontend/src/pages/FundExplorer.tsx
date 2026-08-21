import React, { useState, useEffect, useCallback, FC, ChangeEvent } from 'react';
import { Search, Filter, ShieldAlert, Globe, ExternalLink, TrendingUp, BarChart2, X, PlusCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import GlassCard from '../components/ui/GlassCard';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { fundsAPI, handleApiError } from '../services/api';
import { useDebounce } from '../hooks/useDebounce';
import { Fund } from '../types';
import './FundExplorer.css';

interface FundCardProps {
  fund: Fund;
  index: number;
  isTopPick: boolean;
  onAnalyze: (fund: Fund) => void;
  onCompareSelect: (fund: Fund) => void;
  isSelectedForCompare: boolean;
}

const FundCard: FC<FundCardProps> = ({
  fund,
  index,
  isTopPick,
  onAnalyze,
  onCompareSelect,
  isSelectedForCompare,
}) => (
  <GlassCard
    className={`fund-card ${isSelectedForCompare ? 'selected-for-compare' : ''}`}
    style={{ animationDelay: `${index * 80}ms` }}
  >
    {isTopPick && <div className="top-pick-badge">🏆 Top Pick</div>}

    <div className="fund-header">
      <h3 className="fund-name">{fund.name}</h3>
      <span className="fund-category">{fund.category}</span>
    </div>

    <div className="fund-metrics">
      <div className="metric">
        <span className="metric-label">3Y Return</span>
        <span className="metric-value text-accent">{fund.return_3y}%</span>
      </div>
      <div className="metric">
        <span className="metric-label">5Y Return</span>
        <span className="metric-value text-accent">{fund.return_5y}%</span>
      </div>
      <div className="metric">
        <span className="metric-label">Exp. Ratio</span>
        <span className="metric-value">{fund.expense_ratio}%</span>
      </div>
    </div>

    <div className="fund-tags">
      <div className="tag">
        <ShieldAlert size={12} /> {fund.risk_level}
      </div>
      <div className="tag">
        <Globe size={12} /> {fund.platform}
      </div>
    </div>

    <div className="fund-actions" style={{ display: 'flex', gap: '8px', marginTop: '1rem', flexWrap: 'wrap' }}>
      <a
        href={fund.invest_url}
        target="_blank"
        rel="noopener noreferrer"
        className="invest-btn"
        style={{ flex: 1, minWidth: '100px' }}
      >
        Invest Now <ExternalLink size={14} />
      </a>
      <Button
        variant="secondary"
        onClick={() => onAnalyze(fund)}
        style={{ flex: 1, minWidth: '130px', padding: '0.6rem' }}
      >
        <TrendingUp size={14} /> Analyze SIP
      </Button>
      <Button
        variant={isSelectedForCompare ? 'primary' : 'outline'}
        onClick={() => onCompareSelect(fund)}
        style={{ flex: 1, minWidth: '100px', padding: '0.6rem' }}
        className={isSelectedForCompare ? 'bg-accent' : ''}
      >
        <BarChart2 size={14} /> {isSelectedForCompare ? 'Selected' : 'Compare'}
      </Button>
    </div>
  </GlassCard>
);


const PLATFORMS = ['All Platforms', 'Groww', 'Zerodha', 'Angel One'];

const FundExplorer: FC = () => {
  const navigate = useNavigate();
  const [funds, setFunds] = useState<Fund[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [compareList, setCompareList] = useState<Fund[]>([]);

  const [filters, setFilters] = useState({
    q: '',
    risk: '',
    platform: 'All Platforms',
    sort_by: '',
  });

  const debouncedQ = useDebounce(filters.q, 300);

  const fetchFunds = useCallback(
    async (queryText: string) => {
      setLoading(true);
      setErrorMessage(null);
      try {
        const data = await fundsAPI.search(
          queryText,
          filters.platform,
          filters.risk,
          filters.sort_by
        );
        setFunds(data);
      } catch (err) {
        setErrorMessage(handleApiError(err));
      } finally {
        setLoading(false);
      }
    },
    [filters.platform, filters.risk, filters.sort_by]
  );

  useEffect(() => {
    fetchFunds(debouncedQ);
  }, [debouncedQ, fetchFunds]);

  const handleFilterChange = (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    setFilters((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleAnalyze = (fund: Fund) => {
    navigate('/', { state: { prefilledFund: fund } });
  };

  const handleCompareSelect = (fund: Fund) => {
    setCompareList((prev) => {
      const alreadySelected = prev.find((f) => f.id === fund.id);
      if (alreadySelected) {
        return prev.filter((f) => f.id !== fund.id);
      }
      if (prev.length >= 2) {
        return [prev[1], fund];
      }
      return [...prev, fund];
    });
  };

  const topPickId =
    funds.length > 0
      ? funds.reduce((prev, current) =>
          prev.return_5y > current.return_5y ? prev : current
        ).id
      : null;

  return (
    <div className="explorer-container">
      <div className="explorer-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ color: 'var(--text-primary)' }}>Mutual Fund Explorer</h2>
          <p className="text-muted">Discover and compare equity, index, and hybrid fund historical metrics.</p>
        </div>

        {compareList.length > 0 && (
          <div className="compare-dock slide-up">
            <span className="text-muted" style={{ fontSize: '0.9rem', marginRight: '1rem' }}>
              Comparing {compareList.length}/2
            </span>
            <div className="compare-items" style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
              {compareList.map((fund) => (
                <div key={fund.id} className="compare-chip">
                  <span className="truncate" style={{ maxWidth: '120px', display: 'inline-block', lineHeight: 1 }}>
                    {fund.name}
                  </span>
                  <X
                    size={14}
                    className="cursor-pointer"
                    style={{ marginLeft: '4px' }}
                    onClick={() => handleCompareSelect(fund)}
                  />
                </div>
              ))}
              {compareList.length < 2 && (
                <div className="compare-chip text-muted" style={{ background: 'transparent', border: '1px dashed var(--border-color)' }}>
                  <PlusCircle size={14} /> Add 2nd Fund
                </div>
              )}
            </div>
            {compareList.length === 2 && (
              <Button
                style={{ marginLeft: '1rem', padding: '0.4rem 1rem' }}
                onClick={() => navigate('/compare', { state: { funds: compareList } })}
              >
                Compare Now
              </Button>
            )}
          </div>
        )}
      </div>

      <GlassCard className="filter-bar" hoverEffect={false}>
        <div className="filter-inputs">
          <Input
            placeholder="Search fund name or category..."
            name="q"
            value={filters.q}
            onChange={handleFilterChange}
            style={{ marginBottom: 0 }}
          />
          <select
            name="risk"
            className="custom-select"
            value={filters.risk}
            onChange={handleFilterChange}
          >
            <option value="">All Risk Levels</option>
            <option value="Moderate">Moderate Risk</option>
            <option value="Moderately High">Moderately High</option>
            <option value="High">High Risk</option>
            <option value="Very High">Very High Risk</option>
          </select>
          <div className="platform-buttons">
            {PLATFORMS.map((platform) => (
              <button
                key={platform}
                type="button"
                className={`platform-chip ${filters.platform === platform ? 'active' : ''}`}
                onClick={() => setFilters((prev) => ({ ...prev, platform }))}
              >
                {platform}
              </button>
            ))}
          </div>
          <select
            name="sort_by"
            className="custom-select"
            value={filters.sort_by}
            onChange={handleFilterChange}
          >
            <option value="">Sort By Performance</option>
            <option value="return_5y">5Y Return (High to Low)</option>
            <option value="return_3y">3Y Return (High to Low)</option>
            <option value="expense_ratio">Expense Ratio (Low to High)</option>
          </select>
        </div>
        <Button onClick={() => fetchFunds(filters.q)} disabled={loading} style={{ height: '100%' }}>
          <Search size={18} /> Search
        </Button>
      </GlassCard>

      {errorMessage && (
        <div className="error-banner" style={{ margin: '1rem 0', padding: '0.75rem', borderRadius: '8px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' }}>
          {errorMessage}
        </div>
      )}

      {loading ? (
        <div className="funds-loading">Loading funds catalogue...</div>
      ) : (
        <div className="funds-grid">
          {funds.length > 0 ? (
            funds.map((fund, i) => (
              <FundCard
                key={fund.id}
                fund={fund}
                index={i}
                isTopPick={fund.id === topPickId}
                onAnalyze={handleAnalyze}
                onCompareSelect={handleCompareSelect}
                isSelectedForCompare={!!compareList.find((f) => f.id === fund.id)}
              />
            ))
          ) : (
            <div className="no-results">
              <Filter size={48} className="text-muted" style={{ opacity: 0.3, marginBottom: '1rem' }} />
              <p className="text-muted">No funds matched your filter criteria.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default FundExplorer;
