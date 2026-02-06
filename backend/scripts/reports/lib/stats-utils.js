/**
 * Statistical utility functions for analytics
 */

/**
 * Calculate basic statistics for an array of numbers
 */
export function calculateStats(values) {
  if (!values || values.length === 0) {
    return {
      count: 0,
      sum: 0,
      mean: 0,
      min: 0,
      max: 0,
      median: 0,
      std: 0,
    };
  }
  
  const sorted = [...values].sort((a, b) => a - b);
  const sum = values.reduce((a, b) => a + b, 0);
  const mean = sum / values.length;
  
  // Variance and standard deviation
  const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length;
  const std = Math.sqrt(variance);
  
  // Median
  const mid = Math.floor(sorted.length / 2);
  const median = sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
  
  return {
    count: values.length,
    sum,
    mean,
    min: sorted[0],
    max: sorted[sorted.length - 1],
    median,
    std,
  };
}

/**
 * Calculate percentile of an array
 */
export function percentile(values, p) {
  if (!values || values.length === 0) return 0;
  
  const sorted = [...values].sort((a, b) => a - b);
  const index = (p / 100) * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  const weight = index % 1;
  
  if (lower === upper) return sorted[lower];
  
  return sorted[lower] * (1 - weight) + sorted[upper] * weight;
}

/**
 * Calculate interquartile range (IQR)
 */
export function calculateIQR(values) {
  if (!values || values.length === 0) return 0;
  
  const q1 = percentile(values, 25);
  const q3 = percentile(values, 75);
  
  return {
    q1,
    q3,
    iqr: q3 - q1,
  };
}

/**
 * Calculate z-score for a value
 */
export function zScore(value, mean, std) {
  if (std === 0) return 0;
  return (value - mean) / std;
}

/**
 * Filter out zeros and calculate percentile of non-zero values
 */
export function nonZeroPercentile(values, p) {
  const nonZero = values.filter(v => v > 0);
  return percentile(nonZero, p);
}

/**
 * Group values by a key function
 */
export function groupBy(array, keyFn) {
  return array.reduce((acc, item) => {
    const key = keyFn(item);
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});
}

/**
 * Calculate rolling statistics over a window
 */
export function rollingStats(values, windowSize) {
  const results = [];
  
  for (let i = windowSize - 1; i < values.length; i++) {
    const window = values.slice(i - windowSize + 1, i + 1);
    results.push({
      index: i,
      ...calculateStats(window),
    });
  }
  
  return results;
}

/**
 * Calculate rolling variance over a window
 */
export function rollingVariance(values, windowSize) {
  const results = [];
  
  for (let i = windowSize - 1; i < values.length; i++) {
    const window = values.slice(i - windowSize + 1, i + 1);
    const stats = calculateStats(window);
    results.push({
      index: i,
      variance: stats.std * stats.std,
      std: stats.std,
      mean: stats.mean,
    });
  }
  
  return results;
}

/**
 * Detect outliers using IQR method
 */
export function detectOutliers(values, multiplier = 1.5) {
  const { q1, q3, iqr } = calculateIQR(values);
  const lowerBound = q1 - multiplier * iqr;
  const upperBound = q3 + multiplier * iqr;
  
  return values.map((value, index) => ({
    value,
    index,
    isOutlier: value < lowerBound || value > upperBound,
    lowerBound,
    upperBound,
  }));
}

/**
 * Calculate completeness percentage
 */
export function calculateCompleteness(actualCount, expectedCount) {
  if (expectedCount === 0) return 0;
  return (actualCount / expectedCount) * 100;
}

/**
 * Find gaps in a time series
 */
export function findGaps(timestamps, expectedIntervalSeconds) {
  const gaps = [];
  
  for (let i = 1; i < timestamps.length; i++) {
    const prevTime = new Date(timestamps[i - 1]).getTime();
    const currTime = new Date(timestamps[i]).getTime();
    const actualInterval = (currTime - prevTime) / 1000;
    const expectedInterval = expectedIntervalSeconds;
    
    // Allow 10% tolerance
    if (actualInterval > expectedInterval * 1.1) {
      gaps.push({
        start: timestamps[i - 1],
        end: timestamps[i],
        expectedIntervals: Math.round(actualInterval / expectedInterval),
        actualInterval,
        missingIntervals: Math.round(actualInterval / expectedInterval) - 1,
      });
    }
  }
  
  return gaps;
}

/**
 * Aggregate values by time period (hour of day, day of week, etc.)
 */
export function aggregateByPeriod(dataPoints, periodFn, valueFn) {
  const grouped = groupBy(dataPoints, periodFn);
  
  const result = {};
  for (const [period, points] of Object.entries(grouped)) {
    const values = points.map(valueFn).filter(v => v != null);
    result[period] = calculateStats(values);
  }
  
  return result;
}
