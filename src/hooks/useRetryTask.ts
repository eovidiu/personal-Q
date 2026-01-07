import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import { toast } from 'sonner';

export function useRetryTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (taskId: string) => apiClient.retryTask(taskId),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.setQueryData(['tasks', data.id], data);
      toast.success(`Task "${data.title}" queued for retry`);
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to retry task');
    },
  });
}
