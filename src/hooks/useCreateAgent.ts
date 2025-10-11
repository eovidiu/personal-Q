/**
 * React Query mutation hook for creating a new agent
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { AgentCreate } from '@/types/agent';

export function useCreateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AgentCreate) => apiClient.createAgent(data),
    onSuccess: () => {
      // Invalidate agents list to refetch with new agent
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      // Also invalidate dashboard metrics as counts changed
      queryClient.invalidateQueries({ queryKey: ['metrics', 'dashboard'] });
    },
  });
}
