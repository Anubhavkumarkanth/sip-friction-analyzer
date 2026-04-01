import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Target, Activity, CheckCircle, AlertTriangle, TrendingDown, TrendingUp, Zap } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { formatINR, formatINRAxis } from '../utils/formatINR';
import api from '../api';
import './MonteCarlo.css';

const StatBox = ({ title, value, icon, gradient }) => (
  <GlassCard className="mc-stat-box" style={{ padding: '1rem' }} hoverEffect={false}>
    <div className="mc-stat-icon" style={{ background: gradient }}>{icon}</div>
    <div className="mc-stat-info">
      <p className="mc-stat-title">{title}</p>
      <h3 className="mc-stat-value">{formatINR(value)}</h3>
    </div>
  </GlassCard>
);

const SCENARIO_COLORS = {
  'Worst Case': '#ef4444',
  'P10': '#f59e0b',
  'Median (P50)': '#3b82f6',
  'Mean': '#8b5cf6',
  'P90': '#6366f1',
  'Best Case': '#10b981',
};

const CustomBarTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="mc-bar-tooltip">
      <p style={{ color: d.color, fontWeight: 600 }}>{d.name}</p>
      <p style={{ color: 'var(--text-primary)', marginTop: '0.25rem' }}>{formatINR(d.value)}</p>
    </div>
  );
};

const MonteCarlo = () => {
  const [inputs, setInputs] = useState({
    monthly_amount: 10000,
    annual_return: 12,
    years: 15
  });

  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    setInputs({ ...inputs, [e.target.id]: parseFloat(e.target.value) || 0 });
  };

  const runSimulation = async () => {
    setLoading(true);
    try {
      const response = await api.post('/monte-carlo', { ...inputs, events: [] });
      setResults(response.data);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const chartData = results ? [
    { name: 'Worst Case', value: results.worst_case, color: SCENARIO_COLORS['Worst Case'] },
    { name: 'P10', value: results.p10, color: SCENARIO_COLORS['P10'] },
    { name: 'Median (P50)', value: results.p50, color: SCENARIO_COLORS['Median (P50)'] },
    { name: 'Mean', value: results.mean, color: SCENARIO_COLORS['Mean'] },
    { name: 'P90', value: results.p90, color: SCENARIO_COLORS['P90'] },
    { name: 'Best Case', value: results.best_case, color: SCENARIO_COLORS['Best Case'] },
  ] : [];

  return (
    <div className="mc-container">
      <div className="mc-header">
        <Activity size={32} className="text-accent" />
        <div>
          <h2 style={{ color: 'var(--text-primary)' }}>Monte Carlo Simulation</h2>
          <p className="text-muted">Simulate 1,000 market scenarios to find realistic outcomes.</p>
        </div>
      </div>

      <div className="mc-layout">
        <GlassCard className="mc-inputs" hoverEffect={false}>
          <h3 style={{ marginBottom: '1.5rem', color: 'var(--text-primary)' }}>Simulation Parameters</h3>
          <Input label="Monthly SIP (₹)" id="monthly_amount" type="number" value={inputs.monthly_amount} onChange={handleInputChange} />
          <Input label="Target Annual Return (%)" id="annual_return" type="number" value={inputs.annual_return} onChange={handleInputChange} />
          <Input label="Duration (Years)" id="years" type="number" value={inputs.years} onChange={handleInputChange} />

          <Button onClick={runSimulation} disabled={loading} style={{ width: '100%', marginTop: '2rem', padding: '1rem' }}>
            <Zap size={18} /> {loading ? 'Running 1000 Simulations...' : 'Run Monte Carlo'}
          </Button>
        </GlassCard>

        <div className="mc-results-area">
          {results ? (
            <div className="mc-results-grid animate-fade-in">
              <StatBox title="Worst Case (Minimum)" value={results.worst_case} icon={<AlertTriangle size={24} color="#fff" />} gradient="var(--danger)" />
              <StatBox title="10th Percentile (P10)" value={results.p10} icon={<TrendingDown size={24} color="#fff" />} gradient="linear-gradient(135deg, #f59e0b 0%, #d97706 100%)" />
              <StatBox title="Expected Median (P50)" value={results.p50} icon={<Target size={24} color="#fff" />} gradient="var(--accent-gradient)" />
              <StatBox title="Mean (Average)" value={results.mean} icon={<Activity size={24} color="#fff" />} gradient="var(--accent-gradient-alt)" />
              <StatBox title="90th Percentile (P90)" value={results.p90} icon={<TrendingUp size={24} color="#fff" />} gradient="linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)" />
              <StatBox title="Best Case (Maximum)" value={results.best_case} icon={<CheckCircle size={24} color="#fff" />} gradient="linear-gradient(135deg, #10b981 0%, #059669 100%)" />

              {/* Scenario Range Chart */}
              <GlassCard style={{ gridColumn: '1 / -1', marginTop: '0.5rem', height: '320px' }} hoverEffect={false}>
                <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.75rem' }}>Scenario Distribution</h3>
                <ResponsiveContainer width="100%" height="85%">
                  <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 30 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" horizontal={false} />
                    <XAxis type="number" stroke="var(--text-muted)" tickFormatter={formatINRAxis} />
                    <YAxis type="category" dataKey="name" stroke="var(--text-muted)" width={100} tick={{ fontSize: 12 }} />
                    <Tooltip content={<CustomBarTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                    <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={24}>
                      {chartData.map((entry, i) => (
                        <Cell key={i} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </GlassCard>

              <GlassCard style={{ gridColumn: '1 / -1', marginTop: '0.5rem' }} hoverEffect={false}>
                <h3 style={{ color: 'var(--text-primary)' }}>Summary of Outcomes</h3>
                <p style={{ marginTop: '1rem', lineHeight: '1.8', color: 'var(--text-main)' }}>
                  Across 1,000 market simulations based on historical volatility logic, the terminal wealth of your SIP spans from
                  <strong style={{ color: 'var(--danger)', marginLeft: '0.4rem', marginRight: '0.4rem' }}>{formatINR(results.worst_case)}</strong>
                  to
                  <strong style={{ color: 'var(--success)', marginLeft: '0.4rem', marginRight: '0.4rem' }}>{formatINR(results.best_case)}</strong>.
                  However, standard expectation lies around the median of
                  <strong style={{ color: 'var(--accent-primary)', marginLeft: '0.4rem' }}>{formatINR(results.p50)}</strong>.
                </p>
              </GlassCard>
            </div>
          ) : (
            <div className="mc-empty-state">
              <div className="empty-icon-wrap">
                <Activity size={48} className="text-muted empty-pulse" />
              </div>
              <p className="text-muted" style={{ marginTop: '1rem' }}>Set your parameters and run the simulation to see probable outcomes</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MonteCarlo;
