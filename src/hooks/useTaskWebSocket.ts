/**
 * Hook to subscribe to task-related WebSocket events
 */
import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { wsClient } from '@/services/api';
import { toast } from 'sonner';

export function useTaskWebSocket() {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Handler for task status updates
    const handleTaskStarted = (data: any) => {
      console.log(`Task started: ${data.task_id} - ${data.title}`, data);

      // Invalidate tasks list to show updated status
      queryClient.invalidateQueries({ queryKey: ['tasks'] });

      // Update specific task in cache if exists
      queryClient.setQueryData(['tasks', data.task_id], (old: any) => ({
        ...old,
        status: 'running',
        started_at: data.started_at,
      }));

      toast.info(`Task "${data.title}" started`);
    };

    const handleTaskCompleted = (data: any) => {
      console.log('Task completed:', data);

      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['metrics', 'dashboard'] });

      toast.success(`Task "${data.title}" completed successfully`);
    };

    const handleTaskFailed = (data: any) => {
      console.log('Task failed:', data);

      queryClient.invalidateQueries({ queryKey: ['tasks'] });
      queryClient.invalidateQueries({ queryKey: ['metrics', 'dashboard'] });

      toast.error(`Task "${data.title}" failed: ${data.error_message}`);
    };

    const handleTaskCancelled = (data: any) => {
      console.log('Task cancelled:', data);

      queryClient.invalidateQueries({ queryKey: ['tasks'] });

      toast.info(`Task "${data.title}" was cancelled`);
    };

    // Subscribe to events
    wsClient.on('task_started', handleTaskStarted);
    wsClient.on('task_completed', handleTaskCompleted);
    wsClient.on('task_failed', handleTaskFailed);
    wsClient.on('task_cancelled', handleTaskCancelled);

    // Subscribe via WebSocket protocol
    wsClient.subscribe(['task_started', 'task_completed', 'task_failed', 'task_cancelled']);

    // Cleanup
    return () => {
      wsClient.off('task_started', handleTaskStarted);
      wsClient.off('task_completed', handleTaskCompleted);
      wsClient.off('task_failed', handleTaskFailed);
      wsClient.off('task_cancelled', handleTaskCancelled);
    };
  }, [queryClient]);
}
