import React from 'react';

// ==================== Fund Types ====================
export interface Fund {
  id: number;
  name: string;
  category: string;
  platform: string;
  risk_level: string;
  return_3y: number;
  return_5y: number;
  expense_ratio: number;
  invest_url: string;
}

// ==================== SIP Simulation Types ====================
export type EventType = 'PAUSE_RANGE' | 'STEP_UP' | 'REDUCE' | 'SKIP' | 'INCREASE';

/**
 * A friction event as the UI holds it.
 *
 * `id` is required and client-only: it exists so React can key the list and so
 * an event can be edited or removed before the simulation is run. It is
 * stripped before the request is sent, which is what `SimulationEventInput`
 * below describes.
 */
export interface FrictionEvent {
  id: number;
  type: EventType;
  month?: number;
  factor?: number;
  yearly_growth?: number;
  start_month?: number;
  end_month?: number;
}

/** A friction event as the API accepts it, without the client-only id. */
export type SimulationEventInput = Omit<FrictionEvent, 'id'>;

export interface SIPInputs {
  monthly_amount: string;
  annual_return: string;
  years: string;
}

export interface ChartDataPoint {
  year: number;
  ideal: number;
  actual: number;
  /** ideal - actual, supplied by the API and shaded on the chart. */
  difference: number;
}

export interface SimulationResult {
  simulation_id: number;
  ideal_value: number;
  actual_value: number;
  compounding_loss: number;
  discipline_score: number;
  ccr: number;
  total_expected_contribution: number;
  total_actual_contribution: number;
  chart_data: ChartDataPoint[];
}

export interface SimulationRequest {
  monthly_amount: number;
  annual_return: number;
  years: number;
  events?: SimulationEventInput[];
}

// ==================== Saved Simulations ====================
export interface SimulationSummary {
  id: number;
  created_at: string;
  monthly_amount: number;
  annual_return: number;
  years: number;
  ideal_value: number;
  actual_value: number;
  compounding_loss: number;
  discipline_score: number;
  ccr: number;
  event_count: number;
}

export interface SimulationDetail extends SimulationSummary {
  events: SimulationEventInput[];
}

// ==================== Auth ====================
export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface MonteCarloRequest extends SimulationRequest {
  simulations?: number;
  volatility?: number;
}

export interface MonteCarloResult {
  mean: number;
  p10: number;
  p50: number;
  p90: number;
  best_case: number;
  worst_case: number;
}

// ==================== Component Props Types ====================
export interface StatBoxProps {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  gradient: string;
  prefix?: string;
  suffix?: string;
}

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  className?: string;
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
}

export interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
  style?: React.CSSProperties;
}
