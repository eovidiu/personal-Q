/**
 * React Query mutation hook for updating an agent's status
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { AgentStatusUpdate } from '@/types/agent';

export function useUpdateAgentStatus(agentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AgentStatusUpdate) => apiClient.updateAgentStatus(agentId, data),
    onSuccess: (updatedAgent) => {
      // Update the specific agent in cache
      queryClient.setQueryData(['agent', agentId], updatedAgent);
      // Invalidate agents list to show updated status
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      // Invalidate dashboard metrics as active count may have changed
      queryClient.invalidateQueries({ queryKey: ['metrics', 'dashboard'] });
    },
  });
}
