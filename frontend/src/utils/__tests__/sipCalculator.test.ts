import { calculateSIPSimulation } from '../sipCalculator';

describe('SIP Calculator', () => {
  describe('calculateSIPSimulation', () => {
    it('should calculate basic SIP for 1 year with 12% annual return', () => {
      const { result } = calculateSIPSimulation(10000, 12, 1);

      expect(result.total_expected_contribution).toBe(120000);
      expect(result.total_actual_contribution).toBe(120000);
      expect(result.ccr).toBe(1); // 100% contribution compliance
      expect(result.discipline_score).toBe(100); // Perfect discipline
    });

    it('should calculate SIP for 20 years', () => {
      const { result, chartData } = calculateSIPSimulation(10000, 12, 20);

      expect(chartData.length).toBe(20);
      expect(result.chart_data.length).toBe(20);
      expect(result.total_expected_contribution).toBe(2400000); // 10000 * 240 months
      expect(result.ideal_value).toBeGreaterThan(result.total_expected_contribution);
    });

    it('should have positive wealth accumulation', () => {
      const { result } = calculateSIPSimulation(5000, 10, 10);

      expect(result.ideal_value).toBeGreaterThan(0);
      expect(result.actual_value).toBeGreaterThan(0);
      expect(result.ideal_value).toBeCloseTo(result.actual_value, 2); // No friction = identical
    });

    it('should handle 0% annual return', () => {
      const { result } = calculateSIPSimulation(1000, 0, 5);
      expect(result.ideal_value).toBeCloseTo(60000, 1); // 1000 * 60 months
      expect(result.compounding_loss).toBe(0);
    });

    it('should calculate chart data points correctly', () => {
      const { chartData } = calculateSIPSimulation(10000, 12, 3);

      expect(chartData).toHaveLength(3);
      chartData.forEach((point, index) => {
        expect(point.year).toBe(index + 1);
        expect(point.ideal).toBeGreaterThan(0);
        expect(point.actual).toBeGreaterThan(0);
      });
    });

    it('should have increasing wealth over time', () => {
      const { chartData } = calculateSIPSimulation(10000, 15, 5);

      for (let i = 1; i < chartData.length; i++) {
        expect(chartData[i].ideal).toBeGreaterThan(chartData[i - 1].ideal);
        expect(chartData[i].actual).toBeGreaterThan(chartData[i - 1].actual);
      }
    });
  });

  describe('Edge cases', () => {
    it('should handle large return rates', () => {
      const { result } = calculateSIPSimulation(1000, 30, 10);
      expect(result.ideal_value).toBeGreaterThan(0);
      expect(isFinite(result.ideal_value)).toBe(true);
    });

    it('should maintain CCR = 1 when there is no friction', () => {
      const { result } = calculateSIPSimulation(5000, 10, 15);
      expect(result.ccr).toBe(1);
    });
  });
});
