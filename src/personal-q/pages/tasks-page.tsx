import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { TaskCard } from "@/personal-q/components/task-card";
import { useTasks } from "@/hooks/useTasks";
import { useCreateTask } from "@/hooks/useCreateTask";
import { useAgents } from "@/hooks/useAgents";
import { PlusIcon, AlertCircle, Loader2 } from "lucide-react";
import type { TaskStatus, TaskPriority, TaskCreate } from "@/types/task";

export function TasksPage() {
  const [statusFilter, setStatusFilter] = useState<TaskStatus | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  // Fetch tasks with filters
  const { data: tasksData, isLoading, error } = useTasks({
    status: statusFilter !== "all" ? statusFilter : undefined,
  });

  // Fetch agents for task creation
  const { data: agentsData } = useAgents();

  // Create task mutation
  const createTaskMutation = useCreateTask();

  // Form state for creating new task
  const [formData, setFormData] = useState<TaskCreate>({
    agent_id: "",
    title: "",
    description: "",
    priority: "medium",
    input_data: {},
  });

  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTaskMutation.mutateAsync(formData);
      // Reset form and close dialog
      setFormData({
        agent_id: "",
        title: "",
        description: "",
        priority: "medium",
        input_data: {},
      });
      setIsCreateDialogOpen(false);
    } catch (error) {
      console.error("Failed to create task:", error);
    }
  };

  // Filter tasks by search query (client-side filtering)
  const filteredTasks = tasksData?.tasks.filter((task) => {
    const matchesSearch =
      task.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      task.description?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  }) || [];

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-24 w-full" />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Failed to load tasks. Please check your connection and try again.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
          <p className="text-muted-foreground">Manage and monitor agent tasks</p>
        </div>
        <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Task
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>Create New Task</DialogTitle>
              <DialogDescription>
                Assign a new task to an agent. Fill in the details below.
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={handleCreateTask} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="agent">Agent</Label>
                <Select
                  value={formData.agent_id}
                  onValueChange={(value) => setFormData({ ...formData, agent_id: value })}
                >
                  <SelectTrigger id="agent">
                    <SelectValue placeholder="Select an agent" />
                  </SelectTrigger>
                  <SelectContent>
                    {agentsData?.agents.map((agent) => (
                      <SelectItem key={agent.id} value={agent.id}>
                        {agent.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="title">Title</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="Task title"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Task description (optional)"
                  rows={3}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="priority">Priority</Label>
                <Select
                  value={formData.priority}
                  onValueChange={(value) => setFormData({ ...formData, priority: value as TaskPriority })}
                >
                  <SelectTrigger id="priority">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex justify-end gap-2 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsCreateDialogOpen(false)}
                  disabled={createTaskMutation.isPending}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createTaskMutation.isPending || !formData.agent_id || !formData.title}>
                  {createTaskMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                  Create Task
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <Input
          placeholder="Search tasks..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="sm:max-w-xs"
        />
        <Select value={statusFilter} onValueChange={(value) => setStatusFilter(value as TaskStatus | "all")}>
          <SelectTrigger className="sm:max-w-[180px]">
            <SelectValue placeholder="Filter by status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="completed">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
            <SelectItem value="cancelled">Cancelled</SelectItem>
          </SelectContent>
        </Select>
        {(statusFilter !== "all" || searchQuery) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSearchQuery("");
              setStatusFilter("all");
            }}
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Task Count */}
      <div className="text-sm text-muted-foreground">
        Showing {filteredTasks.length} of {tasksData?.total || 0} tasks
      </div>

      {/* Tasks Grid */}
      {filteredTasks.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <p className="text-muted-foreground mb-4">
            {searchQuery || statusFilter !== "all" ? "No tasks match your filters" : "No tasks yet"}
          </p>
          <Button onClick={() => setIsCreateDialogOpen(true)}>
            <PlusIcon className="h-4 w-4 mr-2" />
            Create First Task
          </Button>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredTasks.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      )}
    </div>
  );
}
