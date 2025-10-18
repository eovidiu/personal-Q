import { Link } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  MoreVerticalIcon,
  PlayIcon,
  PauseIcon,
  SettingsIcon,
  TrendingUpIcon,
  CheckCircle2Icon,
  ClockIcon,
} from "lucide-react";
import { Agent } from "@/personal-q/data/agents-data";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

interface AgentCardProps {
  agent: Agent;
}

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

const typeConfig: Record<string, { label: string; color: string }> = {
  conversational: {
    label: "Conversational",
    color: "bg-purple-500/10 text-purple-600 dark:text-purple-400",
  },
  analytical: {
    label: "Analytical",
    color: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  },
  creative: {
    label: "Creative",
    color: "bg-pink-500/10 text-pink-600 dark:text-pink-400",
  },
  automation: {
    label: "Automation",
    color: "bg-orange-500/10 text-orange-600 dark:text-orange-400",
  },
  default: {
    label: "General",
    color: "bg-gray-500/10 text-gray-600 dark:text-gray-400",
  },
};

export function AgentCard({ agent }: AgentCardProps) {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            <Avatar className="h-12 w-12">
              <AvatarImage src={agent.avatar} alt={agent.name} />

              <AvatarFallback>
                {agent.name.substring(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 min-w-0">
              <CardTitle className="text-lg truncate mb-2">{agent.name}</CardTitle>
              <div className="mb-2">
                <Badge
                  variant="outline"
                  className={statusConfig[agent.status].className}
                >
                  {statusConfig[agent.status].label}
                </Badge>
              </div>
              <CardDescription className="line-clamp-2">
                {agent.description}
              </CardDescription>
            </div>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVerticalIcon className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem>
                <SettingsIcon className="h-4 w-4 mr-2" />
                Configure
              </DropdownMenuItem>
              <DropdownMenuItem>
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
              </DropdownMenuItem>
              <DropdownMenuSeparator />

              <DropdownMenuItem className="text-destructive">
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        <div className="flex items-center gap-2 flex-wrap">
          <Badge variant="secondary" className={(typeConfig[agent.type] || typeConfig.default).color}>
            {(typeConfig[agent.type] || typeConfig.default).label}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {agent.model}
          </Badge>
          {agent.tags.slice(0, 2).map((tag) => (
            <Badge key={tag} variant="outline" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>

        <div className="grid grid-cols-3 gap-4 pt-2">
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <CheckCircle2Icon className="h-3 w-3" />

              <span>Tasks</span>
            </div>
            <p className="text-lg font-semibold">
              {agent.tasksCompleted.toLocaleString()}
            </p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <TrendingUpIcon className="h-3 w-3" />

              <span>Success</span>
            </div>
            <p className="text-lg font-semibold">{agent.successRate}%</p>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <ClockIcon className="h-3 w-3" />

              <span>Uptime</span>
            </div>
            <p className="text-lg font-semibold">{agent.uptime}%</p>
          </div>
        </div>

        <div className="text-xs text-muted-foreground pt-2 border-t border-border">
          Last active: {agent.lastActive}
        </div>
      </CardContent>

      <CardFooter>
        <Link to={`/agent/${agent.id}`} className="w-full">
          <Button variant="outline" className="w-full">
            View Details
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
}
