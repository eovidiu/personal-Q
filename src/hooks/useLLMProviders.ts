/**
 * ABOUTME: Hook to fetch LLM providers and their models.
 * ABOUTME: Used by agent form for provider/model selection.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/services/api';
import type { ProvidersResponse } from '@/types/llm';

export function useLLMProviders() {
  return useQuery<ProvidersResponse>({
    queryKey: ['llm-providers'],
    queryFn: () => apiClient.getLLMProviders(),
    staleTime: 5 * 60 * 1000, // 5 minutes - providers don't change often
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}
