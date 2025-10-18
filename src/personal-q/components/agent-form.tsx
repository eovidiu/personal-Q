import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { XIcon } from "lucide-react";
import { Agent, AgentType } from "@/personal-q/data/agents-data";

interface AgentFormProps {
  agent?: Agent;
  onSubmit?: (data: Partial<Agent>) => void;
  onCancel?: () => void;
}

export function AgentForm({ agent, onSubmit, onCancel }: AgentFormProps) {
  const [formData, setFormData] = useState({
    name: agent?.name || "",
    description: agent?.description || "",
    // Handle both snake_case (backend) and camelCase (legacy)
    type: (agent as any)?.agent_type || agent?.type || ("conversational" as AgentType),
    model: agent?.model || "GPT-4",
    temperature: agent?.temperature || 0.7,
    maxTokens: (agent as any)?.max_tokens || (agent as any)?.maxTokens || 2048,
    systemPrompt: (agent as any)?.system_prompt || (agent as any)?.systemPrompt || "",
    tags: agent?.tags || [],
  });

  const [tagInput, setTagInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Convert camelCase to snake_case for backend API
    const apiData = {
      name: formData.name,
      description: formData.description,
      agent_type: formData.type,  // Convert type -> agent_type
      model: formData.model,
      temperature: formData.temperature,
      max_tokens: formData.maxTokens,  // Convert maxTokens -> max_tokens
      system_prompt: formData.systemPrompt,  // Convert systemPrompt -> system_prompt
      tags: formData.tags,
    };

    onSubmit?.(apiData);
  };

  const addTag = () => {
    if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
      setFormData({ ...formData, tags: [...formData.tags, tagInput.trim()] });
      setTagInput("");
    }
  };

  const removeTag = (tag: string) => {
    setFormData({ ...formData, tags: formData.tags.filter((t) => t !== tag) });
  };

  return (
    <Card>
      <form onSubmit={handleSubmit}>
        <CardHeader>
          <CardTitle>{agent ? "Edit Agent" : "Create New Agent"}</CardTitle>
          <CardDescription>
            {agent
              ? "Update your agent configuration"
              : "Configure your AI agent with custom settings"}
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Basic Information */}
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Agent Name *</Label>
              <Input
                id="name"
                placeholder="e.g., Customer Support Bot"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description *</Label>
              <Textarea
                id="description"
                placeholder="Describe what this agent does..."
                value={formData.description}
                onChange={(e) =>
                  setFormData({ ...formData, description: e.target.value })
                }
                rows={3}
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="type">Agent Type *</Label>
                <Select
                  value={formData.type}
                  onValueChange={(value: AgentType) =>
                    setFormData({ ...formData, type: value })
                  }
                >
                  <SelectTrigger id="type">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="conversational">
                      Conversational
                    </SelectItem>
                    <SelectItem value="analytical">Analytical</SelectItem>
                    <SelectItem value="creative">Creative</SelectItem>
                    <SelectItem value="automation">Automation</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="model">Model *</Label>
                <Select
                  value={formData.model}
                  onValueChange={(value) =>
                    setFormData({ ...formData, model: value })
                  }
                >
                  <SelectTrigger id="model">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GPT-4">GPT-4</SelectItem>
                    <SelectItem value="GPT-3.5">GPT-3.5</SelectItem>
                    <SelectItem value="Claude-3">Claude-3</SelectItem>
                    <SelectItem value="Gemini-Pro">Gemini Pro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          {/* Model Configuration */}
          <div className="space-y-4 pt-4 border-t border-border">
            <h3 className="text-sm font-semibold">Model Configuration</h3>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="temperature">Temperature</Label>
                <span className="text-sm text-muted-foreground">
                  {formData.temperature}
                </span>
              </div>
              <Slider
                id="temperature"
                min={0}
                max={1}
                step={0.1}
                value={[formData.temperature]}
                onValueChange={([value]) =>
                  setFormData({ ...formData, temperature: value })
                }
              />

              <p className="text-xs text-muted-foreground">
                Lower values make output more focused, higher values more
                creative
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxTokens">Max Tokens</Label>
              <Input
                id="maxTokens"
                type="number"
                min={256}
                max={32768}
                step={256}
                value={formData.maxTokens}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    maxTokens: parseInt(e.target.value),
                  })
                }
              />

              <p className="text-xs text-muted-foreground">
                Maximum length of the response
              </p>
            </div>
          </div>

          {/* System Prompt */}
          <div className="space-y-2 pt-4 border-t border-border">
            <Label htmlFor="systemPrompt">System Prompt *</Label>
            <Textarea
              id="systemPrompt"
              placeholder="You are a helpful assistant..."
              value={formData.systemPrompt}
              onChange={(e) =>
                setFormData({ ...formData, systemPrompt: e.target.value })
              }
              rows={4}
              required
            />

            <p className="text-xs text-muted-foreground">
              Define the agent's behavior and personality
            </p>
          </div>

          {/* Tags */}
          <div className="space-y-2 pt-4 border-t border-border">
            <Label htmlFor="tags">Tags</Label>
            <div className="flex gap-2">
              <Input
                id="tags"
                placeholder="Add a tag..."
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addTag();
                  }
                }}
              />

              <Button type="button" variant="secondary" onClick={addTag}>
                Add
              </Button>
            </div>
            {formData.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="gap-1">
                    {tag}
                    <button
                      type="button"
                      onClick={() => removeTag(tag)}
                      className="ml-1 hover:text-destructive"
                    >
                      <XIcon className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            )}
          </div>
        </CardContent>

        <CardFooter className="flex justify-end gap-2">
          {onCancel && (
            <Button type="button" variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button type="submit">
            {agent ? "Update Agent" : "Create Agent"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
