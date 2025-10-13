// TypeScript Form Type Definitions
// Add this to src/types/forms.ts or create a new types file

export interface Form {
  id: number;
  title: string;
  description?: string;
  schema: FormSchema;
  is_active: boolean;
  submission_count?: number;
  created_at: string;
  updated_at: string;
  user_id: number;
  access_code?: string;
  qr_code?: string;
}

export interface FormField {
  id: string;
  type:
    | "text"
    | "email"
    | "number"
    | "textarea"
    | "select"
    | "radio"
    | "checkbox";
  label: string;
  required?: boolean;
  options?: string[];
  placeholder?: string;
  validation?: Record<string, string | number | boolean>;
}

export interface FormSchema {
  fields: FormField[];
  title?: string;
  description?: string;
  settings?: Record<string, string | number | boolean>;
}

export interface FormSubmission {
  id: number;
  form_id: number;
  data: Record<string, string | number | boolean>;
  submitted_at: string;
  ip_address?: string;
}

export type FormSubmissionData = Record<string, string | number | boolean>;
