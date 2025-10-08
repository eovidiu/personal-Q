/**
 * Agent types
 */

export type AgentStatus = 'active' | 'inactive' | 'training' | 'error' | 'paused';
export type AgentType = 'conversational' | 'analytical' | 'creative' | 'automation';

export interface Agent {
  id: string;
  name: string;
  description: string;
  agent_type: AgentType;
  status: AgentStatus;
  model: string;
  temperature: number;
  max_tokens: number;
  system_prompt: string;
  tags: string[];
  avatar_url?: string;
  tasks_completed: number;
  tasks_failed: number;
  last_active?: string;
  tools_config: Record<string, any>;
  created_at: string;
  updated_at: string;
  success_rate: number;
  uptime: number;
}

export interface AgentCreate {
  name: string;
  description: string;
  agent_type: AgentType;
  model: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt: string;
  tags?: string[];
  avatar_url?: string;
  tools_config?: Record<string, any>;
}

export interface AgentUpdate {
  name?: string;
  description?: string;
  agent_type?: AgentType;
  model?: string;
  temperature?: number;
  max_tokens?: number;
  system_prompt?: string;
  tags?: string[];
  avatar_url?: string;
  tools_config?: Record<string, any>;
}

export interface AgentStatusUpdate {
  status: AgentStatus;
}

export interface AgentList {
  agents: Agent[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
