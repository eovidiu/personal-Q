/**
 * React Query hooks for fetching metrics and statistics
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';

/**
 * Hook for fetching dashboard-level metrics
 * Used in AgentsPage for overall statistics display
 */
export function useDashboardMetrics() {
  return useQuery({
    queryKey: ['metrics', 'dashboard'],
    queryFn: () => apiClient.getDashboardMetrics(),
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Auto-refetch every minute
  });
}

/**
 * Hook for fetching agent-specific metrics
 * Used in AgentDetailPage for performance stats
 */
export function useAgentMetrics(agentId: string | undefined) {
  return useQuery({
    queryKey: ['metrics', 'agent', agentId],
    queryFn: () => apiClient.getAgentMetrics(agentId!),
    enabled: !!agentId,
    staleTime: 30000, // 30 seconds
    refetchInterval: 60000, // Auto-refetch every minute
  });
}

/**
 * Hook for fetching memory/ChromaDB statistics
 * Optional - for advanced metrics pages
 */
export function useMemoryStatistics() {
  return useQuery({
    queryKey: ['metrics', 'memory'],
    queryFn: () => apiClient.getMemoryStatistics(),
    staleTime: 60000, // 1 minute
  });
}
