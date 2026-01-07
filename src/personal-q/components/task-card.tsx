import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { CheckCircle2Icon, ClockIcon, XCircleIcon, PlayCircleIcon, Loader2Icon, BanIcon, XIcon } from "lucide-react";
import { TaskDetailModal } from "./task-detail-modal";
import { useCancelTask } from "@/hooks/useCancelTask";
import type { Task } from "@/types/task";

interface TaskCardProps {
  task: Task;
}

const statusConfig = {
  pending: {
    label: "Pending",
    className: "bg-gray-500/10 text-gray-600 dark:text-gray-400 border-gray-500/20",
    icon: ClockIcon,
  },
  running: {
    label: "Running",
    className: "bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20",
    icon: PlayCircleIcon,
  },
  completed: {
    label: "Completed",
    className: "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20",
    icon: CheckCircle2Icon,
  },
  failed: {
    label: "Failed",
    className: "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
    icon: XCircleIcon,
  },
  cancelled: {
    label: "Cancelled",
    className: "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20",
    icon: BanIcon,
  },
};

const priorityConfig = {
  low: {
    label: "Low",
    className: "bg-slate-500/10 text-slate-600 dark:text-slate-400",
  },
  medium: {
    label: "Medium",
    className: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  },
  high: {
    label: "High",
    className: "bg-orange-500/10 text-orange-600 dark:text-orange-400",
  },
  urgent: {
    label: "Urgent",
    className: "bg-red-500/10 text-red-600 dark:text-red-400",
  },
};

export function TaskCard({ task }: TaskCardProps) {
  const [showDetail, setShowDetail] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const cancelTaskMutation = useCancelTask();

  // Defensive fallbacks for unexpected status/priority values
  const statusInfo = statusConfig[task.status] || statusConfig.pending;
  const priorityInfo = priorityConfig[task.priority] || priorityConfig.medium;
  const StatusIcon = statusInfo.icon;

  const canCancel = task.status === 'pending' || task.status === 'running';

  const handleCancelClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click from opening detail modal
    setShowCancelDialog(true);
  };

  const handleConfirmCancel = async () => {
    await cancelTaskMutation.mutateAsync(task.id);
    setShowCancelDialog(false);
  };

  return (
    <>
      <Card
        className="hover:shadow-lg transition-shadow cursor-pointer"
        onClick={() => setShowDetail(true)}
      >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <StatusIcon className="h-4 w-4 flex-shrink-0" />
              <CardTitle className="text-lg truncate">{task.title}</CardTitle>
            </div>
            {task.description && (
              <CardDescription className="line-clamp-2">{task.description}</CardDescription>
            )}
          </div>
          {canCancel && (
            <Button
              variant="ghost"
              size="icon"
              onClick={handleCancelClick}
              disabled={cancelTaskMutation.isPending}
              className="ml-2 flex-shrink-0"
              title="Cancel task"
            >
              <XIcon className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="outline" className={statusInfo.className}>
            {statusInfo.label}
          </Badge>
          <Badge variant="secondary" className={priorityInfo.className}>
            {priorityInfo.label}
          </Badge>
        </div>

        {task.error_message && (
          <div className="p-2 rounded bg-destructive/10 text-destructive text-sm">
            <p className="font-medium">Error:</p>
            <p className="line-clamp-2">{task.error_message}</p>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4 pt-2">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Created</p>
            <p className="text-sm font-medium">
              {new Date(task.created_at).toLocaleDateString()}
            </p>
          </div>
          {task.completed_at && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Completed</p>
              <p className="text-sm font-medium">
                {new Date(task.completed_at).toLocaleDateString()}
              </p>
            </div>
          )}
          {task.execution_time_seconds != null && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Duration</p>
              <p className="text-sm font-medium">{task.execution_time_seconds.toFixed(2)}s</p>
            </div>
          )}
          {task.retry_count > 0 && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground">Retries</p>
              <p className="text-sm font-medium">{task.retry_count}</p>
            </div>
          )}
        </div>

        {task.status === 'running' && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground pt-2 border-t border-border">
            <Loader2Icon className="h-3 w-3 animate-spin" />
            <span>Task in progress...</span>
          </div>
        )}
      </CardContent>
    </Card>

      <TaskDetailModal
        taskId={task.id}
        open={showDetail}
        onOpenChange={setShowDetail}
      />

      <AlertDialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancel Task?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to cancel "{task.title}"? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>No, keep running</AlertDialogCancel>
            <AlertDialogAction onClick={handleConfirmCancel} disabled={cancelTaskMutation.isPending}>
              {cancelTaskMutation.isPending ? (
                <>
                  <Loader2Icon className="h-4 w-4 mr-2 animate-spin" />
                  Cancelling...
                </>
              ) : (
                'Yes, cancel task'
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
