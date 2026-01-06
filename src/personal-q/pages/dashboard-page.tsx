import { useState } from "react";
import { AgentStats } from "@/personal-q/components/agent-stats";
import { AgentList } from "@/personal-q/components/agent-list";
import { AgentActivity } from "@/personal-q/components/agent-activity";
import { AgentForm } from "@/personal-q/components/agent-form";
import { useAgents } from "@/hooks/useAgents";
import { useActivities } from "@/hooks/useActivities";
import { useDashboardMetrics } from "@/hooks/useMetrics";
import { useCreateAgent } from "@/hooks/useCreateAgent";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

/**
 * DashboardPage - Overview of the entire system
 *
 * Shows:
 * - Metrics (total agents, active agents, tasks completed, success rate)
 * - Recent agents (first 6)
 * - Recent activity
 *
 * This is the main landing page after login.
 */
export function DashboardPage() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  // Fetch data using React Query hooks
  const { data: agentsData, isLoading: agentsLoading, error: agentsError } = useAgents();
  const { data: metricsData, isLoading: metricsLoading } = useDashboardMetrics();
  const { data: activitiesData, isLoading: activitiesLoading } = useActivities({ page_size: 10 });
  const createAgentMutation = useCreateAgent();

  // Handle create agent submission
  const handleCreateAgent = async (data: any) => {
    try {
      await createAgentMutation.mutateAsync(data);
      setIsCreateDialogOpen(false);
    } catch (error) {
      console.error("Failed to create agent:", error);
    }
  };

  // Show loading state
  if (agentsLoading || metricsLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Overview of your AI agents and activity
          </p>
        </div>
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  // Show error state
  if (agentsError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Overview of your AI agents and activity
          </p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load dashboard data. Please check if the backend is running on http://localhost:8000
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const agents = agentsData?.agents || [];
  const metrics = metricsData || {
    total_agents: 0,
    active_agents: 0,
    tasks_completed: 0,
    avg_success_rate: 0,
    trends: undefined
  };

  // Transform backend activities to frontend format
  const activities = (activitiesData?.activities || []).map((activity: any) => {
    // Find agent name
    const agent = agents.find(a => a.id === activity.agent_id);
    const agentName = agent?.name || "System";

    // Map backend status to frontend status
    const statusMap: Record<string, "success" | "error" | "warning"> = {
      "SUCCESS": "success",
      "ERROR": "error",
      "WARNING": "warning",
      "INFO": "success", // Map INFO to success for UI purposes
    };

    // Format timestamp
    const formatTimestamp = (dateString: string) => {
      const date = new Date(dateString);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return "Just now";
      if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
      if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
      if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
      return date.toLocaleDateString();
    };

    return {
      id: activity.id,
      agentId: activity.agent_id || "",
      agentName,
      action: activity.title,
      timestamp: formatTimestamp(activity.created_at),
      status: statusMap[activity.status] || "success",
      details: activity.description || undefined,
    };
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Overview of your AI agents and activity
          </p>
        </div>
        <Link to="/agents">
          <Button variant="outline">View All Agents</Button>
        </Link>
      </div>

      {/* Statistics */}
      <AgentStats
        totalAgents={metrics.total_agents}
        activeAgents={metrics.active_agents}
        totalTasks={metrics.tasks_completed}
        averageSuccessRate={metrics.avg_success_rate}
        trends={metrics.trends}
      />

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Agents (2/3 width) */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Recent Agents</h2>
            <Link to="/agents">
              <Button variant="ghost" size="sm">
                View All →
              </Button>
            </Link>
          </div>
          <AgentList
            agents={agents.slice(0, 6)}
            onCreateNew={() => setIsCreateDialogOpen(true)}
          />
        </div>

        {/* Recent Activity (1/3 width) */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          {activitiesLoading ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <AgentActivity activities={activities} />
          )}
        </div>
      </div>

      {/* Create Agent Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Agent</DialogTitle>
          </DialogHeader>
          <AgentForm
            onSubmit={handleCreateAgent}
            onCancel={() => setIsCreateDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
