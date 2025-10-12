/**
 * React Query hook for fetching tasks
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { TaskStatus } from '@/types/task';

interface UseTasksParams {
  page?: number;
  page_size?: number;
  agent_id?: string;
  status?: TaskStatus;
}

export function useTasks(params?: UseTasksParams) {
  return useQuery({
    queryKey: ['tasks', params],
    queryFn: () => apiClient.getTasks(params),
    staleTime: 30000, // 30 seconds (tasks change frequently)
  });
}
