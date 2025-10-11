/**
 * React Query mutation hook for updating an agent's configuration
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { AgentUpdate } from '@/types/agent';

export function useUpdateAgent(agentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: AgentUpdate) => apiClient.updateAgent(agentId, data),
    onSuccess: (updatedAgent) => {
      // Update the specific agent in cache
      queryClient.setQueryData(['agent', agentId], updatedAgent);
      // Invalidate agents list to show updated data
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    },
  });
}
