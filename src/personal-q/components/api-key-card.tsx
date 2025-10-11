/**
 * API Key Card Component
 * Displays a single API key with masked values and action buttons
 */

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  KeyIcon,
  CheckCircle2Icon,
  XCircleIcon,
  EditIcon,
  Trash2Icon,
  PlayCircleIcon,
  Loader2Icon,
} from 'lucide-react';
import type { APIKey } from '@/types/settings';
import { formatDistanceToNow } from 'date-fns';

interface APIKeyCardProps {
  apiKey: APIKey;
  onEdit: (apiKey: APIKey) => void;
  onDelete: (serviceName: string) => void;
  onTestConnection: (serviceName: string) => void;
  isTestingConnection?: boolean;
  testConnectionResult?: { success: boolean; message: string } | null;
}

const SERVICE_LABELS: Record<string, string> = {
  anthropic: 'Anthropic (Claude API)',
  slack: 'Slack',
  outlook: 'Outlook',
  onedrive: 'OneDrive',
  obsidian: 'Obsidian',
};

function maskValue(value: string): string {
  if (value.length <= 8) return '***';
  return `${value.slice(0, 4)}...${value.slice(-4)}`;
}

export function APIKeyCard({
  apiKey,
  onEdit,
  onDelete,
  onTestConnection,
  isTestingConnection,
  testConnectionResult,
}: APIKeyCardProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const serviceName = SERVICE_LABELS[apiKey.service_name] || apiKey.service_name;

  const handleDelete = () => {
    onDelete(apiKey.service_name);
    setShowDeleteDialog(false);
  };

  return (
    <>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <KeyIcon className="h-5 w-5 text-muted-foreground" />
              <CardTitle className="text-lg">{serviceName}</CardTitle>
            </div>
            <div className="flex items-center gap-2">
              {apiKey.is_active ? (
                <Badge variant="default" className="gap-1">
                  <CheckCircle2Icon className="h-3 w-3" />
                  Active
                </Badge>
              ) : (
                <Badge variant="secondary" className="gap-1">
                  <XCircleIcon className="h-3 w-3" />
                  Inactive
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Masked Credentials Info */}
          <div className="space-y-2 text-sm">
            {apiKey.has_api_key && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">API Key:</span>
                <span className="font-mono">***************</span>
              </div>
            )}
            {apiKey.has_access_token && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Access Token:</span>
                <span className="font-mono">***************</span>
              </div>
            )}
            {apiKey.has_client_credentials && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Client Credentials:</span>
                <span className="font-mono">Configured</span>
              </div>
            )}
          </div>

          {/* Last Validated */}
          {apiKey.last_validated && (
            <div className="text-xs text-muted-foreground">
              Last validated {formatDistanceToNow(new Date(apiKey.last_validated), { addSuffix: true })}
            </div>
          )}

          {/* Test Connection Result */}
          {testConnectionResult && (
            <div
              className={`text-sm p-2 rounded ${
                testConnectionResult.success
                  ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                  : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-400'
              }`}
            >
              {testConnectionResult.message}
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onTestConnection(apiKey.service_name)}
              disabled={isTestingConnection}
              className="flex-1"
            >
              {isTestingConnection ? (
                <>
                  <Loader2Icon className="mr-2 h-4 w-4 animate-spin" />
                  Testing...
                </>
              ) : (
                <>
                  <PlayCircleIcon className="mr-2 h-4 w-4" />
                  Test
                </>
              )}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => onEdit(apiKey)}
            >
              <EditIcon className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDeleteDialog(true)}
              className="text-destructive hover:bg-destructive hover:text-destructive-foreground"
            >
              <Trash2Icon className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete API Key?</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete the API key for <strong>{serviceName}</strong>?
              This action cannot be undone. You will need to reconfigure the service to use it again.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
