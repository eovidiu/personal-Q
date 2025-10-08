/**
 * Task types
 */

export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export interface Task {
  id: string;
  agent_id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  input_data: Record<string, any>;
  output_data?: Record<string, any>;
  error_message?: string;
  celery_task_id?: string;
  execution_time_seconds?: number;
  retry_count: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  updated_at: string;
}

export interface TaskCreate {
  agent_id: string;
  title: string;
  description?: string;
  priority?: TaskPriority;
  input_data?: Record<string, any>;
}

export interface TaskList {
  tasks: Task[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
