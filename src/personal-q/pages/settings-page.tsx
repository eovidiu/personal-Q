/**
 * Settings Page
 * Manage API keys for various services
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Skeleton } from '@/components/ui/skeleton';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { AlertCircle, PlusIcon, KeyIcon } from 'lucide-react';
import { toast } from 'sonner';
import { APIKeyCard } from '@/personal-q/components/api-key-card';
import { APIKeyForm } from '@/personal-q/components/api-key-form';
import {
  useAPIKeys,
  useCreateOrUpdateAPIKey,
  useDeleteAPIKey,
  useTestConnection,
} from '@/hooks/useSettings';
import type { APIKey, APIKeyCreate } from '@/types/settings';

export function SettingsPage() {
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [editingKey, setEditingKey] = useState<APIKey | null>(null);
  const [testingServices, setTestingServices] = useState<Set<string>>(new Set());
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({});

  // Fetch data
  const { data: apiKeys, isLoading, error } = useAPIKeys();

  // Mutations
  const createOrUpdateMutation = useCreateOrUpdateAPIKey();
  const deleteMutation = useDeleteAPIKey();
  const testConnectionMutation = useTestConnection();

  const handleAddOrUpdate = async (data: APIKeyCreate) => {
    try {
      await createOrUpdateMutation.mutateAsync(data);
      toast.success(editingKey ? 'API key updated successfully' : 'API key added successfully');
      setIsAddDialogOpen(false);
      setEditingKey(null);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to save API key. Please try again.');
      console.error('Error saving API key:', errorMessage);
    }
  };

  const handleDelete = async (serviceName: string) => {
    try {
      await deleteMutation.mutateAsync(serviceName);
      toast.success('API key deleted successfully');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to delete API key. Please try again.');
      console.error('Error deleting API key:', errorMessage);
    }
  };

  const handleTestConnection = async (serviceName: string) => {
    setTestingServices(prev => new Set(prev).add(serviceName));
    try {
      const result = await testConnectionMutation.mutateAsync(serviceName);
      setTestResults((prev) => ({ ...prev, [serviceName]: result }));

      if (result.success) {
        toast.success(`Connection to ${serviceName} successful`);
      } else {
        toast.error(`Connection to ${serviceName} failed: ${result.message}`);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      toast.error('Failed to test connection. Please try again.');
      console.error('Error testing connection:', errorMessage);
    } finally {
      setTestingServices(prev => {
        const next = new Set(prev);
        next.delete(serviceName);
        return next;
      });
    }
  };

  const handleEdit = (apiKey: APIKey) => {
    setEditingKey(apiKey);
    setTestResults({});  // Clear previous test results
    setIsAddDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setIsAddDialogOpen(false);
    setEditingKey(null);
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Manage API keys for external services
          </p>
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Manage API keys for external services
          </p>
        </div>
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load API keys. Please check your network connection and try again.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const hasAPIKeys = apiKeys && apiKeys.length > 0;
  const isAnyMutationLoading = createOrUpdateMutation.isPending ||
                                deleteMutation.isPending ||
                                testConnectionMutation.isPending;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">
            Manage API keys for external services
          </p>
        </div>
        <Button onClick={() => setIsAddDialogOpen(true)} disabled={isAnyMutationLoading}>
          <PlusIcon className="mr-2 h-4 w-4" />
          Add API Key
        </Button>
      </div>

      {/* API Keys List */}
      {hasAPIKeys ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {apiKeys.map((apiKey) => (
            <APIKeyCard
              key={apiKey.id}
              apiKey={apiKey}
              onEdit={handleEdit}
              onDelete={handleDelete}
              onTestConnection={handleTestConnection}
              isTestingConnection={testingServices.has(apiKey.service_name)}
              testConnectionResult={testResults[apiKey.service_name]}
            />
          ))}
        </div>
      ) : (
        /* Empty State */
        <div className="flex flex-col items-center justify-center py-12 px-4 border-2 border-dashed rounded-lg">
          <KeyIcon className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No API Keys Configured</h3>
          <p className="text-sm text-muted-foreground text-center mb-6 max-w-md">
            Get started by configuring your first API key. You'll need API keys to enable
            LLM functionality and external integrations like Slack, Outlook, and OneDrive.
          </p>
          <Button onClick={() => setIsAddDialogOpen(true)}>
            <PlusIcon className="mr-2 h-4 w-4" />
            Configure Your First API Key
          </Button>
        </div>
      )}

      {/* Add/Edit Dialog */}
      <Dialog open={isAddDialogOpen} onOpenChange={handleCloseDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {editingKey ? 'Edit API Key' : 'Add API Key'}
            </DialogTitle>
          </DialogHeader>
          <APIKeyForm
            initialData={editingKey ? {
              service_name: editingKey.service_name,
            } : undefined}
            onSubmit={handleAddOrUpdate}
            onCancel={handleCloseDialog}
            isLoading={createOrUpdateMutation.isPending}
          />
        </DialogContent>
      </Dialog>
    </div>
  );
}
