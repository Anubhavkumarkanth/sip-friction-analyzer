import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Search, Filter, ShieldAlert, Globe, ExternalLink, TrendingUp, BarChart2, X, PlusCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import GlassCard from '../components/ui/GlassCard';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import api from '../api';
import './FundExplorer.css';

const FundCard = ({ fund, index, isTopPick, onAnalyze, onCompareSelect, isSelectedForCompare }) => (
  <GlassCard className={`fund-card ${isSelectedForCompare ? 'selected-for-compare' : ''}`} style={{ animationDelay: `${index * 80}ms` }}>
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
      <div className="tag"><ShieldAlert size={12} /> {fund.risk_level}</div>
      <div className="tag"><Globe size={12} /> {fund.platform}</div>
    </div>

    <div className="fund-actions" style={{ display: 'flex', gap: '8px', marginTop: '1rem', flexWrap: 'wrap' }}>
      <a href={fund.invest_url} target="_blank" rel="noopener noreferrer" className="invest-btn" style={{flex: 1, minWidth: '100px'}}>
        Invest Now <ExternalLink size={14} />
      </a>
      <Button variant="secondary" onClick={() => onAnalyze(fund)} style={{flex: 1, minWidth: '130px', padding: '0.6rem'}}>
        <TrendingUp size={14} /> Detailed Analysis
      </Button>
      <Button 
        variant={isSelectedForCompare ? "primary" : "outline"} 
        onClick={() => onCompareSelect(fund)} 
        style={{flex: 1, minWidth: '100px', padding: '0.6rem'}}
        className={isSelectedForCompare ? 'bg-accent' : ''}
      >
        <BarChart2 size={14} /> {isSelectedForCompare ? "Added" : "Compare"}
      </Button>
    </div>
  </GlassCard>
);

function useDebounce(value, delay) {
  const [debouncedValue, setDebouncedValue] = useState(value);
  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(handler);
  }, [value, delay]);
  return debouncedValue;
}

