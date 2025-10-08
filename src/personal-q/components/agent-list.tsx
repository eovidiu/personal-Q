import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SearchIcon, PlusIcon, FilterIcon } from "lucide-react";
import { Agent, AgentStatus, AgentType } from "@/personal-q/data/agents-data";
import { AgentCard } from "@/personal-q/components/agent-card";

interface AgentListProps {
  agents: Agent[];
  onCreateNew?: () => void;
}

export function AgentList({ agents, onCreateNew }: AgentListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<AgentStatus | "all">("all");
  const [typeFilter, setTypeFilter] = useState<AgentType | "all">("all");

  const filteredAgents = agents.filter((agent) => {
    const matchesSearch =
      agent.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      agent.tags.some((tag) =>
        tag.toLowerCase().includes(searchQuery.toLowerCase())
      );

    const matchesStatus =
      statusFilter === "all" || agent.status === statusFilter;
    const matchesType = typeFilter === "all" || agent.type === typeFilter;

    return matchesSearch && matchesStatus && matchesType;
  });

  return (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />

          <Input
            placeholder="Search agents by name, description, or tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>

        <div className="flex gap-2">
          <Select
            value={statusFilter}
            onValueChange={(value: AgentStatus | "all") =>
              setStatusFilter(value)
            }
          >
            <SelectTrigger className="w-[140px]">
              <FilterIcon className="h-4 w-4 mr-2" />

              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
              <SelectItem value="training">Training</SelectItem>
              <SelectItem value="error">Error</SelectItem>
            </SelectContent>
          </Select>

          <Select
            value={typeFilter}
            onValueChange={(value: AgentType | "all") => setTypeFilter(value)}
          >
            <SelectTrigger className="w-[160px]">
              <FilterIcon className="h-4 w-4 mr-2" />

              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="conversational">Conversational</SelectItem>
              <SelectItem value="analytical">Analytical</SelectItem>
              <SelectItem value="creative">Creative</SelectItem>
              <SelectItem value="automation">Automation</SelectItem>
            </SelectContent>
          </Select>

          {onCreateNew && (
            <Button onClick={onCreateNew}>
              <PlusIcon className="h-4 w-4 mr-2" />
              New Agent
            </Button>
          )}
        </div>
      </div>

      {/* Results Count */}
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted-foreground">
          Showing {filteredAgents.length} of {agents.length} agents
        </p>
        {(statusFilter !== "all" || typeFilter !== "all" || searchQuery) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setSearchQuery("");
              setStatusFilter("all");
              setTypeFilter("all");
            }}
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Agent Grid */}
      {filteredAgents.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredAgents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 border border-dashed border-border rounded-lg">
          <p className="text-muted-foreground mb-4">
            No agents found matching your criteria
          </p>
          {onCreateNew && (
            <Button onClick={onCreateNew}>
              <PlusIcon className="h-4 w-4 mr-2" />
              Create Your First Agent
            </Button>
          )}
        </div>
      )}
    </div>
  );
}
