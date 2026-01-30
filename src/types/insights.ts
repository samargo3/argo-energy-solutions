// Insight and recommendation types
export interface Insight {
  id: string;
  type: InsightType;
  severity: InsightSeverity;
  title: string;
  description: string;
  recommendation?: string;
  customerId?: string;
  siteId?: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export type InsightType = 
  | 'consumption_spike'
  | 'consumption_drop'
  | 'cost_optimization'
  | 'efficiency_improvement'
  | 'maintenance_alert'
  | 'usage_pattern'
  | 'anomaly';

export type InsightSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  impact: {
    savings?: number;
    efficiency?: number;
    type: 'cost' | 'energy' | 'both';
  };
  priority: 'low' | 'medium' | 'high';
  actionable: boolean;
}

