/**
 * React Query mutation hook for deleting an agent
 */

import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';

export function useDeleteAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (agentId: string) => apiClient.deleteAgent(agentId),
    onSuccess: (_, agentId) => {
      // Remove agent from cache
      queryClient.removeQueries({ queryKey: ['agent', agentId] });
      // Invalidate agents list to refetch without deleted agent
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      // Invalidate metrics as counts changed
      queryClient.invalidateQueries({ queryKey: ['metrics', 'dashboard'] });
    },
  });
}
