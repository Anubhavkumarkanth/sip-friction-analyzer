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

