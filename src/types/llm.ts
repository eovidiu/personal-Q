/**
 * ABOUTME: Types for LLM providers and models.
 * ABOUTME: Used by the provider/model selection dropdown in agent form.
 */

export interface ModelInfo {
  id: string;
  display_name: string;
  context_window: number;
  max_output_tokens: number;
  supports_vision: boolean;
  supports_tools: boolean;
  cost_per_1k_input: number;
  cost_per_1k_output: number;
  is_recommended: boolean;
}

export interface ProviderInfo {
  name: string;
  display_name: string;
  prefix: string;
  is_configured: boolean;
  status: 'available' | 'not_configured' | 'error';
  models: ModelInfo[];
}

export interface ProvidersResponse {
  providers: ProviderInfo[];
  default_provider: string;
  default_model: string;
}
