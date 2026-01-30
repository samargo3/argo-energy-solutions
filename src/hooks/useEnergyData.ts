import { useQuery } from '@tanstack/react-query';
import { bestEnergyApi } from '../services/api/bestEnergyApi';
import type { DateRangeParams, PaginationParams } from '../types/api';
import { getDateRange } from '../utils/dateUtils';

/**
 * Hook to fetch customer energy consumption data
 */
export const useCustomerEnergyData = (
  customerId: string,
  params?: DateRangeParams & PaginationParams
) => {
  return useQuery({
    queryKey: ['energy', 'customer', customerId, params],
    queryFn: () => bestEnergyApi.getCustomerEnergyConsumption(customerId, params || getDateRange('month')),
    enabled: !!customerId,
  });
};

/**
 * Hook to fetch site energy consumption data
 */
export const useSiteEnergyData = (
  siteId: string,
  params?: DateRangeParams & PaginationParams
) => {
  return useQuery({
    queryKey: ['energy', 'site', siteId, params],
    queryFn: () => bestEnergyApi.getSiteEnergyConsumption(siteId, params || getDateRange('month')),
    enabled: !!siteId,
  });
};

/**
 * Hook to fetch grouped energy consumption data
 */
export const useGroupedEnergyData = (
  customerId: string,
  params?: DateRangeParams & { groupBy?: 'day' | 'week' | 'month' }
) => {
  return useQuery({
    queryKey: ['energy', 'grouped', customerId, params],
    queryFn: () => bestEnergyApi.getGroupedEnergyConsumption(customerId, params || { ...getDateRange('month'), groupBy: 'day' }),
    enabled: !!customerId,
  });
};

