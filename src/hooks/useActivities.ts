/**
 * React Query hooks for fetching agent activities
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';

interface UseActivitiesFilters {
  page?: number;
  page_size?: number;
  agent_id?: string;
  activity_type?: string;
  status?: string;
}

/**
 * Main activities hook with filters
 */
export function useActivities(filters?: UseActivitiesFilters) {
  return useQuery({
    queryKey: ['activities', filters],
    queryFn: () => apiClient.getActivities(filters),
    staleTime: 10000, // 10 seconds (activities change frequently)
    refetchInterval: 30000, // Auto-refetch every 30 seconds for real-time feel
  });
}

/**
 * Convenience hook for fetching activities for a specific agent
 */
export function useAgentActivities(agentId: string | undefined, limit: number = 20) {
  return useActivities({
    agent_id: agentId,
    page_size: limit,
  });
}
