import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "sonner";
import { queryClient } from "@/lib/query-client";
import { AuthProvider } from "@/contexts/AuthContext";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { ErrorBoundary } from "@/components/error-boundary";
import { DashboardLayout } from "@/personal-q/layouts/dashboard-layout";
import { DashboardPage } from "@/personal-q/pages/dashboard-page";
import { AgentsPage } from "@/personal-q/pages/agents-page";
import { AgentDetailPage } from "@/personal-q/pages/agent-detail-page";
import { TasksPage } from "@/personal-q/pages/tasks-page";
import { SettingsPage } from "@/personal-q/pages/settings-page";
import { LoginPage } from "@/personal-q/pages/login-page";
import { AuthCallbackPage } from "@/personal-q/pages/auth-callback-page";

export default function AIAgentApp() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <WebSocketProvider>
          <Router>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/auth/callback" element={<AuthCallbackPage />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <DashboardPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/agents"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <AgentsPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/agent/:id"
              element={
                <ProtectedRoute>
                  <DashboardLayout>
                    <AgentDetailPage />
                  </DashboardLayout>
                </ProtectedRoute>
              }
            />

            <Route
              path="/tasks"
              element={
                <ProtectedRoute>
                  <ErrorBoundary>
                    <DashboardLayout>
                      <TasksPage />
                    </DashboardLayout>
                  </ErrorBoundary>
                </ProtectedRoute>
              }
            />

            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <ErrorBoundary>
                    <DashboardLayout>
                      <SettingsPage />
                    </DashboardLayout>
                  </ErrorBoundary>
                </ProtectedRoute>
              }
            />
            </Routes>
          </Router>
          <ReactQueryDevtools initialIsOpen={false} />
          <Toaster position="top-right" richColors />
        </WebSocketProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}
