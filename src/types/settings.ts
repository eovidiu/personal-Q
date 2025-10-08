/**
 * Settings types
 */

export interface APIKey {
  id: string;
  service_name: string;
  is_active: boolean;
  has_api_key: boolean;
  has_access_token: boolean;
  has_client_credentials: boolean;
  last_validated?: string;
  created_at: string;
  updated_at: string;
}

export interface APIKeyCreate {
  service_name: string;
  api_key?: string;
  access_token?: string;
  refresh_token?: string;
  client_id?: string;
  client_secret?: string;
  tenant_id?: string;
  config?: string;
  is_active?: boolean;
}

export interface ConnectionTestResponse {
  service_name: string;
  success: boolean;
  message: string;
}
