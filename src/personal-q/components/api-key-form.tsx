/**
 * API Key Form Component
 * Handles adding/editing API keys for different services
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { EyeIcon, EyeOffIcon, Loader2Icon } from 'lucide-react';
import type { APIKeyCreate } from '@/types/settings';

interface APIKeyFormProps {
  initialData?: Partial<APIKeyCreate>;
  onSubmit: (data: APIKeyCreate) => void;
  onCancel: () => void;
  isLoading?: boolean;
}

const SERVICES = [
  { value: 'anthropic', label: 'Anthropic (Claude API)', fields: ['api_key'] },
  { value: 'slack', label: 'Slack', fields: ['access_token', 'refresh_token'] },
  { value: 'outlook', label: 'Outlook', fields: ['client_id', 'client_secret', 'tenant_id'] },
  { value: 'onedrive', label: 'OneDrive', fields: ['client_id', 'client_secret', 'tenant_id'] },
  { value: 'obsidian', label: 'Obsidian', fields: ['config'] },
];

export function APIKeyForm({ initialData, onSubmit, onCancel, isLoading }: APIKeyFormProps) {
  const [selectedService, setSelectedService] = useState(initialData?.service_name || '');
  const [showFields, setShowFields] = useState<Record<string, boolean>>({});

  const { register, handleSubmit, formState: { errors } } = useForm<APIKeyCreate>({
    defaultValues: initialData || {},
  });

  const selectedServiceConfig = SERVICES.find((s) => s.value === selectedService);

  const toggleFieldVisibility = (fieldName: string) => {
    setShowFields((prev) => ({ ...prev, [fieldName]: !prev[fieldName] }));
  };

  const onFormSubmit = (data: APIKeyCreate) => {
    onSubmit({
      ...data,
      service_name: selectedService,
      is_active: true,
    });
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-6">
      {/* Service Selection */}
      <div className="space-y-2">
        <Label htmlFor="service">Service *</Label>
        <Select
          value={selectedService}
          onValueChange={setSelectedService}
          disabled={!!initialData?.service_name}
        >
          <SelectTrigger id="service">
            <SelectValue placeholder="Select a service" />
          </SelectTrigger>
          <SelectContent>
            {SERVICES.map((service) => (
              <SelectItem key={service.value} value={service.value}>
                {service.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {!selectedService && (
          <p className="text-sm text-muted-foreground">
            Choose a service to configure
          </p>
        )}
      </div>

      {/* Dynamic Fields Based on Service */}
      {selectedService && selectedServiceConfig && (
        <div className="space-y-4">
          <h3 className="text-sm font-medium">Configuration for {selectedServiceConfig.label}</h3>

          {/* API Key field (for Anthropic) */}
          {selectedServiceConfig.fields.includes('api_key') && (
            <div className="space-y-2">
              <Label htmlFor="api_key">API Key *</Label>
              <div className="relative">
                <Input
                  id="api_key"
                  type={showFields.api_key ? 'text' : 'password'}
                  placeholder="sk-ant-..."
                  {...register('api_key', {
                    required: 'API key is required',
                    minLength: { value: 10, message: 'API key must be at least 10 characters' },
                  })}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleFieldVisibility('api_key')}
                  aria-label={showFields.api_key ? "Hide API key" : "Show API key"}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showFields.api_key ? (
                    <EyeOffIcon className="h-4 w-4" />
                  ) : (
                    <EyeIcon className="h-4 w-4" />
                  )}
                </button>
              </div>
              {errors.api_key && (
                <p className="text-sm text-destructive">{errors.api_key.message}</p>
              )}
            </div>
          )}

          {/* Access Token field (for Slack) */}
          {selectedServiceConfig.fields.includes('access_token') && (
            <div className="space-y-2">
              <Label htmlFor="access_token">Access Token *</Label>
              <div className="relative">
                <Input
                  id="access_token"
                  type={showFields.access_token ? 'text' : 'password'}
                  placeholder="xoxb-..."
                  {...register('access_token', {
                    required: 'Access token is required',
                  })}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleFieldVisibility('access_token')}
                  aria-label={showFields.access_token ? "Hide access token" : "Show access token"}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showFields.access_token ? (
                    <EyeOffIcon className="h-4 w-4" />
                  ) : (
                    <EyeIcon className="h-4 w-4" />
                  )}
                </button>
              </div>
              {errors.access_token && (
                <p className="text-sm text-destructive">{errors.access_token.message}</p>
              )}
            </div>
          )}

          {/* Refresh Token field (for Slack) */}
          {selectedServiceConfig.fields.includes('refresh_token') && (
            <div className="space-y-2">
              <Label htmlFor="refresh_token">Refresh Token (Optional)</Label>
              <div className="relative">
                <Input
                  id="refresh_token"
                  type={showFields.refresh_token ? 'text' : 'password'}
                  placeholder="Optional refresh token"
                  {...register('refresh_token')}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleFieldVisibility('refresh_token')}
                  aria-label={showFields.refresh_token ? "Hide refresh token" : "Show refresh token"}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showFields.refresh_token ? (
                    <EyeOffIcon className="h-4 w-4" />
                  ) : (
                    <EyeIcon className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>
          )}

          {/* Client ID field (for Outlook/OneDrive) */}
          {selectedServiceConfig.fields.includes('client_id') && (
            <div className="space-y-2">
              <Label htmlFor="client_id">Client ID *</Label>
              <Input
                id="client_id"
                type="text"
                placeholder="Application (client) ID"
                {...register('client_id', {
                  required: 'Client ID is required',
                })}
              />
              {errors.client_id && (
                <p className="text-sm text-destructive">{errors.client_id.message}</p>
              )}
            </div>
          )}

          {/* Client Secret field (for Outlook/OneDrive) */}
          {selectedServiceConfig.fields.includes('client_secret') && (
            <div className="space-y-2">
              <Label htmlFor="client_secret">Client Secret *</Label>
              <div className="relative">
                <Input
                  id="client_secret"
                  type={showFields.client_secret ? 'text' : 'password'}
                  placeholder="Client secret value"
                  {...register('client_secret', {
                    required: 'Client secret is required',
                  })}
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleFieldVisibility('client_secret')}
                  aria-label={showFields.client_secret ? "Hide client secret" : "Show client secret"}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showFields.client_secret ? (
                    <EyeOffIcon className="h-4 w-4" />
                  ) : (
                    <EyeIcon className="h-4 w-4" />
                  )}
                </button>
              </div>
              {errors.client_secret && (
                <p className="text-sm text-destructive">{errors.client_secret.message}</p>
              )}
            </div>
          )}

          {/* Tenant ID field (for Outlook/OneDrive) */}
          {selectedServiceConfig.fields.includes('tenant_id') && (
            <div className="space-y-2">
              <Label htmlFor="tenant_id">Tenant ID *</Label>
              <Input
                id="tenant_id"
                type="text"
                placeholder="Directory (tenant) ID"
                {...register('tenant_id', {
                  required: 'Tenant ID is required',
                })}
              />
              {errors.tenant_id && (
                <p className="text-sm text-destructive">{errors.tenant_id.message}</p>
              )}
            </div>
          )}

          {/* Config field (for Obsidian) */}
          {selectedServiceConfig.fields.includes('config') && (
            <div className="space-y-2">
              <Label htmlFor="config">Vault Path *</Label>
              <Input
                id="config"
                type="text"
                placeholder="/path/to/obsidian/vault"
                {...register('config', {
                  required: 'Vault path is required',
                  pattern: {
                    value: /^[a-zA-Z0-9_\-\/.:~\\]+$/,
                    message: 'Invalid path format. Use alphanumeric characters, dashes, underscores, forward slashes, colons, dots, tildes, or backslashes only.'
                  }
                })}
              />
              {errors.config && (
                <p className="text-sm text-destructive">{errors.config.message}</p>
              )}
              <p className="text-xs text-muted-foreground">
                Full path to your Obsidian vault directory
              </p>
            </div>
          )}
        </div>
      )}

      {/* Form Actions */}
      <div className="flex justify-end gap-2">
        <Button type="button" variant="outline" onClick={onCancel} disabled={isLoading}>
          Cancel
        </Button>
        <Button type="submit" disabled={!selectedService || isLoading}>
          {isLoading && <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />}
          {initialData ? 'Update' : 'Add'} API Key
        </Button>
      </div>
    </form>
  );
}
