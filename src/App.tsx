import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { DashboardLayout } from "@/personal-q/layouts/dashboard-layout";
import { AgentsPage } from "@/personal-q/pages/agents-page";
import { AgentDetailPage } from "@/personal-q/pages/agent-detail-page";

export default function AIAgentApp() {
  return (
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
      </Routes>
    </Router>
  );
}
