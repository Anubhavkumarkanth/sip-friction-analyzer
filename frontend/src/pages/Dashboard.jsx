import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { Trash2, TrendingUp, AlertCircle, Award, Target, Activity, Wallet, PieChart } from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { formatINR, formatINRAxis } from '../utils/formatINR';
import api from '../api';
import './Dashboard.css';

const StatBox = ({ title, value, icon, gradient, prefix = '', suffix = '' }) => (
  <GlassCard className="stat-box" style={{ padding: '1rem' }} hoverEffect={false}>
    <div className="stat-icon" style={{ background: gradient }}>{icon}</div>
    <div className="stat-info">
      <p className="stat-title">{title}</p>
      <h3 className="stat-value">{prefix}{value}{suffix}</h3>
    </div>
  </GlassCard>
);

const CCRBar = ({ ccr }) => {
  const pct = Math.min(Math.max(ccr * 100, 0), 100);
  const color = pct >= 90 ? 'var(--success)' : pct >= 60 ? 'var(--warning)' : 'var(--danger)';
  return (
    <div className="ccr-container">
      <div className="ccr-header">
        <span className="ccr-label">Contribution Compliance Rate</span>
        <span className="ccr-value" style={{ color }}>{pct.toFixed(1)}%</span>
      </div>
      <div className="ccr-track">
        <div className="ccr-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="custom-tooltip">
      <p className="tooltip-label">Year {label}</p>
      {payload.map((entry, i) => (
        <p key={i} className="tooltip-item" style={{ color: entry.color }}>
          {entry.name}: {formatINR(entry.value)}
        </p>
      ))}
    </div>
  );
};

const Dashboard = () => {
  const [inputs, setInputs] = useState({
    monthly_amount: '10000',
    annual_return: '12',
    years: '20'
  });

  const [events, setEvents] = useState([]);
  const [platformSearch, setPlatformSearch] = useState('All Platforms');
  const [platformFundResults, setPlatformFundResults] = useState([]);
  const location = useLocation();
  const [selectedFund, setSelectedFund] = useState(null);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (location.state?.prefilledFund) {
      const fund = location.state.prefilledFund;
      setSelectedFund(fund);
      setInputs((prev) => ({
        ...prev,
        annual_return: fund.return_5y || prev.annual_return
      }));
    }
  }, [location.state]);

  const handleInputChange = (e) => {
    const rawValue = e.target.value;
    // allow partial input so backspace clears field properly
    setInputs((prev) => ({
      ...prev,
      [e.target.id]: rawValue
    }));
  };

  const addEvent = (type) => {
    const newEvent = { type, month: 12, factor: 0.5, yearly_growth: 0.1, start_month: 12, end_month: 24, id: Date.now() };
    setEvents([...events, newEvent]);
  };

  const removeEvent = (id) => {
    setEvents(events.filter(e => e.id !== id));
  };

  const handleEventChange = (id, field, value) => {
    setEvents(events.map(e => e.id === id ? { ...e, [field]: parseFloat(value) || 0 } : e));
  };

  const runSimulation = async (overrideFund) => {
    setLoading(true);
    try {
      // Parse inputs - handle string values from input fields
      const monthlyAmount = parseFloat(inputs.monthly_amount);
      // Check if overrideFund is actually a Fund object (has return_5y property), not a click event
      const annReturn = (overrideFund && typeof overrideFund === 'object' && 'return_5y' in overrideFund) 
        ? parseFloat(overrideFund.return_5y) 
        : parseFloat(inputs.annual_return);
      const years = parseFloat(inputs.years);

      // Simple validation - check for valid positive numbers
      if (isNaN(monthlyAmount) || isNaN(annReturn) || isNaN(years) || monthlyAmount <= 0 || annReturn <= 0 || years <= 0) {
        alert('Invalid input detected. Please ensure all fields contain valid positive numbers.');
        setLoading(false);
        return;
      }

      const monthlyReturn = annReturn / 100 / 12;
      const totalMonths = Math.floor(years * 12);
      const simEvents = events.map(({ id, ...rest }) => rest);

      let idealValue = 0;
      let actualValue = 0;
      let monthlyBase = monthlyAmount;
      let totalExpected = 0;
      let totalActual = 0;
      const eventMap = {};
      const pauseRanges = [];
      let stepUpRate = 0;

      // Parse events
      simEvents.forEach((event) => {
        if (event.type === 'PAUSE_RANGE') {
          pauseRanges.push([Number(event.start_month) || 0, Number(event.end_month) || 0]);
        } else if (event.type === 'STEP_UP') {
          stepUpRate = Number(event.yearly_growth) || 0;
        } else {
          const month = Number(event.month) || 0;
          if (month > 0) {
            if (!eventMap[month]) eventMap[month] = [];
            eventMap[month].push(event);
          }
        }
      });

      const chartData = [];

      // Run simulation month by month
      for (let month = 1; month <= totalMonths; month++) {
        // Ideal calculation
        idealValue = (idealValue + monthlyBase) * (1 + monthlyReturn);

        // Actual calculation
        let contribution = monthlyBase;
        totalExpected += monthlyBase;

        // Check pause ranges
        for (let i = 0; i < pauseRanges.length; i++) {
          const [start, end] = pauseRanges[i];
          if (start > 0 && end > 0 && month >= start && month <= end) {
            contribution = 0;
            break;
          }
        }

        // Check event map
        if (eventMap[month]) {
          for (let i = 0; i < eventMap[month].length; i++) {
            const ev = eventMap[month][i];
            if (ev.type === 'SKIP') {
              contribution = 0;
            } else if (ev.type === 'REDUCE') {
              contribution = monthlyBase * (Number(ev.factor) || 1);
            } else if (ev.type === 'INCREASE') {
              monthlyBase = monthlyBase * (Number(ev.factor) || 1);
              contribution = monthlyBase;
            }
          }
        }

        totalActual += contribution;

        // Step up annually
        if (stepUpRate && month % 12 === 0) {
          monthlyBase = monthlyBase * (1 + stepUpRate);
        }

        actualValue = (actualValue + contribution) * (1 + monthlyReturn);

        // Record annual data
        if (month % 12 === 0) {
          chartData.push({
            year: month / 12,
            ideal: Math.round(idealValue * 100) / 100,
            actual: Math.round(actualValue * 100) / 100,
            difference: Math.round((idealValue - actualValue) * 100) / 100
          });
        }
      }

      // Calculate metrics
      const cld = Math.max(idealValue - actualValue, 0);
      const ccr = totalExpected > 0 ? totalActual / totalExpected : 1;
      const cldRatio = idealValue > 0 ? cld / idealValue : 0;
      const penaltyScore = 40 * (1 - ccr) + 60 * cldRatio;
      const disciplineScore = Math.max(0, Math.min(100, 100 - penaltyScore));

      const finalResults = {
        ideal_value: Math.round(idealValue * 100) / 100,
        actual_value: Math.round(actualValue * 100) / 100,
        compounding_loss: Math.round(cld * 100) / 100,
        discipline_score: Math.round(disciplineScore * 100) / 100,
        ccr: Math.round(ccr * 10000) / 10000,
        total_expected_contribution: Math.round(totalExpected * 100) / 100,
        total_actual_contribution: Math.round(totalActual * 100) / 100,
        chart_data: chartData
      };

      setResults(finalResults);
    } catch (err) {
      console.error('❌ Simulation error:', err);
      alert('Simulation error: ' + err.message);
    }
    setLoading(false);
  };

  const searchPlatformFunds = async (platform) => {
    setPlatformSearch(platform);
    try {
      const q = platform === 'All Platforms' ? '' : platform;
      const response = await api.get(`/search-funds?platform=${encodeURIComponent(q)}`);
      setPlatformFundResults(response.data);
    } catch (err) {
      console.error('Platform search error:', err);
      setPlatformFundResults([]);
    }
  };

  return (
    <div className="dashboard-container">
      <div className="dashboard-inputs">
        <GlassCard hoverEffect={false}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Target size={20} className="text-accent" />
            <h3 style={{ margin: 0 }}>Base Setup</h3>
          </div>
          <Input label="Monthly Amount (₹)" id="monthly_amount" type="number" value={inputs.monthly_amount} onChange={handleInputChange} />
          <Input label="Expected Annual Return (%)" id="annual_return" type="number" value={inputs.annual_return} onChange={handleInputChange} />
          <Input label="Investment Period (Years)" id="years" type="number" value={inputs.years} onChange={handleInputChange} />

          <div className="events-section">
            <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem', color: 'var(--text-main)' }}>Add Friction Events</h4>
            <div className="event-buttons">
              <Button variant="secondary" onClick={() => addEvent("PAUSE_RANGE")} style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}>+ Pause SIP</Button>
              <Button variant="secondary" onClick={() => addEvent("STEP_UP")} style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}>+ Step Up</Button>
              <Button variant="secondary" onClick={() => addEvent("REDUCE")} style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}>+ Reduce SIP</Button>
            </div>

            <div className="event-list">
              {events.map((e) => (
                <div key={e.id} className="event-item">
                  <div className="event-header">
                    <span className="event-badge">{e.type}</span>
                    <button className="icon-btn-small" onClick={() => removeEvent(e.id)}><Trash2 size={14} /></button>
                  </div>
                  {e.type === 'PAUSE_RANGE' && (
                    <div className="event-inputs">
                      <Input label="Start Month" type="number" value={e.start_month} onChange={(ev) => handleEventChange(e.id, 'start_month', ev.target.value)} />
                      <Input label="End Month" type="number" value={e.end_month} onChange={(ev) => handleEventChange(e.id, 'end_month', ev.target.value)} />
                    </div>
                  )}
                  {e.type === 'STEP_UP' && (
                    <div className="event-inputs">
                      <Input label="Annual Increase (%)" type="number" value={e.yearly_growth * 100} onChange={(ev) => handleEventChange(e.id, 'yearly_growth', ev.target.value / 100)} />
                    </div>
                  )}
                  {e.type === 'REDUCE' && (
                    <div className="event-inputs">
                      <Input label="At Month" type="number" value={e.month} onChange={(ev) => handleEventChange(e.id, 'month', ev.target.value)} />
                      <Input label="Factor (e.g. 0.5)" type="number" value={e.factor} onChange={(ev) => handleEventChange(e.id, 'factor', ev.target.value)} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <Button onClick={runSimulation} disabled={loading} className="run-btn" style={{ width: '100%', marginTop: '1.5rem' }}>
            {loading ? 'Simulating...' : 'Run Simulation'}
          </Button>
        </GlassCard>

        {selectedFund && (
          <GlassCard hoverEffect={false} style={{ marginTop: '1rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
              <div>
                <h3 style={{ marginBottom: '0.75rem' }}>Detailed Fund Review</h3>
                <p className="text-muted" style={{ marginBottom: '0.5rem' }}>{selectedFund.name}</p>
              </div>
              <Button variant="outline" onClick={() => setSelectedFund(null)} style={{ height: '2rem' }}>
                Clear
              </Button>
            </div>

            <div className="compare-metrics" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div className="compare-row"><strong>Category</strong><span>{selectedFund.category}</span></div>
              <div className="compare-row"><strong>Risk</strong><span>{selectedFund.risk_level}</span></div>
              <div className="compare-row"><strong>3Y Return</strong><span>{selectedFund.return_3y}%</span></div>
              <div className="compare-row"><strong>5Y Return</strong><span>{selectedFund.return_5y}%</span></div>
              <div className="compare-row"><strong>Expense Ratio</strong><span>{selectedFund.expense_ratio}%</span></div>
              <div className="compare-row"><strong>Platform</strong><span>{selectedFund.platform}</span></div>
            </div>
            <Button onClick={() => runSimulation(selectedFund)} style={{ marginTop: '1rem', width: '100%' }}>
              Run SIP Simulation for this fund
            </Button>
          </GlassCard>
        )}

        <GlassCard hoverEffect={false} style={{ marginTop: '1rem' }}>
          <h3 style={{ marginBottom: '0.75rem' }}>Search SIPs by Platform</h3>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            {['All Platforms', 'Groww', 'Zerodha', 'Angel One'].map((plat) => (
              <button
                key={plat}
                className={`platform-chip ${platformSearch === plat ? 'active' : ''}`}
                style={{ padding: '0.35rem 0.75rem', borderRadius: '999px', border: '1px solid var(--border-color)', background: platformSearch === plat ? 'var(--accent-background)' : 'transparent', color: 'var(--text-primary)', cursor: 'pointer' }}
                onClick={() => searchPlatformFunds(plat)}
              >
                {plat}
              </button>
            ))}
          </div>
          <div style={{ marginTop: '0.8rem', maxHeight: '210px', overflowY: 'auto' }}>
            {platformFundResults.length === 0 ? (
              <p className="text-muted">No funds found for {platformSearch} yet.</p>
            ) : (
              <div style={{ display: 'grid', gap: '0.6rem' }}>
                {platformFundResults.map((fund) => (
                  <div key={fund.id} className="compare-row" style={{ display: 'flex', justifyContent: 'space-between', cursor: 'pointer' }} onClick={() => {
                    setSelectedFund(fund);
                    setInputs(prev => ({ ...prev, annual_return: fund.return_5y || prev.annual_return }));
                  }}>
                    <span>{fund.name}</span>
                    <span className="text-accent">{fund.return_5y}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </GlassCard>
      </div>

      <div className="dashboard-results">
        {results ? (
          <div className="animate-fade-in">
            <div className="stats-grid">
              <StatBox title="Ideal Wealth" value={formatINR(results.ideal_value)} icon={<TrendingUp size={24} color="#fff" />} gradient="var(--accent-gradient)" />
              <StatBox title="Actual Wealth" value={formatINR(results.actual_value)} icon={<Target size={24} color="#fff" />} gradient="var(--accent-gradient-alt)" />
              <StatBox title="Compounding Loss" value={formatINR(results.compounding_loss)} icon={<AlertCircle size={24} color="#fff" />} gradient="linear-gradient(135deg, #ef4444 0%, #f97316 100%)" />
              <StatBox title="Total Invested" value={formatINR(results.total_actual_contribution)} icon={<Wallet size={24} color="#fff" />} gradient="linear-gradient(135deg, #f59e0b 0%, #eab308 100%)" />
              <StatBox title="Discipline Score" value={results.discipline_score} icon={<Award size={24} color="#fff" />} gradient="linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%)" suffix="/100" />
            </div>

            {results.ccr != null && <CCRBar ccr={results.ccr} />}

            <GlassCard className="chart-container" style={{ marginTop: '1.5rem', height: '400px' }} hoverEffect={false}>
              <h3 style={{ marginBottom: '1rem' }}>Wealth Accumulation Trajectory (Single Combined Chart)</h3>
              <p className="text-muted" style={{ marginBottom: '0.8rem' }}>Blue line = ideal discipline; red line = actual with friction; grey area = difference.</p>
              <ResponsiveContainer width="100%" height="82%">
                <AreaChart data={results.chart_data}>
                  <defs>
                    <linearGradient id="diffGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f87171" stopOpacity={0.3} />
                      <stop offset="100%" stopColor="#f87171" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                  <XAxis dataKey="year" stroke="var(--text-muted)" tickMargin={10} name="Year" />
                  <YAxis stroke="var(--text-muted)" tickFormatter={formatINRAxis} width={80} />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ paddingTop: '10px' }} />

                  <Area type="monotone" dataKey="ideal" name="Ideal (disciplined)" stroke="#3b82f6" strokeWidth={2.5} fill="none" dot={false} />
                  <Area type="monotone" dataKey="actual" name="Actual (with friction)" stroke="#ef4444" strokeWidth={2.5} fill="none" dot={false} />

                  <Area type="monotone" dataKey="difference" name="Friction Loss (ideal - actual)" stroke="none" fill="url(#diffGrad)" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </GlassCard>
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-icon-wrap">
              <Activity size={48} className="text-muted empty-pulse" />
            </div>
            <p className="text-muted" style={{ marginTop: '1rem' }}>Configure your SIP and run a simulation to visualise the trajectory</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
