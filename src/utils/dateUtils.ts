import { format, subDays, subMonths, subWeeks, startOfDay, endOfDay, parseISO } from 'date-fns';

/**
 * Format date for API requests (ISO 8601)
 */
export const formatDateForApi = (date: Date): string => {
  return date.toISOString();
};

/**
 * Get date range for common periods
 */
export const getDateRange = (period: 'today' | 'week' | 'month' | 'year' | 'custom', customStart?: Date, customEnd?: Date) => {
  const end = customEnd || new Date();
  let start: Date;

  switch (period) {
    case 'today':
      start = startOfDay(end);
      break;
    case 'week':
      start = subWeeks(end, 1);
      break;
    case 'month':
      start = subMonths(end, 1);
      break;
    case 'year':
      start = subMonths(end, 12);
      break;
    case 'custom':
      start = customStart || subMonths(end, 1);
      break;
    default:
      start = subMonths(end, 1);
  }

  return {
    startDate: formatDateForApi(start),
    endDate: formatDateForApi(end),
  };
};

/**
 * Format date for display
 */
export const formatDisplayDate = (date: string | Date, formatStr: string = 'MMM dd, yyyy'): string => {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, formatStr);
};

/**
 * Format date and time for display
 */
export const formatDateTime = (date: string | Date): string => {
  return formatDisplayDate(date, 'MMM dd, yyyy HH:mm');
};

/**
 * Get previous period for comparison
 */
export const getPreviousPeriod = (startDate: string, endDate: string) => {
  const start = parseISO(startDate);
  const end = parseISO(endDate);
  const duration = end.getTime() - start.getTime();
  
  return {
    startDate: formatDateForApi(new Date(start.getTime() - duration)),
    endDate: formatDateForApi(start),
  };
};

