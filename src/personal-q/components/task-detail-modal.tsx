import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useTask } from "@/hooks/useTask";
import { AlertCircle, Clock, Calendar, Activity, AlertTriangle } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { Task } from "@/types/task";

interface TaskDetailModalProps {
  taskId: string | undefined;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function TaskDetailModal({ taskId, open, onOpenChange }: TaskDetailModalProps) {
  const { data: task, isLoading, error } = useTask(taskId, { enabled: open && !!taskId });

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            {isLoading ? (
              <Skeleton className="h-6 w-64" />
            ) : (
              <>
                <span>{task?.title}</span>
                {task && <TaskStatusBadge status={task.status} />}
              </>
            )}
          </DialogTitle>
        </DialogHeader>

        {error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>Failed to load task details. Please try again.</AlertDescription>
          </Alert>
        ) : isLoading ? (
          <LoadingSkeleton />
        ) : task ? (
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="output">Output</TabsTrigger>
              <TabsTrigger value="error" disabled={!task.error_message}>
                Error
              </TabsTrigger>
              <TabsTrigger value="timeline">Timeline</TabsTrigger>
            </TabsList>

            <TabsContent value="overview" className="space-y-4 mt-4">
              <OverviewTab task={task} />
            </TabsContent>

            <TabsContent value="output" className="space-y-4 mt-4">
              <OutputTab task={task} />
            </TabsContent>

            <TabsContent value="error" className="space-y-4 mt-4">
              <ErrorTab task={task} />
            </TabsContent>

            <TabsContent value="timeline" className="space-y-4 mt-4">
              <TimelineTab task={task} />
            </TabsContent>
          </Tabs>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}

function TaskStatusBadge({ status }: { status: Task['status'] }) {
  const variants = {
    pending: "secondary",
    running: "default",
    completed: "default",
    failed: "destructive",
    cancelled: "secondary",
  } as const;

  const colors = {
    pending: "bg-yellow-500",
    running: "bg-blue-500",
    completed: "bg-green-500",
    failed: "bg-red-500",
    cancelled: "bg-gray-500",
  };

  return (
    <Badge variant={variants[status]} className={colors[status]}>
      {status}
    </Badge>
  );
}

function TaskPriorityBadge({ priority }: { priority: Task['priority'] }) {
  const variants = {
    low: "secondary",
    medium: "default",
    high: "default",
    urgent: "destructive",
  } as const;

  const colors = {
    low: "bg-gray-500",
    medium: "bg-blue-500",
    high: "bg-orange-500",
    urgent: "bg-red-500",
  };

  return (
    <Badge variant={variants[priority]} className={colors[priority]}>
      {priority}
    </Badge>
  );
}

function OverviewTab({ task }: { task: Task }) {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Status</h3>
          <TaskStatusBadge status={task.status} />
        </div>
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Priority</h3>
          <TaskPriorityBadge priority={task.priority} />
        </div>
      </div>

      {task.description && (
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-2">Description</h3>
          <p className="text-sm bg-muted p-3 rounded-md">{task.description}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-2">
            <Calendar className="h-4 w-4" />
            Created
          </h3>
          <p className="text-sm">{formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}</p>
        </div>

        {task.started_at && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Started
            </h3>
            <p className="text-sm">{formatDistanceToNow(new Date(task.started_at), { addSuffix: true })}</p>
          </div>
        )}

        {task.completed_at && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Completed
            </h3>
            <p className="text-sm">{formatDistanceToNow(new Date(task.completed_at), { addSuffix: true })}</p>
          </div>
        )}

        {task.execution_time_seconds !== null && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-1 flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Execution Time
            </h3>
            <p className="text-sm">{task.execution_time_seconds}s</p>
          </div>
        )}
      </div>

      {task.retry_count > 0 && (
        <div>
          <h3 className="text-sm font-medium text-muted-foreground mb-1">Retry Count</h3>
          <p className="text-sm">{task.retry_count} retries</p>
        </div>
      )}
    </div>
  );
}

function OutputTab({ task }: { task: Task }) {
  if (!task.output_data || Object.keys(task.output_data).length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No output data available yet.</p>
        {task.status === "running" && <p className="text-xs mt-2">Task is currently running...</p>}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium text-muted-foreground">Output Data</h3>
      <pre className="bg-muted p-4 rounded-md text-xs overflow-x-auto max-h-96">
        {JSON.stringify(task.output_data, null, 2)}
      </pre>
    </div>
  );
}

function ErrorTab({ task }: { task: Task }) {
  if (!task.error_message) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <p>No errors</p>
      </div>
    );
  }

  return (
    <Alert variant="destructive">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription className="mt-2">
        <h3 className="font-medium mb-2">Error Details</h3>
        <pre className="text-xs bg-destructive/10 p-3 rounded-md overflow-x-auto whitespace-pre-wrap">
          {task.error_message}
        </pre>
      </AlertDescription>
    </Alert>
  );
}

function TimelineTab({ task }: { task: Task }) {
  const events = [
    {
      type: "created",
      label: "Task Created",
      timestamp: task.created_at,
      icon: Calendar,
      color: "text-blue-500",
    },
    task.started_at && {
      type: "started",
      label: "Task Started",
      timestamp: task.started_at,
      icon: Activity,
      color: "text-green-500",
    },
    task.completed_at && {
      type: "completed",
      label: task.status === "completed" ? "Task Completed" : task.status === "failed" ? "Task Failed" : "Task Cancelled",
      timestamp: task.completed_at,
      icon: task.status === "completed" ? Clock : AlertCircle,
      color: task.status === "completed" ? "text-green-500" : "text-red-500",
    },
  ].filter(Boolean) as Array<{
    type: string;
    label: string;
    timestamp: string;
    icon: any;
    color: string;
  }>;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-muted-foreground">Execution Timeline</h3>
      <div className="space-y-4">
        {events.map((event, index) => {
          const Icon = event.icon;
          return (
            <div key={event.type} className="flex gap-3">
              <div className="relative">
                <div className={`flex h-8 w-8 items-center justify-center rounded-full border-2 bg-background ${event.color}`}>
                  <Icon className="h-4 w-4" />
                </div>
                {index < events.length - 1 && (
                  <div className="absolute left-4 top-8 h-full w-0.5 bg-border" />
                )}
              </div>
              <div className="flex-1 pt-1">
                <p className="text-sm font-medium">{event.label}</p>
                <p className="text-xs text-muted-foreground">
                  {new Date(event.timestamp).toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(event.timestamp), { addSuffix: true })}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {task.execution_time_seconds !== null && (
        <div className="mt-6 pt-6 border-t">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Total Execution Time</span>
            <span className="text-sm text-muted-foreground">{task.execution_time_seconds} seconds</span>
          </div>
        </div>
      )}
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-full" />
      <Skeleton className="h-32 w-full" />
      <Skeleton className="h-24 w-full" />
      <Skeleton className="h-24 w-full" />
    </div>
  );
}
