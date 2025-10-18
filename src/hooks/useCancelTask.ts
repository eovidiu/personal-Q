import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import { toast } from 'sonner';

export function useCancelTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => apiClient.cancelTask(taskId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.setQueryData(['tasks', data.id], data);
      toast.success(`Task "${data.title}" cancelled`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to cancel task');
    },
  });
}
