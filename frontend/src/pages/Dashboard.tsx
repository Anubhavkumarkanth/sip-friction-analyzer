import { useState, useEffect, useCallback, FC, ChangeEvent } from 'react';
import { useLocation } from 'react-router-dom';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts';
import {
  Trash2,
  TrendingUp,
  AlertCircle,
  Award,
  Target,
  Activity,
  Wallet,
} from 'lucide-react';
import GlassCard from '../components/ui/GlassCard';
import Input from '../components/ui/Input';
import Button from '../components/ui/Button';
import { formatINR, formatINRAxis } from '../utils/formatINR';
import { fundsAPI, simulationAPI, handleApiError } from '../services/api';
import {
  Fund,
  FrictionEvent,
  SIPInputs,
  SimulationResult,
  SimulationSummary,
  StatBoxProps,
} from '../types';
import './Dashboard.css';

// ==================== Sub-Components ====================
const StatBox: FC<StatBoxProps> = ({
  title,
  value,
  icon,
  gradient,
  prefix = '',
  suffix = '',
}) => (
  <GlassCard className="stat-box" style={{ padding: '1rem' }} hoverEffect={false}>
    <div className="stat-icon" style={{ background: gradient }}>{icon}</div>
    <div className="stat-info">
      <p className="stat-title">{title}</p>
      <h3 className="stat-value">
        {prefix}
        {value}
        {suffix}
      </h3>
    </div>
  </GlassCard>
);

interface CCRBarProps {
  ccr: number;
}

const CCRBar: FC<CCRBarProps> = ({ ccr }) => {
  const pct = Math.min(Math.max(ccr * 100, 0), 100);
  const color =
    pct >= 90 ? 'var(--success)' : pct >= 60 ? 'var(--warning)' : 'var(--danger)';
  return (
    <div className="ccr-container">
      <div className="ccr-header">
        <span className="ccr-label">Contribution Compliance Rate</span>
        <span className="ccr-value" style={{ color }}>
          {pct.toFixed(1)}%
        </span>
      </div>
      <div className="ccr-track">
        <div className="ccr-fill" style={{ width: `${pct}%`, background: color }} />
      </div>
    </div>
  );
};

interface CustomTooltipProps extends TooltipProps<number, string> {
  active?: boolean;
  payload?: Array<{ color: string; value: number; name: string }>;
  label?: number;
}

const CustomTooltip: FC<CustomTooltipProps> = ({ active, payload, label }) => {
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

// ==================== Main Dashboard Component ====================
const Dashboard: FC = () => {
  const [inputs, setInputs] = useState<SIPInputs>({
    monthly_amount: '10000',
    annual_return: '12',
    years: '20',
  });

  const [events, setEvents] = useState<FrictionEvent[]>([]);
  const [platformSearch, setPlatformSearch] = useState<string>('All Platforms');
  const [platformFundResults, setPlatformFundResults] = useState<Fund[]>([]);
  const [selectedFund, setSelectedFund] = useState<Fund | null>(null);
  const [results, setResults] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [validationErrors, setValidationErrors] = useState<Partial<SIPInputs>>({});
  const [apiError, setApiError] = useState<string | null>(null);
  const [history, setHistory] = useState<SimulationSummary[]>([]);
  const location = useLocation();

  // Past runs for the signed-in user, newest first.
  const loadHistory = useCallback(async (): Promise<void> => {
    try {
      setHistory(await simulationAPI.history(5));
    } catch {
      // History is supplementary; a failure here must not block simulating.
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    void loadHistory();
  }, [loadHistory]);

  // Load the fund list on mount. Without this the panel rendered an empty
  // result and the "No funds found" message before any search had actually
  // run, which read as a failure rather than an untouched filter.
  useEffect(() => {
    fundsAPI
      .search()
      .then(setPlatformFundResults)
      .catch(() => setPlatformFundResults([]));
  }, []);

  // Load prefilled fund from navigation
  useEffect(() => {
    const prefilledFund = (location.state as any)?.prefilledFund;
    if (prefilledFund) {
      setSelectedFund(prefilledFund);
      setInputs((prev) => ({
        ...prev,
        annual_return: String(prefilledFund.return_5y || prev.annual_return),
      }));
    }
  }, [location.state]);

  // ==================== Event Handlers ====================
  const handleInputChange = (e: ChangeEvent<HTMLInputElement>): void => {
    const { id, value } = e.target;
    setInputs((prev) => ({
      ...prev,
      [id]: value,
    }));
    // Clear errors when user starts typing
    if (validationErrors[id as keyof SIPInputs]) {
      setValidationErrors((prev) => ({
        ...prev,
        [id]: undefined,
      }));
    }
  };

  const validateInputs = (): boolean => {
    const errors: Partial<SIPInputs> = {};
    const monthlyAmount = parseFloat(inputs.monthly_amount);
    const annReturn = parseFloat(inputs.annual_return);
    const years = parseFloat(inputs.years);

    if (isNaN(monthlyAmount) || monthlyAmount <= 0) {
      errors.monthly_amount = 'Must be a positive number';
    }
    if (isNaN(annReturn) || annReturn < 0 || annReturn > 50) {
      errors.annual_return = 'Must be between 0-50%';
    }
    if (isNaN(years) || years <= 0 || years > 50) {
      errors.years = 'Must be 1-50 years';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const addEvent = (type: string): void => {
    const newEvent: FrictionEvent = {
      id: Date.now(),
      type: type as any,
      month: 12,
      factor: 0.5,
      yearly_growth: 0.1,
      start_month: 12,
      end_month: 24,
    };
    setEvents([...events, newEvent]);
  };

  const removeEvent = (id: number): void => {
    setEvents(events.filter((e) => e.id !== id));
  };

  const handleEventChange = (
    id: number,
    field: string,
    value: string
  ): void => {
    setEvents(
      events.map((e) =>
        e.id === id ? { ...e, [field]: parseFloat(value) || 0 } : e
      )
    );
  };

  const runSimulation = async (overrideFund?: Fund): Promise<void> => {
    if (!validateInputs()) {
      return;
    }

    setLoading(true);
    setApiError(null);
    try {
      const annReturn = overrideFund
        ? parseFloat(String(overrideFund.return_5y))
        : parseFloat(inputs.annual_return);

      // The simulation runs on the server.
      //
      // These same rules used to be reimplemented here in TypeScript, so the
      // compounding loop and the discipline-score formula existed twice, in two
      // languages, with nothing keeping them in step. The dashboard never
      // called the API at all, and nothing was ever saved. Now there is one
      // implementation, and every run is persisted with the events that
      // produced it.
      const result = await simulationAPI.run({
        monthly_amount: parseFloat(inputs.monthly_amount),
        annual_return: annReturn,
        years: parseFloat(inputs.years),
        // The id on each event is client-only, for list keys and editing.
        events: events.map((event) => ({
          type: event.type,
          month: event.month,
          factor: event.factor,
          yearly_growth: event.yearly_growth,
          start_month: event.start_month,
          end_month: event.end_month,
        })),
      });

      setResults(result);
      await loadHistory();
    } catch (err) {
      setApiError(handleApiError(err));
    } finally {
      setLoading(false);
    }
  };

  const searchPlatformFunds = async (platform: string): Promise<void> => {
    setPlatformSearch(platform);
    try {
      const query = platform === 'All Platforms' ? undefined : platform;
      const funds = await fundsAPI.search(undefined, query, undefined, undefined);
      setPlatformFundResults(funds);
    } catch (err) {
      console.error('Platform search error:', err);
      setPlatformFundResults([]);
    }
  };

  // ==================== Render ====================
  return (
    <div className="dashboard-container">
      {/* Left Panel - Inputs */}
      <div className="dashboard-inputs">
        <GlassCard hoverEffect={false}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <Target size={20} className="text-accent" />
            <h3 style={{ margin: 0 }}>Base Setup</h3>
          </div>

          <Input
            label="Monthly Amount (₹)"
            id="monthly_amount"
            type="number"
            value={inputs.monthly_amount}
            onChange={handleInputChange}
            error={validationErrors.monthly_amount}
          />
          <Input
            label="Expected Annual Return (%)"
            id="annual_return"
            type="number"
            value={inputs.annual_return}
            onChange={handleInputChange}
            error={validationErrors.annual_return}
          />
          <Input
            label="Investment Period (Years)"
            id="years"
            type="number"
            value={inputs.years}
            onChange={handleInputChange}
            error={validationErrors.years}
          />

          {/* Events Section */}
          <div className="events-section">
            <h4 style={{ marginTop: '1.5rem', marginBottom: '1rem', color: 'var(--text-main)' }}>
              Add Friction Events
            </h4>
            <div className="event-buttons">
              <Button
                variant="secondary"
                onClick={() => addEvent('PAUSE_RANGE')}
                style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
              >
                + Pause SIP
              </Button>
              <Button
                variant="secondary"
                onClick={() => addEvent('STEP_UP')}
                style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
              >
                + Step Up
              </Button>
              <Button
                variant="secondary"
                onClick={() => addEvent('REDUCE')}
                style={{ fontSize: '0.8rem', padding: '0.4rem 0.8rem' }}
              >
                + Reduce SIP
              </Button>
            </div>

            <div className="event-list">
              {events.map((e) => (
                <div key={e.id} className="event-item">
                  <div className="event-header">
                    <span className="event-badge">{e.type}</span>
                    <button
                      className="icon-btn-small"
                      onClick={() => removeEvent(e.id)}
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                  {e.type === 'PAUSE_RANGE' && (
                    <div className="event-inputs">
                      <Input
                        label="Start Month"
                        type="number"
                        value={e.start_month}
                        onChange={(ev) =>
                          handleEventChange(e.id, 'start_month', ev.target.value)
                        }
                      />
                      <Input
                        label="End Month"
                        type="number"
                        value={e.end_month}
                        onChange={(ev) =>
                          handleEventChange(e.id, 'end_month', ev.target.value)
                        }
                      />
                    </div>
                  )}
                  {e.type === 'STEP_UP' && (
                    <div className="event-inputs">
                      <Input
                        label="Annual Increase (%)"
                        type="number"
                        value={(e.yearly_growth || 0) * 100}
                        onChange={(ev) =>
                          handleEventChange(
                            e.id,
                            'yearly_growth',
                            String(parseFloat(ev.target.value) / 100)
                          )
                        }
                      />
                    </div>
                  )}
                  {e.type === 'REDUCE' && (
                    <div className="event-inputs">
                      <Input
                        label="At Month"
                        type="number"
                        value={e.month}
                        onChange={(ev) =>
                          handleEventChange(e.id, 'month', ev.target.value)
                        }
                      />
                      <Input
                        label="Factor (e.g. 0.5)"
                        type="number"
                        value={e.factor}
                        onChange={(ev) =>
                          handleEventChange(e.id, 'factor', ev.target.value)
                        }
                      />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          <Button
            onClick={() => runSimulation()}
            disabled={loading}
            loading={loading}
            className="run-btn"
            style={{ width: '100%', marginTop: '1.5rem' }}
          >
            Run Simulation
          </Button>

          {apiError && (
            <p
              role="alert"
              style={{
                marginTop: '0.75rem',
                marginBottom: 0,
                color: 'var(--danger)',
                fontSize: '0.85rem',
              }}
            >
              {apiError}
            </p>
          )}
        </GlassCard>

        {/* Past runs, read back from the database */}
        {history.length > 0 && (
          <GlassCard hoverEffect={false} style={{ marginTop: '1rem' }}>
            <h4 style={{ marginTop: 0, marginBottom: '0.75rem' }}>Recent runs</h4>
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {history.map((run) => (
                <li
                  key={run.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: '0.75rem',
                    padding: '0.45rem 0',
                    borderBottom: '1px solid var(--border, rgba(255,255,255,0.08))',
                    fontSize: '0.82rem',
                  }}
                >
                  <span>{new Date(run.created_at).toLocaleDateString()}</span>
                  <span>
                    {formatINR(run.monthly_amount)}/mo · {run.years}y
                  </span>
                  <span>
                    {run.event_count} event{run.event_count === 1 ? '' : 's'}
                  </span>
                  <strong>{run.discipline_score.toFixed(1)}</strong>
                </li>
              ))}
            </ul>
          </GlassCard>
        )}

        {/* Fund Review Card */}
        {selectedFund && (
          <GlassCard hoverEffect={false} style={{ marginTop: '1rem' }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'start',
              }}
            >
              <div>
                <h3 style={{ marginBottom: '0.75rem' }}>{selectedFund.name}</h3>
                <p className="text-muted" style={{marginBottom: '0.5rem'}}>
                  {selectedFund.category}
                </p>
              </div>
              <Button
                variant="outline"
                onClick={() => setSelectedFund(null)}
                style={{ height: '2rem' }}
              >
                Clear
              </Button>
            </div>

            <div
              className="compare-metrics"
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr 1fr',
                gap: '0.75rem',
                marginTop: '1rem',
              }}
            >
              <div className="compare-row">
                <strong>Risk Level</strong>
                <span>{selectedFund.risk_level}</span>
              </div>
              <div className="compare-row">
                <strong>Platform</strong>
                <span>{selectedFund.platform}</span>
              </div>
              <div className="compare-row">
                <strong>3Y Return</strong>
                <span>{selectedFund.return_3y}%</span>
              </div>
              <div className="compare-row">
                <strong>5Y Return</strong>
                <span>{selectedFund.return_5y}%</span>
              </div>
              <div className="compare-row">
                <strong>Expense Ratio</strong>
                <span>{selectedFund.expense_ratio}%</span>
              </div>
            </div>

            <Button
              onClick={() => runSimulation(selectedFund)}
              style={{ marginTop: '1rem', width: '100%' }}
            >
              Run SIP Simulation for this Fund
            </Button>
          </GlassCard>
        )}

        {/* Platform Search */}
        <GlassCard hoverEffect={false} style={{ marginTop: '1rem' }}>
          <h3 style={{ marginBottom: '0.75rem' }}>Search SIPs by Platform</h3>
          <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap' }}>
            {['All Platforms', 'Groww', 'Zerodha', 'Angel One'].map((plat) => (
              <button
                key={plat}
                className={`platform-chip ${platformSearch === plat ? 'active' : ''}`}
                style={{
                  padding: '0.35rem 0.75rem',
                  borderRadius: '999px',
                  border: '1px solid var(--border-color)',
                  background:
                    platformSearch === plat
                      ? 'var(--accent-background)'
                      : 'transparent',
                  color: 'var(--text-primary)',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
                onClick={() => searchPlatformFunds(plat)}
              >
                {plat}
              </button>
            ))}
          </div>
          <div
            style={{
              marginTop: '0.8rem',
              maxHeight: '210px',
              overflowY: 'auto',
            }}
          >
            {platformFundResults.length === 0 ? (
              <p className="text-muted">No funds found for {platformSearch}.</p>
            ) : (
              <div style={{ display: 'grid', gap: '0.6rem' }}>
                {platformFundResults.map((fund) => (
                  <div
                    key={fund.id}
                    className="compare-row"
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      cursor: 'pointer',
                      padding: '0.5rem',
                      borderRadius: '0.25rem',
                      transition: 'background 0.2s ease',
                    }}
                    onClick={() => {
                      setSelectedFund(fund);
                      setInputs((prev) => ({
                        ...prev,
                        annual_return: String(
                          fund.return_5y || prev.annual_return
                        ),
                      }));
                    }}
                  >
                    <span>{fund.name}</span>
                    <span className="text-accent">{fund.return_5y}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </GlassCard>
      </div>

      {/* Right Panel - Results */}
      <div className="dashboard-results">
        {results ? (
          <div className="animate-fade-in">
            <div className="stats-grid">
              <StatBox
                title="Ideal Wealth"
                value={formatINR(results.ideal_value)}
                icon={<TrendingUp size={24} color="#fff" />}
                gradient="var(--accent-gradient)"
              />
              <StatBox
                title="Actual Wealth"
                value={formatINR(results.actual_value)}
                icon={<Target size={24} color="#fff" />}
                gradient="var(--accent-gradient-alt)"
              />
              <StatBox
                title="Compounding Loss"
                value={formatINR(results.compounding_loss)}
                icon={<AlertCircle size={24} color="#fff" />}
                gradient="linear-gradient(135deg, #ef4444 0%, #f97316 100%)"
              />
              <StatBox
                title="Total Invested"
                value={formatINR(results.total_actual_contribution)}
                icon={<Wallet size={24} color="#fff" />}
                gradient="linear-gradient(135deg, #f59e0b 0%, #eab308 100%)"
              />
              <StatBox
                title="Discipline Score"
                value={results.discipline_score}
                icon={<Award size={24} color="#fff" />}
                gradient="linear-gradient(135deg, #8b5cf6 0%, #d946ef 100%)"
                suffix="/100"
              />
            </div>

            {results.ccr != null && <CCRBar ccr={results.ccr} />}

            <GlassCard
              className="chart-container"
              style={{ marginTop: '1.5rem', height: '400px' }}
              hoverEffect={false}
            >
              <h3 style={{ marginBottom: '1rem' }}>
                Wealth Accumulation Trajectory
              </h3>
              <p className="text-muted" style={{ marginBottom: '0.8rem' }}>
                Blue = ideal discipline | Red = actual with friction | Grey =
                loss
              </p>
              <ResponsiveContainer width="100%" height="82%">
                <AreaChart data={results.chart_data}>
                  <defs>
                    <linearGradient id="diffGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#f87171" stopOpacity={0.3} />
                      <stop
                        offset="100%"
                        stopColor="#f87171"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>
                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="var(--border-color)"
                  />
                  <XAxis
                    dataKey="year"
                    stroke="var(--text-muted)"
                    tickMargin={10}
                  />
                  <YAxis
                    stroke="var(--text-muted)"
                    tickFormatter={formatINRAxis}
                    width={80}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{ paddingTop: '10px' }} />

                  <Area
                    type="monotone"
                    dataKey="ideal"
                    name="Ideal (disciplined)"
                    stroke="#3b82f6"
                    strokeWidth={2.5}
                    fill="none"
                    dot={false}
                  />
                  <Area
                    type="monotone"
                    dataKey="actual"
                    name="Actual (with friction)"
                    stroke="#ef4444"
                    strokeWidth={2.5}
                    fill="none"
                    dot={false}
                  />

                  <Area
                    type="monotone"
                    dataKey="difference"
                    name="Friction Loss"
                    stroke="none"
                    fill="url(#diffGrad)"
                    isAnimationActive={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </GlassCard>
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-icon-wrap">
              <Activity size={48} className="text-muted empty-pulse" />
            </div>
            <p className="text-muted" style={{ marginTop: '1rem' }}>
              Configure your SIP and run a simulation to visualize the trajectory
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
