/**
 * React Query hook for fetching a single task by ID
 */
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';

interface UseTaskOptions {
  enabled?: boolean;
}

export function useTask(taskId: string | undefined, options?: UseTaskOptions) {
  return useQuery({
    queryKey: ['tasks', taskId],
    queryFn: () => {
      if (!taskId) {
        throw new Error('Task ID is required');
      }
      return apiClient.getTask(taskId);
    },
    enabled: options?.enabled ?? !!taskId,
    staleTime: 30000, // 30 seconds
  });
}
