/**
 * Activity types
 */

export type ActivityType =
  | 'agent_created'
  | 'agent_updated'
  | 'agent_deleted'
  | 'agent_started'
  | 'agent_stopped'
  | 'task_created'
  | 'task_started'
  | 'task_completed'
  | 'task_failed'
  | 'task_cancelled'
  | 'integration_connected'
  | 'integration_error';

export type ActivityStatus = 'success' | 'error' | 'info' | 'warning';

export interface Activity {
  id: string;
  agent_id?: string;
  task_id?: string;
  activity_type: ActivityType;
  status: ActivityStatus;
  title: string;
  description?: string;
  metadata: Record<string, any>;
  created_at: string;
}

export interface ActivityList {
  activities: Activity[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
