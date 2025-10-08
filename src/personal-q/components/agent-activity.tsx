import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  CheckCircle2Icon,
  AlertCircleIcon,
  AlertTriangleIcon,
  ClockIcon,
} from "lucide-react";
import { AgentActivity as AgentActivityType } from "@/personal-q/data/agents-data";

interface AgentActivityProps {
  activities: AgentActivityType[];
  maxHeight?: string;
}

const statusConfig = {
  success: {
    icon: CheckCircle2Icon,
    className: "text-green-600 dark:text-green-400",
    badgeClassName:
      "bg-green-500/10 text-green-600 dark:text-green-400 border-green-500/20",
  },
  error: {
    icon: AlertCircleIcon,
    className: "text-red-600 dark:text-red-400",
    badgeClassName:
      "bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20",
  },
  warning: {
    icon: AlertTriangleIcon,
    className: "text-orange-600 dark:text-orange-400",
    badgeClassName:
      "bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-500/20",
  },
};

export function AgentActivity({
  activities,
  maxHeight = "400px",
}: AgentActivityProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>
          Latest actions and events from your agents
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ScrollArea className="pr-4" style={{ maxHeight }}>
          <div className="space-y-4">
            {activities.map((activity) => {
              const StatusIcon = statusConfig[activity.status].icon;

              return (
                <div
                  key={activity.id}
                  className="flex gap-4 pb-4 border-b border-border last:border-0 last:pb-0"
                >
                  <div
                    className={`mt-1 ${statusConfig[activity.status].className}`}
                  >
                    <StatusIcon className="h-5 w-5" />
                  </div>
                  <div className="flex-1 space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <p className="text-sm font-medium leading-none mb-1">
                          {activity.agentName}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {activity.action}
                        </p>
                      </div>
                      <Badge
                        variant="outline"
                        className={`${statusConfig[activity.status].badgeClassName} text-xs shrink-0`}
                      >
                        {activity.status}
                      </Badge>
                    </div>
                    {activity.details && (
                      <p className="text-xs text-muted-foreground bg-muted p-2 rounded">
                        {activity.details}
                      </p>
                    )}
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <ClockIcon className="h-3 w-3" />

                      <span>{activity.timestamp}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
