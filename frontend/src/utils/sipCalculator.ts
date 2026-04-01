import { ChartDataPoint, SimulationResult } from '../types';

/**
 * Calculate SIP simulation results
 * Used for testing and validation
 */
export function calculateSIPSimulation(
  monthlyAmount: number,
  annualReturn: number,
  years: number
): {result: SimulationResult; chartData: ChartDataPoint[]} {
  const monthlyReturn = annualReturn / 100 / 12;
  const totalMonths = Math.floor(years * 12);

  let idealValue = 0;
  let actualValue = 0;
  let totalExpected = 0;
  let totalActual = 0;
  const chartData: ChartDataPoint[] = [];

  for (let month = 1; month <= totalMonths; month++) {
    // Ideal calculation (no friction)
    idealValue = (idealValue + monthlyAmount) * (1 + monthlyReturn);

    // Actual calculation (same as ideal without events)
    const contribution = monthlyAmount;
    totalExpected += monthlyAmount;
    totalActual += contribution;
    actualValue = (actualValue + contribution) * (1 + monthlyReturn);

    // Record annual data
    if (month % 12 === 0) {
      chartData.push({
        year: month / 12,
        ideal: Math.round(idealValue * 100) / 100,
        actual: Math.round(actualValue * 100) / 100,
        difference: 0, // No difference when no friction events
      });
    }
  }

  // Calculate metrics
  const cld = 0; // No compounding loss without friction
  const ccr = totalExpected > 0 ? totalActual / totalExpected : 1;
  const disciplineScore = 100; // Perfect discipline without friction

  const result: SimulationResult = {
    ideal_value: Math.round(idealValue * 100) / 100,
    actual_value: Math.round(actualValue * 100) / 100,
    compounding_loss: cld,
    discipline_score: disciplineScore,
    ccr: Math.round(ccr * 10000) / 10000,
    total_expected_contribution: Math.round(totalExpected * 100) / 100,
    total_actual_contribution: Math.round(totalActual * 100) / 100,
    chart_data: chartData,
  };

  return { result, chartData };
}
