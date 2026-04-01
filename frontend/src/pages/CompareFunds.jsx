import React from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { RefreshCcw, TrendingUp, ArrowLeft } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import Button from '../components/ui/Button';
import './CompareFunds.css';

const CompareFunds = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const funds = location.state?.funds;

  if (!funds || funds.length < 2) {
    return <Navigate to="/funds" replace />;
  }

  const [fundOne, fundTwo] = funds;

  const handleSimulate = (fund) => {
    navigate('/', { state: { prefilledFund: fund } });
  };

  return (
    <div className="compare-container animate-fade-in">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', width: '100%' }}>
        <button className="icon-btn-small" onClick={() => navigate('/funds')}>
          <ArrowLeft size={18} />
        </button>
        <h2 style={{ color: 'var(--text-primary)', margin: 0 }}>Fund Comparison</h2>
      </div>
      <p className="text-muted" style={{ marginTop: '0.5rem', marginBottom: '2rem', marginLeft: '2.5rem' }}>
        Side-by-side analysis of your selected mutual funds.
      </p>

      <div className="compare-grid">
        {/* Fund 1 */}
        <GlassCard className="compare-card">
          <h3 className="fund-name text-center" style={{ marginBottom: '0.5rem' }}>{fundOne.name}</h3>
          <p className="text-muted text-center" style={{ marginBottom: '1.5rem' }}>{fundOne.category} &bull; {fundOne.risk_level}</p>
          
          <div className="compare-metrics">
            <div className="compare-row">
              <span className="text-muted">3-Year Return</span>
              <span className={fundOne.return_3y > fundTwo.return_3y ? "text-accent fw-bold" : ""}>{fundOne.return_3y}%</span>
            </div>
            <div className="compare-row">
              <span className="text-muted">5-Year Return</span>
              <span className={fundOne.return_5y > fundTwo.return_5y ? "text-accent fw-bold" : ""}>{fundOne.return_5y}%</span>
            </div>
            <div className="compare-row">
              <span className="text-muted">Expense Ratio</span>
              <span className={fundOne.expense_ratio < fundTwo.expense_ratio ? "text-success fw-bold" : ""}>{fundOne.expense_ratio}%</span>
            </div>
            <div className="compare-row">
              <span className="text-muted">Platform</span>
              <span>{fundOne.platform}</span>
            </div>
          </div>

          <div style={{ marginTop: '2rem' }}>
            <Button onClick={() => handleSimulate(fundOne)} style={{ width: '100%' }}>
              <TrendingUp size={16} /> Simulate This Fund
            </Button>
          </div>
        </GlassCard>

        <div className="vs-badge">
          <RefreshCcw size={24} className="text-muted" />
        </div>

        {/* Fund 2 */}
        <GlassCard className="compare-card">
          <h3 className="fund-name text-center" style={{ marginBottom: '0.5rem' }}>{fundTwo.name}</h3>
          <p className="text-muted text-center" style={{ marginBottom: '1.5rem' }}>{fundTwo.category} &bull; {fundTwo.risk_level}</p>
          
          <div className="compare-metrics">
            <div className="compare-row">
              <span className="text-muted">3-Year Return</span>
              <span className={fundTwo.return_3y > fundOne.return_3y ? "text-accent fw-bold" : ""}>{fundTwo.return_3y}%</span>
            </div>
            <div className="compare-row">
              <span className="text-muted">5-Year Return</span>
              <span className={fundTwo.return_5y > fundOne.return_5y ? "text-accent fw-bold" : ""}>{fundTwo.return_5y}%</span>
            </div>
            <div className="compare-row">
              <span className="text-muted">Expense Ratio</span>
              <span className={fundTwo.expense_ratio < fundOne.expense_ratio ? "text-success fw-bold" : ""}>{fundTwo.expense_ratio}%</span>
            </div>
            <div className="compare-row">
              <span className="text-muted">Platform</span>
              <span>{fundTwo.platform}</span>
            </div>
          </div>

          <div style={{ marginTop: '2rem' }}>
            <Button onClick={() => handleSimulate(fundTwo)} style={{ width: '100%' }}>
              <TrendingUp size={16} /> Simulate This Fund
            </Button>
          </div>
        </GlassCard>
      </div>
    </div>
  );
};

export default CompareFunds;
