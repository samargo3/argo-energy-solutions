import { useQuery } from '@tanstack/react-query';
import { bestEnergyApi } from '../services/api/bestEnergyApi';
import type { PaginationParams } from '../types/api';

/**
 * Hook to fetch all customers
 */
export const useCustomers = (params?: PaginationParams) => {
  return useQuery({
    queryKey: ['customers', params],
    queryFn: () => bestEnergyApi.getCustomers(params),
  });
};

/**
 * Hook to fetch a single customer
 */
export const useCustomer = (customerId: string) => {
  return useQuery({
    queryKey: ['customer', customerId],
    queryFn: () => bestEnergyApi.getCustomer(customerId),
    enabled: !!customerId,
  });
};

/**
 * Hook to fetch customer sites
 */
export const useCustomerSites = (customerId: string) => {
  return useQuery({
    queryKey: ['customer', customerId, 'sites'],
    queryFn: () => bestEnergyApi.getCustomerSites(customerId),
    enabled: !!customerId,
  });
};

