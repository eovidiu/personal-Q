import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AgentForm } from "@/personal-q/components/agent-form";
import { AgentActivity } from "@/personal-q/components/agent-activity";
import { agents, recentActivity } from "@/personal-q/data/agents-data";
import {
  ArrowLeftIcon,
  PlayIcon,
  PauseIcon,
  SettingsIcon,
  TrendingUpIcon,
  CheckCircle2Icon,
  ClockIcon,
  ActivityIcon,
  BrainIcon,
  TagIcon,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";

const statusConfig = {
  active: {
    label: "Active",
    className:
      "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20",
  },
  inactive: {
    label: "Inactive",
    className:
      "bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/20",
  },
  training: {
    label: "Training",
    className:
      "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
  },
  error: {
    label: "Error",
    className: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
  },
};

export function AgentDetailPage() {
  const { id = "1" } = useParams();
  const agent = agents.find((a) => a.id === id) || agents[0];
  const agentActivities = recentActivity.filter((a) => a.agentId === agent.id);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link to="/agents">
        <Button variant="ghost" size="sm" className="gap-2">
          <ArrowLeftIcon className="h-4 w-4" />
          Back to Agents
        </Button>
      </Link>

      {/* Agent Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-start gap-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src={agent.avatar} alt={agent.name} />

            <AvatarFallback>
              {agent.name.substring(0, 2).toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="text-3xl font-bold tracking-tight">
                {agent.name}
              </h1>
              <Badge
                variant="outline"
                className={statusConfig[agent.status].className}
              >
                {statusConfig[agent.status].label}
              </Badge>
            </div>
            <p className="text-muted-foreground">{agent.description}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsEditDialogOpen(true)}
          >
            <SettingsIcon className="h-4 w-4 mr-2" />
            Configure
          </Button>
          <Button size="sm">
            {agent.status === "active" ? (
              <>
                <PauseIcon className="h-4 w-4 mr-2" />
                Pause
              </>
            ) : (
              <>
                <PlayIcon className="h-4 w-4 mr-2" />
                Activate
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Tasks Completed
            </CardTitle>
            <CheckCircle2Icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {agent.tasksCompleted.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">+180 this week</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <TrendingUpIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agent.successRate}%</div>
            <Progress value={agent.successRate} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Uptime</CardTitle>
            <ActivityIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agent.uptime}%</div>
            <Progress value={agent.uptime} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Last Active</CardTitle>
            <ClockIcon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{agent.lastActive}</div>
            <p className="text-xs text-muted-foreground mt-1">
              Created {agent.createdAt}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="configuration" className="space-y-4">
        <TabsList>
          <TabsTrigger value="configuration">Configuration</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
          <TabsTrigger value="performance">Performance</TabsTrigger>
        </TabsList>

        <TabsContent value="configuration" className="space-y-4">
          <div className="grid gap-6 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BrainIcon className="h-5 w-5" />
                  Model Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-muted-foreground">Model</p>
                    <p className="font-medium">{agent.model}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Type</p>
                    <p className="font-medium capitalize">{agent.type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Temperature</p>
                    <p className="font-medium">{agent.temperature}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Max Tokens</p>
                    <p className="font-medium">
                      {agent.maxTokens.toLocaleString()}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TagIcon className="h-5 w-5" />
                  Tags & Metadata
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm text-muted-foreground mb-2">Tags</p>
                  <div className="flex flex-wrap gap-2">
                    {agent.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground mb-1">Created</p>
                  <p className="font-medium">{agent.createdAt}</p>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>System Prompt</CardTitle>
              <CardDescription>
                Defines the agent's behavior and personality
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="bg-muted p-4 rounded-lg">
                <p className="text-sm font-mono">{agent.systemPrompt}</p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="activity">
          <AgentActivity
            activities={
              agentActivities.length > 0 ? agentActivities : recentActivity
            }
            maxHeight="600px"
          />
        </TabsContent>

        <TabsContent value="performance">
          <Card>
            <CardHeader>
              <CardTitle>Performance Metrics</CardTitle>
              <CardDescription>
                Detailed performance analytics and trends
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium">Task Success Rate</p>
                    <p className="text-sm text-muted-foreground">
                      {agent.successRate}%
                    </p>
                  </div>
                  <Progress value={agent.successRate} />
                </div>
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-sm font-medium">System Uptime</p>
                    <p className="text-sm text-muted-foreground">
                      {agent.uptime}%
                    </p>
                  </div>
                  <Progress value={agent.uptime} />
                </div>
                <div className="pt-4 border-t border-border">
                  <p className="text-sm text-muted-foreground">
                    This agent has completed{" "}
                    {agent.tasksCompleted.toLocaleString()} tasks with an
                    average success rate of {agent.successRate}%. Performance
                    metrics are updated in real-time.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Agent Configuration</DialogTitle>
          </DialogHeader>
          <AgentForm
            agent={agent}
            onSubmit={(data) => {
              console.log("Updating agent:", data);
              setIsEditDialogOpen(false);
            }}
            onCancel={() => setIsEditDialogOpen(false)}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
