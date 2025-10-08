/**
 * Metrics types
 */

export interface DashboardMetrics {
  total_agents: number;
  active_agents: number;
  tasks_completed: number;
  avg_success_rate: number;
  trends: {
    agents_change: string;
    tasks_change: string;
    success_rate_change: string;
  };
}

export interface AgentMetrics {
  agent_id: string;
  agent_name: string;
  tasks_completed: number;
  tasks_failed: number;
  success_rate: number;
  uptime: number;
  last_active?: string;
  pending_tasks: number;
  running_tasks: number;
  status: string;
}

export interface MemoryStatistics {
  conversations_count: number;
  outputs_count: number;
  documents_count: number;
  retention_days: number;
}
