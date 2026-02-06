/**
 * Date utility functions for weekly report generation
 */

/**
 * Get the last complete week (Monday 00:00 to Sunday 23:59) in a given timezone
 * @param {string} timezone - IANA timezone (e.g., 'America/New_York')
 * @param {Date} referenceDate - Optional reference date (defaults to now)
 * @returns {{ start: Date, end: Date }}
 */
export function getLastCompleteWeek(timezone = 'America/New_York', referenceDate = new Date()) {
  // Calculate in local timezone, then convert to target timezone
  const now = new Date(referenceDate.toLocaleString('en-US', { timeZone: timezone }));
  
  // Find the most recent Monday 00:00
  const dayOfWeek = now.getDay(); // 0 = Sunday, 1 = Monday, etc.
  const daysToMonday = dayOfWeek === 0 ? 7 : dayOfWeek; // If Sunday, go back 7 days
  
  // Last Monday of the previous week
  const lastMonday = new Date(now);
  lastMonday.setDate(now.getDate() - daysToMonday - 7);
  lastMonday.setHours(0, 0, 0, 0);
  
  // Last Sunday 23:59:59
  const lastSunday = new Date(lastMonday);
  lastSunday.setDate(lastMonday.getDate() + 6);
  lastSunday.setHours(23, 59, 59, 999);
  
  return {
    start: lastMonday,
    end: lastSunday,
  };
}

/**
 * Get the baseline period (N weeks before the report week)
 * @param {Date} reportStart - Start of report week
 * @param {number} weeksCount - Number of weeks for baseline
 * @returns {{ start: Date, end: Date }}
 */
export function getBaselinePeriod(reportStart, weeksCount = 4) {
  const baselineEnd = new Date(reportStart);
  baselineEnd.setDate(baselineEnd.getDate() - 1); // Day before report week starts
  baselineEnd.setHours(23, 59, 59, 999);
  
  const baselineStart = new Date(baselineEnd);
  baselineStart.setDate(baselineStart.getDate() - (weeksCount * 7) + 1);
  baselineStart.setHours(0, 0, 0, 0);
  
  return {
    start: baselineStart,
    end: baselineEnd,
  };
}

/**
 * Format date as ISO string for API calls
 */
export function toISOString(date) {
  return date.toISOString();
}

/**
 * Format date as Unix timestamp (seconds)
 */
export function toUnixTimestamp(date) {
  return Math.floor(date.getTime() / 1000);
}

/**
 * Parse timestamp (handles both Unix seconds and ISO strings)
 */
export function parseTimestamp(ts) {
  if (typeof ts === 'number') {
    return new Date(ts * 1000); // Assume Unix seconds
  }
  return new Date(ts);
}

/**
 * Get hour of week (0-167) from a date
 * Monday 00:00 = 0, Sunday 23:00 = 167
 */
export function getHourOfWeek(date) {
  const dayOfWeek = date.getDay(); // 0 = Sunday
  const adjustedDay = dayOfWeek === 0 ? 6 : dayOfWeek - 1; // Monday = 0, Sunday = 6
  const hour = date.getHours();
  return adjustedDay * 24 + hour;
}

/**
 * Get day of week and hour from a date
 */
export function getDayAndHour(date) {
  const dayNames = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'];
  return {
    dayOfWeek: dayNames[date.getDay()],
    hour: date.getHours(),
  };
}

/**
 * Calculate interval duration in hours
 */
export function getIntervalHours(resolution) {
  // resolution is in seconds (900, 1800, 3600, etc.)
  return resolution / 3600;
}

/**
 * Generate an array of expected timestamps for a period
 */
export function generateExpectedTimestamps(start, end, intervalSeconds) {
  const timestamps = [];
  let current = new Date(start);
  
  while (current <= end) {
    timestamps.push(new Date(current));
    current = new Date(current.getTime() + intervalSeconds * 1000);
  }
  
  return timestamps;
}

/**
 * Format date for display (e.g., "Mon Jan 15, 2026 07:00")
 */
export function formatDisplayDate(date) {
  return date.toLocaleString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

/**
 * Format date range for display
 */
export function formatDateRange(start, end) {
  const startStr = start.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  
  const endStr = end.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  
  return `${startStr} - ${endStr}`;
}
