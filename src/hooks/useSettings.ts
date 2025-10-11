/**
 * React Query hooks for Settings API
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { APIKeyCreate } from '@/types/settings';

/**
 * Fetch all API keys (masked)
 */
export function useAPIKeys() {
  return useQuery({
    queryKey: ['settings', 'api-keys'],
    queryFn: () => apiClient.getAPIKeys(),
    staleTime: 60000, // 1 minute
  });
}

/**
 * Create or update an API key
 */
export function useCreateOrUpdateAPIKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: APIKeyCreate) => apiClient.createOrUpdateAPIKey(data),
    onSuccess: () => {
      // Invalidate API keys list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['settings', 'api-keys'] });
    },
  });
}

/**
 * Delete an API key
 */
export function useDeleteAPIKey() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (serviceName: string) => apiClient.deleteAPIKey(serviceName),
    onSuccess: () => {
      // Invalidate API keys list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['settings', 'api-keys'] });
    },
  });
}

/**
 * Test API connection for a service
 */
export function useTestConnection() {
  return useMutation({
    mutationFn: (serviceName: string) => apiClient.testConnection(serviceName),
  });
}
