/**
 * React Query hook for fetching agents list with filters
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { AgentStatus, AgentType } from '@/types/agent';

interface UseAgentsFilters {
  page?: number;
  page_size?: number;
  status?: AgentStatus;
  agent_type?: AgentType;
  search?: string;
  tags?: string;
}

export function useAgents(filters?: UseAgentsFilters) {
  return useQuery({
    queryKey: ['agents', filters],
    queryFn: () => apiClient.getAgents(filters),
    staleTime: 30000, // 30 seconds
  });
}
