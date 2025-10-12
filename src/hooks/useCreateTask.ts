/**
 * React Query mutation hook for creating tasks
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { TaskCreate } from '@/types/task';

export function useCreateTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: TaskCreate) => apiClient.createTask(data),
    onSuccess: () => {
      // Invalidate tasks list to refetch
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      // Also invalidate dashboard metrics as task counts may have changed
      queryClient.invalidateQueries({ queryKey: ['metrics', 'dashboard'] });
    },
  });
}
