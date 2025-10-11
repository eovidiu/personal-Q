import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "sonner";
import { queryClient } from "@/lib/query-client";
import { DashboardLayout } from "@/personal-q/layouts/dashboard-layout";
import { AgentsPage } from "@/personal-q/pages/agents-page";
import { AgentDetailPage } from "@/personal-q/pages/agent-detail-page";
import { SettingsPage } from "@/personal-q/pages/settings-page";

export default function AIAgentApp() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          <Route
            path="/"
            element={
              <DashboardLayout>
                <AgentsPage />
              </DashboardLayout>
            }
          />

          <Route
            path="/agents"
            element={
              <DashboardLayout>
                <AgentsPage />
              </DashboardLayout>
            }
          />

          <Route
            path="/agent/:id"
            element={
              <DashboardLayout>
                <AgentDetailPage />
              </DashboardLayout>
            }
          />

          <Route
            path="/settings"
            element={
              <DashboardLayout>
                <SettingsPage />
              </DashboardLayout>
            }
          />
        </Routes>
      </Router>
      <ReactQueryDevtools initialIsOpen={false} />
      <Toaster position="top-right" richColors />
    </QueryClientProvider>
  );
}
