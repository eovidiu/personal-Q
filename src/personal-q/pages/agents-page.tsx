import { useState } from "react";
import { AgentList } from "@/personal-q/components/agent-list";
import { AgentForm } from "@/personal-q/components/agent-form";
import { useAgents } from "@/hooks/useAgents";
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
import { Button } from "@/components/ui/button";
import { Link } from "react-router-dom";

/**
 * AgentsPage - Full list of all agents
 *
 * Shows:
 * - Complete list of all agents with filtering/search capabilities
 * - Create new agent button
 *
 * This is the dedicated agents management page.
 */
export function AgentsPage() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  // Fetch data using React Query hooks
  const { data: agentsData, isLoading: agentsLoading, error: agentsError } = useAgents();
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
  if (agentsLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agents</h1>
          <p className="text-muted-foreground mt-1">
            Manage and configure your AI agents
          </p>
        </div>
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  // Show error state
  if (agentsError) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agents</h1>
          <p className="text-muted-foreground mt-1">
            Manage and configure your AI agents
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

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agents</h1>
          <p className="text-muted-foreground mt-1">
            Manage and configure all your AI agents
          </p>
        </div>
        <Link to="/">
          <Button variant="outline">Back to Dashboard</Button>
        </Link>
      </div>

      {/* Full Agent List */}
      <AgentList
        agents={agents}
        onCreateNew={() => setIsCreateDialogOpen(true)}
      />

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
