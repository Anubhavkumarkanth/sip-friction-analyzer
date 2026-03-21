import React, { useState, useEffect, FC, ChangeEvent, MouseEvent } from 'react';
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
  ChartDataPoint,
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

