import { useState } from "react";
import { AgentStats } from "@/personal-q/components/agent-stats";
import { AgentList } from "@/personal-q/components/agent-list";
import { AgentActivity } from "@/personal-q/components/agent-activity";
import { AgentForm } from "@/personal-q/components/agent-form";
import { agents, agentStats, recentActivity } from "@/personal-q/data/agents-data";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function AgentsPage() {
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");

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
        totalAgents={agentStats.totalAgents}
        activeAgents={agentStats.activeAgents}
        totalTasks={agentStats.totalTasks}
        averageSuccessRate={agentStats.averageSuccessRate}
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
              <AgentActivity activities={recentActivity} />
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
            onSubmit={(data) => {
              console.log("Creating agent:", data);
              setIsCreateDialogOpen(false);
            }}
            onCancel={() => setIsCreateDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
