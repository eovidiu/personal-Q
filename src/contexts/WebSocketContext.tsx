import React, { createContext, useContext, useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { wsClient, WebSocketClient } from '@/services/api';
import { useAuth } from '@/contexts/AuthContext';

interface WebSocketContextValue {
  client: WebSocketClient;
  isConnected: boolean;
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
}

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = React.useState(false);
  const queryClient = useQueryClient();
  const clientRef = useRef(wsClient);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    // Only connect WebSocket if user is authenticated
    if (!isAuthenticated) {
      return;
    }

    const client = clientRef.current;

    // Connect to WebSocket with JWT token
    client.connect();
    setIsConnected(true);

    // Subscribe to events
    client.subscribe([
      'agent_created',
      'agent_updated',
      'agent_deleted',
      'agent_status_changed',
      'task_completed',
      'activity_created',
    ]);

    // Event handlers
    client.on('agent_created', () => {
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      queryClient.invalidateQueries({ queryKey: ['metrics', 'dashboard'] });
    });

    client.on('agent_updated', (data: any) => {
      queryClient.setQueryData(['agent', data.id], data);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    });

    client.on('agent_deleted', (data: any) => {
      queryClient.removeQueries({ queryKey: ['agent', data.id] });
      queryClient.invalidateQueries({ queryKey: ['agents'] });
      queryClient.invalidateQueries({ queryKey: ['metrics', 'dashboard'] });
    });

    client.on('agent_status_changed', (data: any) => {
      queryClient.setQueryData(['agent', data.id], data);
      queryClient.invalidateQueries({ queryKey: ['agents'] });
    });

    client.on('task_completed', () => {
      queryClient.invalidateQueries({ queryKey: ['metrics'] });
    });

    client.on('activity_created', () => {
      queryClient.invalidateQueries({ queryKey: ['activities'] });
    });

    // Cleanup on unmount
    return () => {
      client.disconnect();
      setIsConnected(false);
    };
  }, [queryClient, isAuthenticated]);

  return (
    <WebSocketContext.Provider value={{ client: clientRef.current, isConnected }}>
      {children}
    </WebSocketContext.Provider>
  );
}
