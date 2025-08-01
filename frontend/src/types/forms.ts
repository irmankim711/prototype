// Type definitions for Form Management System

export interface FormStats {
  total_forms: number;
  public_forms: number;
  active_forms: number;
  external_forms: number;
  private_forms: number;
  inactive_forms: number;
  recent_forms: number;
}

export interface FormField {
  id: string;
  type: string;
  label: string;
  required?: boolean;
  placeholder?: string;
  options?: string[];
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
  };
}

export interface FormCreator {
  id: number;
  name: string;
  email: string;
}

export interface Form {
  id: number;
  title: string;
  description?: string;
  schema?: FormField[];
  is_active: boolean;
  is_public: boolean;
  external_url?: string;
  field_count: number;
  view_count: number;
  submission_count: number;
  created_at?: string;
  updated_at?: string;
  access_key?: string;
  creator?: FormCreator;
}

export interface FormData {
  title: string;
  description: string;
  schema: FormField[];
  is_public: boolean;
  is_active: boolean;
  external_url: string;
}

export interface PaginationInfo {
  page: number;
  pages: number;
  per_page: number;
  total: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface FormsResponse {
  forms: Form[];
  pagination: PaginationInfo;
}

export interface ApiResponse<T = unknown> {
  message?: string;
  error?: string;
  details?: string[];
  data?: T;
}
