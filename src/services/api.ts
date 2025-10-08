/**
 * API client for backend communication
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type { Agent, AgentCreate, AgentUpdate, AgentStatusUpdate } from '../types/agent';
import type { Task, TaskCreate } from '../types/task';
import type { Activity } from '../types/activity';
import type { DashboardMetrics, AgentMetrics } from '../types/metrics';
import type { APIKey, APIKeyCreate } from '../types/settings';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  // Agent endpoints
  async getAgents(params?: {
    page?: number;
    page_size?: number;
    status?: string;
    agent_type?: string;
    search?: string;
    tags?: string;
  }) {
    const response = await this.client.get('/agents', { params });
    return response.data;
  }

  async getAgent(id: string): Promise<Agent> {
    const response = await this.client.get(`/agents/${id}`);
    return response.data;
  }

  async createAgent(data: AgentCreate): Promise<Agent> {
    const response = await this.client.post('/agents', data);
    return response.data;
  }

  async updateAgent(id: string, data: AgentUpdate): Promise<Agent> {
    const response = await this.client.put(`/agents/${id}`, data);
    return response.data;
  }

  async updateAgentStatus(id: string, data: AgentStatusUpdate): Promise<Agent> {
    const response = await this.client.patch(`/agents/${id}/status`, data);
    return response.data;
  }

  async deleteAgent(id: string): Promise<void> {
    await this.client.delete(`/agents/${id}`);
  }

  // Task endpoints
  async getTasks(params?: {
    page?: number;
    page_size?: number;
    agent_id?: string;
    status?: string;
  }) {
    const response = await this.client.get('/tasks', { params });
    return response.data;
  }

  async getTask(id: string): Promise<Task> {
    const response = await this.client.get(`/tasks/${id}`);
    return response.data;
  }

  async createTask(data: TaskCreate): Promise<Task> {
    const response = await this.client.post('/tasks', data);
    return response.data;
  }

  // Activity endpoints
  async getActivities(params?: {
    page?: number;
    page_size?: number;
    agent_id?: string;
    activity_type?: string;
    status?: string;
  }) {
    const response = await this.client.get('/activities', { params });
    return response.data;
  }

  // Metrics endpoints
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const response = await this.client.get('/metrics/dashboard');
    return response.data;
  }

  async getAgentMetrics(agentId: string): Promise<AgentMetrics> {
    const response = await this.client.get(`/metrics/agent/${agentId}`);
    return response.data;
  }

  async getMemoryStatistics() {
    const response = await this.client.get('/metrics/memory');
    return response.data;
  }

  // Settings endpoints
  async getAPIKeys(): Promise<APIKey[]> {
    const response = await this.client.get('/settings/api-keys');
    return response.data;
  }

  async createOrUpdateAPIKey(data: APIKeyCreate): Promise<APIKey> {
    const response = await this.client.post('/settings/api-keys', data);
    return response.data;
  }

  async deleteAPIKey(serviceName: string): Promise<void> {
    await this.client.delete(`/settings/api-keys/${serviceName}`);
  }

  async testConnection(serviceName: string) {
    const response = await this.client.post('/settings/test-connection', {
      service_name: serviceName,
    });
    return response.data;
  }
}

// WebSocket client
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private eventHandlers: Map<string, Set<(data: any) => void>> = new Map();

  constructor(private url: string = `ws://localhost:8000/ws`) {}

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const { event_type, data } = message;

        if (event_type && this.eventHandlers.has(event_type)) {
          this.eventHandlers.get(event_type)?.forEach((handler) => handler(data));
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(eventTypes: string[]): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          action: 'subscribe',
          event_types: eventTypes,
        })
      );
    }
  }

  on(eventType: string, handler: (data: any) => void): void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    this.eventHandlers.get(eventType)?.add(handler);
  }

  off(eventType: string, handler: (data: any) => void): void {
    this.eventHandlers.get(eventType)?.delete(handler);
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      setTimeout(() => {
        console.log(`Reconnecting... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        this.connect();
      }, this.reconnectDelay * this.reconnectAttempts);
    }
  }
}

export const apiClient = new APIClient();
export const wsClient = new WebSocketClient();
export default apiClient;
