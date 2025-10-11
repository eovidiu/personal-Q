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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { AlertCircle } from "lucide-react";

export function AgentsPage() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

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
          <h1 className="text-3xl font-bold tracking-tight">Personal Q</h1>
          <p className="text-muted-foreground mt-1">
            Manage and monitor your AI agents
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
          <h1 className="text-3xl font-bold tracking-tight">Personal Q</h1>
          <p className="text-muted-foreground mt-1">
            Manage and monitor your AI agents
          </p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load agents. Please check if the backend is running on http://localhost:8000
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
  const activities = activitiesData?.activities || [];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Personal Q</h1>
        <p className="text-muted-foreground mt-1">
          Manage and monitor your AI agents
        </p>
      </div>

      {/* Statistics */}
      <AgentStats
        totalAgents={metrics.total_agents}
        activeAgents={metrics.active_agents}
        totalTasks={metrics.tasks_completed}
        averageSuccessRate={metrics.avg_success_rate}
        trends={metrics.trends}
      />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="all-agents">All Agents</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6 mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <AgentList
                agents={agents.slice(0, 6)}
                onCreateNew={() => setIsCreateDialogOpen(true)}
              />
            </div>
            <div>
              {activitiesLoading ? (
                <Skeleton className="h-64 w-full" />
              ) : (
                <AgentActivity activities={activities} />
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="all-agents" className="mt-6">
          <AgentList
            agents={agents}
            onCreateNew={() => setIsCreateDialogOpen(true)}
          />
        </TabsContent>
      </Tabs>

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
