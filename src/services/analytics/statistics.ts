import type { EnergyConsumption, EnergyStatistics, ComparisonData } from '../../types';

/**
 * Calculate statistics from energy consumption data
 */
export const calculateEnergyStatistics = (
  data: EnergyConsumption[],
  startDate: string,
  endDate: string
): EnergyStatistics => {
  if (data.length === 0) {
    return {
      totalConsumption: 0,
      averageConsumption: 0,
      peakConsumption: 0,
      minConsumption: 0,
      cost: 0,
      averageCost: 0,
      period: { start: startDate, end: endDate },
    };
  }

  const values = data.map((d) => d.value);
  const costs = data.map((d) => d.cost || 0).filter((c) => c > 0);

  const totalConsumption = values.reduce((sum, val) => sum + val, 0);
  const averageConsumption = totalConsumption / values.length;
  const peakConsumption = Math.max(...values);
  const minConsumption = Math.min(...values);
  
  const peakIndex = values.indexOf(peakConsumption);
  const minIndex = values.indexOf(minConsumption);

  const totalCost = costs.reduce((sum, cost) => sum + cost, 0);
  const averageCost = costs.length > 0 ? totalCost / costs.length : 0;

  return {
    totalConsumption,
    averageConsumption,
    peakConsumption,
    peakTimestamp: data[peakIndex]?.timestamp,
    minConsumption,
    minTimestamp: data[minIndex]?.timestamp,
    cost: totalCost,
    averageCost,
    period: { start: startDate, end: endDate },
  };
};

/**
 * Compare two periods of energy data
 */
export const comparePeriods = (
  current: EnergyStatistics,
  previous: EnergyStatistics
): ComparisonData => {
  const consumptionChange = previous.totalConsumption > 0
    ? ((current.totalConsumption - previous.totalConsumption) / previous.totalConsumption) * 100
    : 0;

  const costChange = previous.cost && previous.cost > 0
    ? ((current.cost! - previous.cost) / previous.cost) * 100
    : 0;

  return {
    current,
    previous,
    change: {
      consumption: consumptionChange,
      cost: costChange,
    },
  };
};

/**
 * Calculate percentage change
 */
export const calculatePercentageChange = (current: number, previous: number): number => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
};

/**
 * Detect anomalies in consumption data
 */
export const detectAnomalies = (data: EnergyConsumption[], threshold: number = 2): EnergyConsumption[] => {
  if (data.length === 0) return [];

  const values = data.map((d) => d.value);
  const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length;
  const stdDev = Math.sqrt(variance);

  return data.filter((d) => {
    const zScore = Math.abs((d.value - mean) / stdDev);
    return zScore > threshold;
  });
};

/**
 * Group consumption by time periods
 */
export const groupByPeriod = (
  data: EnergyConsumption[],
  period: 'hour' | 'day' | 'week' | 'month'
): Record<string, EnergyConsumption[]> => {
  const groups: Record<string, EnergyConsumption[]> = {};

  data.forEach((item) => {
    const date = new Date(item.timestamp);
    let key: string;

    switch (period) {
      case 'hour':
        key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}`;
        break;
      case 'day':
        key = `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
        break;
      case 'week':
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay());
        key = `${weekStart.getFullYear()}-W${Math.ceil(weekStart.getDate() / 7)}`;
        break;
      case 'month':
        key = `${date.getFullYear()}-${date.getMonth()}`;
        break;
      default:
        key = date.toISOString().split('T')[0];
    }

    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
  });

  return groups;
};

