/**
 * Weekly Report Configuration
 * 
 * Central configuration for the Weekly Exceptions & Opportunities Brief
 */

export const DEFAULT_CONFIG = {
  // Timezone for report calculations
  timezone: 'America/New_York',
  
  // Business hours schedule (24-hour format)
  businessHours: {
    monday: { start: 7, end: 18 },
    tuesday: { start: 7, end: 18 },
    wednesday: { start: 7, end: 18 },
    thursday: { start: 7, end: 18 },
    friday: { start: 7, end: 18 },
    saturday: null, // null means all day after-hours
    sunday: null,
  },
  
  // Data resolution preferences (in seconds)
  intervalPreferences: [900, 1800, 3600], // 15min, 30min, 60min
  
  // Baseline calculation parameters
  baseline: {
    // Number of weeks to use for baseline (4 weeks = 1 month history)
    weeksCount: 4,
    // Minimum data completeness required for baseline (%)
    minCompleteness: 70,
  },
  
  // Sensor/communications issue detection thresholds
  sensorHealth: {
    // Gap detection: missing data threshold (multiplier of interval length)
    gapMultiplier: 2,
    // Stale meter: hours since last data for "current" checks
    staleHours: 2,
    // Missing data threshold for weekly context (% of expected intervals)
    missingThresholdPct: 10,
    // Flatline detection: hours with near-zero variance
    flatlineHours: 6,
    // Variance threshold for flatline (kW)
    flatlineVarianceThreshold: 0.01,
  },
  
  // After-hours waste detection
  afterHours: {
    // Percentile for baseline after-hours load (5th = low-but-running)
    baselinePercentile: 5,
    // Minimum kW to exclude from analysis (filter noise)
    minPowerThreshold: 0.1,
    // Minimum excess kWh to flag as significant
    minExcessKwh: 10,
  },
  
  // Anomaly detection parameters
  anomaly: {
    // Statistical threshold: median + (IQR * multiplier)
    iqrMultiplier: 3,
    // Z-score threshold (alternative method)
    zScoreThreshold: 3,
    // Minimum consecutive intervals to flag as anomaly
    minConsecutiveIntervals: 3,
    // Minimum excess kWh to report
    minExcessKwh: 5,
  },
  
  // Spike detection parameters
  spike: {
    // Percentile for "normal" baseline
    baselinePercentile: 95,
    // Multiplier above baseline to flag spike
    multiplier: 1.5,
    // Absolute minimum threshold for submeters (kW)
    submeterMinKw: 5,
    // Absolute minimum threshold for site total (kW)
    siteMinKw: 20,
    // Minimum duration (intervals) to report
    minDuration: 1,
  },
  
  // Quick wins generation
  quickWins: {
    // Maximum number of recommendations to generate
    maxCount: 10,
    // Minimum weekly kWh impact to suggest
    minWeeklyImpact: 10,
  },
  
  // Energy cost ($/kWh) - optional, for $ calculations
  tariff: {
    defaultRate: 0.12, // $0.12/kWh default
    demandCharge: null, // $/kW if applicable
  },
  
  // Report output options
  output: {
    includeCharts: true,
    includeRawData: false,
    precision: 2, // decimal places for numbers
  },
};

/**
 * Merge user config with defaults
 */
export function mergeConfig(userConfig = {}) {
  return {
    ...DEFAULT_CONFIG,
    ...userConfig,
    businessHours: {
      ...DEFAULT_CONFIG.businessHours,
      ...(userConfig.businessHours || {}),
    },
    baseline: {
      ...DEFAULT_CONFIG.baseline,
      ...(userConfig.baseline || {}),
    },
    sensorHealth: {
      ...DEFAULT_CONFIG.sensorHealth,
      ...(userConfig.sensorHealth || {}),
    },
    afterHours: {
      ...DEFAULT_CONFIG.afterHours,
      ...(userConfig.afterHours || {}),
    },
    anomaly: {
      ...DEFAULT_CONFIG.anomaly,
      ...(userConfig.anomaly || {}),
    },
    spike: {
      ...DEFAULT_CONFIG.spike,
      ...(userConfig.spike || {}),
    },
    quickWins: {
      ...DEFAULT_CONFIG.quickWins,
      ...(userConfig.quickWins || {}),
    },
    tariff: {
      ...DEFAULT_CONFIG.tariff,
      ...(userConfig.tariff || {}),
    },
    output: {
      ...DEFAULT_CONFIG.output,
      ...(userConfig.output || {}),
    },
  };
}

/**
 * Check if a timestamp is during business hours
 */
export function isBusinessHours(date, config = DEFAULT_CONFIG) {
  const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  const dayName = dayNames[date.getDay()];
  const hours = config.businessHours[dayName];
  
  if (!hours) return false; // null means all day after-hours
  
  const hour = date.getHours();
  return hour >= hours.start && hour < hours.end;
}

/**
 * Get the day of week name from a date
 */
export function getDayOfWeek(date) {
  const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  return dayNames[date.getDay()];
}
