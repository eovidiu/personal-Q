/**
 * React Query hook for fetching a single agent by ID
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';

export function useAgent(agentId: string | undefined) {
  return useQuery({
    queryKey: ['agent', agentId],
    queryFn: () => apiClient.getAgent(agentId!),
    enabled: !!agentId, // Only run query if agentId exists
    staleTime: 60000, // 1 minute
  });
}
