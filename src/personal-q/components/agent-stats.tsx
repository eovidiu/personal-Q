import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BotIcon,
  ActivityIcon,
  CheckCircle2Icon,
  TrendingUpIcon,
} from "lucide-react";

interface StatCardProps {
  title: string;
  value: string | number;
  description?: string;
  icon: React.ReactNode;
  trend?: {
    value: string;
    positive: boolean;
  };
}

function StatCard({ title, value, description, icon, trend }: StatCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <div className="h-4 w-4 text-muted-foreground">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
        {trend && (
          <div
            className={`flex items-center gap-1 text-xs mt-2 ${trend.positive ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}
          >
            <TrendingUpIcon
              className={`h-3 w-3 ${!trend.positive && "rotate-180"}`}
            />

            <span>{trend.value}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface AgentStatsProps {
  totalAgents: number;
  activeAgents: number;
  totalTasks: number;
  averageSuccessRate: string | number;
}

export function AgentStats({
  totalAgents,
  activeAgents,
  totalTasks,
  averageSuccessRate,
}: AgentStatsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <StatCard
        title="Total Agents"
        value={totalAgents}
        description={`${activeAgents} currently active`}
        icon={<BotIcon className="h-4 w-4" />}
        trend={{ value: "+2 this week", positive: true }}
      />

      <StatCard
        title="Active Agents"
        value={activeAgents}
        description={`${((activeAgents / totalAgents) * 100).toFixed(0)}% of total`}
        icon={<ActivityIcon className="h-4 w-4" />}
      />

      <StatCard
        title="Tasks Completed"
        value={totalTasks.toLocaleString()}
        description="Across all agents"
        icon={<CheckCircle2Icon className="h-4 w-4" />}
        trend={{ value: "+12.5% from last month", positive: true }}
      />

      <StatCard
        title="Avg Success Rate"
        value={`${averageSuccessRate}%`}
        description="Overall performance"
        icon={<TrendingUpIcon className="h-4 w-4" />}
        trend={{ value: "+2.3% from last month", positive: true }}
      />
    </div>
  );
}
