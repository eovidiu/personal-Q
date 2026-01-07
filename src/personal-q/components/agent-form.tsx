/**
 * ABOUTME: Agent creation/editing form with multi-provider LLM selection.
 * ABOUTME: Supports Anthropic, OpenAI, and Mistral providers.
 */

import { useState, useEffect, useMemo } from "react";
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
  SelectGroup,
  SelectLabel,
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
import { Alert, AlertDescription } from "@/components/ui/alert";
import { XIcon, AlertCircleIcon, CheckCircleIcon, StarIcon, Loader2Icon } from "lucide-react";
import { Agent, AgentType } from "@/personal-q/data/agents-data";
import { useLLMProviders } from "@/hooks/useLLMProviders";
import type { ProviderInfo, ModelInfo } from "@/types/llm";

interface AgentFormProps {
  agent?: Agent;
  onSubmit?: (data: Partial<Agent>) => void;
  onCancel?: () => void;
}

/**
 * Parse a model string into provider and model parts.
 * e.g., "anthropic/claude-3-5-sonnet-20241022" -> { provider: "anthropic", model: "claude-3-5-sonnet-20241022" }
 */
function parseModelString(modelString: string): { provider: string | null; model: string } {
  if (modelString.includes("/")) {
    const [provider, ...modelParts] = modelString.split("/");
    return { provider, model: modelParts.join("/") };
  }
  return { provider: null, model: modelString };
}

/**
 * Build a full model string from provider and model.
 */
function buildModelString(provider: string, model: string): string {
  return `${provider}/${model}`;
}

export function AgentForm({ agent, onSubmit, onCancel }: AgentFormProps) {
  // Fetch LLM providers
  const { data: providersData, isLoading: providersLoading, error: providersError } = useLLMProviders();

  // Parse existing agent model string
  const parsedModel = useMemo(() => {
    if (agent?.model) {
      return parseModelString(agent.model);
    }
    return { provider: null, model: "" };
  }, [agent?.model]);

  // Form state
  const [formData, setFormData] = useState({
    name: agent?.name || "",
    description: agent?.description || "",
    type: (agent as any)?.agent_type || agent?.type || ("conversational" as AgentType),
    temperature: agent?.temperature || 0.7,
    maxTokens: (agent as any)?.max_tokens || (agent as any)?.maxTokens || 4096,
    systemPrompt: (agent as any)?.system_prompt || (agent as any)?.systemPrompt || "",
    tags: agent?.tags || [],
  });

  // Provider/model selection state
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [tagInput, setTagInput] = useState("");

  // Initialize provider/model from existing agent or defaults
  useEffect(() => {
    if (providersData && !selectedProvider) {
      // If agent has a model, try to parse it
      if (parsedModel.provider && parsedModel.model) {
        setSelectedProvider(parsedModel.provider);
        setSelectedModel(parsedModel.model);
      } else if (parsedModel.model) {
        // Legacy model without provider prefix - use default provider
        setSelectedProvider(providersData.default_provider);
        // Try to find the model in the default provider's models
        const defaultProviderInfo = providersData.providers.find(
          (p) => p.name === providersData.default_provider
        );
        if (defaultProviderInfo) {
          // Check if there's a matching model
          const matchingModel = defaultProviderInfo.models.find(
            (m) => m.id.toLowerCase().includes(parsedModel.model.toLowerCase())
          );
          if (matchingModel) {
            setSelectedModel(matchingModel.id);
          } else {
            // Use recommended model
            const recommended = defaultProviderInfo.models.find((m) => m.is_recommended);
            setSelectedModel(recommended?.id || defaultProviderInfo.models[0]?.id || "");
          }
        }
      } else {
        // No existing model - use defaults
        const parsed = parseModelString(providersData.default_model);
        setSelectedProvider(parsed.provider || providersData.default_provider);
        setSelectedModel(parsed.model);
      }
    }
  }, [providersData, parsedModel, selectedProvider]);

  // Get currently selected provider info
  const currentProvider = useMemo((): ProviderInfo | undefined => {
    return providersData?.providers.find((p) => p.name === selectedProvider);
  }, [providersData, selectedProvider]);

  // Get models for selected provider
  const availableModels = useMemo((): ModelInfo[] => {
    return currentProvider?.models || [];
  }, [currentProvider]);

  // Handle provider change - reset model selection
  const handleProviderChange = (providerName: string) => {
    setSelectedProvider(providerName);
    // Auto-select recommended model for new provider
    const provider = providersData?.providers.find((p) => p.name === providerName);
    if (provider) {
      const recommended = provider.models.find((m) => m.is_recommended);
      setSelectedModel(recommended?.id || provider.models[0]?.id || "");
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    // Build full model string
    const fullModelString = selectedProvider && selectedModel
      ? buildModelString(selectedProvider, selectedModel)
      : "";

    // Convert to backend API format
    const apiData = {
      name: formData.name,
      description: formData.description,
      agent_type: formData.type,
      model: fullModelString,
      temperature: formData.temperature,
      max_tokens: formData.maxTokens,
      system_prompt: formData.systemPrompt,
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

  // Get selected model info for display
  const selectedModelInfo = useMemo((): ModelInfo | undefined => {
    return availableModels.find((m) => m.id === selectedModel);
  }, [availableModels, selectedModel]);

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
                  <SelectItem value="conversational">Conversational</SelectItem>
                  <SelectItem value="analytical">Analytical</SelectItem>
                  <SelectItem value="creative">Creative</SelectItem>
                  <SelectItem value="automation">Automation</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {/* LLM Provider & Model Selection */}
          <div className="space-y-4 pt-4 border-t border-border">
            <h3 className="text-sm font-semibold">LLM Configuration</h3>

            {providersLoading && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2Icon className="h-4 w-4 animate-spin" />
                Loading providers...
              </div>
            )}

            {providersError && (
              <Alert variant="destructive">
                <AlertCircleIcon className="h-4 w-4" />
                <AlertDescription>
                  Failed to load LLM providers. Please try again.
                </AlertDescription>
              </Alert>
            )}

            {providersData && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Provider Selection */}
                  <div className="space-y-2">
                    <Label htmlFor="provider">Provider *</Label>
                    <Select
                      value={selectedProvider}
                      onValueChange={handleProviderChange}
                    >
                      <SelectTrigger id="provider">
                        <SelectValue placeholder="Select provider..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          <SelectLabel>Available Providers</SelectLabel>
                          {providersData.providers.map((provider) => (
                            <SelectItem
                              key={provider.name}
                              value={provider.name}
                              disabled={!provider.is_configured}
                            >
                              <div className="flex items-center gap-2">
                                <span>{provider.display_name}</span>
                                {provider.is_configured ? (
                                  <CheckCircleIcon className="h-3 w-3 text-green-500" />
                                ) : (
                                  <AlertCircleIcon className="h-3 w-3 text-orange-500" />
                                )}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                    {currentProvider && !currentProvider.is_configured && (
                      <p className="text-xs text-orange-500">
                        API key not configured. Set {currentProvider.name.toUpperCase()}_API_KEY environment variable.
                      </p>
                    )}
                  </div>

                  {/* Model Selection */}
                  <div className="space-y-2">
                    <Label htmlFor="model">Model *</Label>
                    <Select
                      value={selectedModel}
                      onValueChange={setSelectedModel}
                      disabled={!selectedProvider || availableModels.length === 0}
                    >
                      <SelectTrigger id="model">
                        <SelectValue placeholder="Select model..." />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectGroup>
                          <SelectLabel>Available Models</SelectLabel>
                          {availableModels.map((model) => (
                            <SelectItem key={model.id} value={model.id}>
                              <div className="flex items-center gap-2">
                                <span>{model.display_name}</span>
                                {model.is_recommended && (
                                  <StarIcon className="h-3 w-3 text-yellow-500 fill-yellow-500" />
                                )}
                              </div>
                            </SelectItem>
                          ))}
                        </SelectGroup>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Model Info */}
                {selectedModelInfo && (
                  <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
                    <Badge variant="outline" className="text-xs">
                      {(selectedModelInfo.context_window / 1000).toFixed(0)}K context
                    </Badge>
                    {selectedModelInfo.supports_vision && (
                      <Badge variant="outline" className="text-xs">Vision</Badge>
                    )}
                    {selectedModelInfo.supports_tools && (
                      <Badge variant="outline" className="text-xs">Tools</Badge>
                    )}
                    <Badge variant="outline" className="text-xs">
                      ${selectedModelInfo.cost_per_1k_input}/1K in, ${selectedModelInfo.cost_per_1k_output}/1K out
                    </Badge>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Model Parameters */}
          <div className="space-y-4 pt-4 border-t border-border">
            <h3 className="text-sm font-semibold">Model Parameters</h3>

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
                Lower values make output more focused, higher values more creative
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="maxTokens">Max Tokens</Label>
              <Input
                id="maxTokens"
                type="number"
                min={256}
                max={selectedModelInfo?.max_output_tokens || 32768}
                step={256}
                value={formData.maxTokens}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    maxTokens: parseInt(e.target.value) || 4096,
                  })
                }
              />
              <p className="text-xs text-muted-foreground">
                Maximum length of the response
                {selectedModelInfo && (
                  <span> (max: {selectedModelInfo.max_output_tokens.toLocaleString()})</span>
                )}
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
          <Button
            type="submit"
            disabled={!selectedProvider || !selectedModel || providersLoading}
          >
            {agent ? "Update Agent" : "Create Agent"}
          </Button>
        </CardFooter>
      </form>
    </Card>
  );
}
