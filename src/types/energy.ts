// Energy consumption data types
export interface EnergyConsumption {
  id: string;
  siteId: string;
  customerId: string;
  timestamp: string;
  value: number; // kWh
  cost?: number; // in currency units
  unit?: string; // Default: 'kWh'
}

export interface EnergyConsumptionGrouped {
  date: string;
  value: number;
  cost?: number;
  peak?: number;
  average?: number;
}

export interface Site {
  id: string;
  customerId: string;
  name: string;
  address?: string;
  timezone?: string;
  metadata?: Record<string, unknown>;
}

export interface Customer {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  sites?: Site[];
  metadata?: Record<string, unknown>;
}

// Time series data for charts
export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number;
  label?: string;
}

// Energy statistics
export interface EnergyStatistics {
  totalConsumption: number;
  averageConsumption: number;
  peakConsumption: number;
  peakTimestamp?: string;
  minConsumption: number;
  minTimestamp?: string;
  cost?: number;
  averageCost?: number;
  period: {
    start: string;
    end: string;
  };
}

// Comparison data
export interface ComparisonData {
  current: EnergyStatistics;
  previous: EnergyStatistics;
  change: {
    consumption: number; // percentage change
    cost: number; // percentage change
  };
}

