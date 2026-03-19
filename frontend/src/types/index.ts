// ==================== Fund Types ====================
export interface Fund {
  id: number;
  name: string;
  category: string;
  risk_level: 'Low' | 'Medium' | 'High';
  return_1y?: number;
  return_3y: number;
  return_5y: number;
  expense_ratio: number;
  platform: 'Groww' | 'Zerodha' | 'Angel One';
  aum?: number;
  benchmark?: string;
  description?: string;
}

// ==================== SIP Simulation Types ====================
export type EventType = 'PAUSE_RANGE' | 'STEP_UP' | 'REDUCE' | 'SKIP' | 'INCREASE';

export interface FrictionEvent {
  id: number;
  type: EventType;
  month?: number;
  factor?: number;
  yearly_growth?: number;
  start_month?: number;
  end_month?: number;
}

export interface SIPInputs {
  monthly_amount: string;
  annual_return: string;
  years: string;
}

export interface ChartDataPoint {
  year: number;
  ideal: number;
  actual: number;
  difference: number;
}

export interface SimulationResult {
  ideal_value: number;
  actual_value: number;
  compounding_loss: number;
  discipline_score: number;
  ccr: number;
  total_expected_contribution: number;
  total_actual_contribution: number;
  chart_data: ChartDataPoint[];
}

