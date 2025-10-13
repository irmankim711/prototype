/**
 * Advanced Form Builder Types and Interfaces
 * Enhanced type definitions for the conditional logic form builder
 */

export interface ConditionalRule {
  id: string;
  sourceFieldId: string;
  condition:
    | "equals"
    | "not_equals"
    | "contains"
    | "not_contains"
    | "greater_than"
    | "less_than"
    | "greater_equal"
    | "less_equal"
    | "is_empty"
    | "is_not_empty"
    | "regex_match";
  value: string | number | boolean | string[];
  action: "show" | "hide" | "require" | "disable" | "set_value" | "calculate";
  targetFieldIds: string[];
  logicOperator?: "AND" | "OR"; // For multiple conditions
  priority?: number; // Rule execution priority
}

export interface FieldValidation {
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  pattern?: string;
  min?: number;
  max?: number;
  customValidation?: string; // JavaScript function string
  errorMessage?: string;
}

export interface FormField {
  id: string;
  type:
    | "text"
    | "email"
    | "phone"
    | "number"
    | "textarea"
    | "select"
    | "radio"
    | "checkbox"
    | "file"
    | "date"
    | "time"
    | "datetime"
    | "url"
    | "rating"
    | "signature"
    | "location"
    | "calculated"
    | "section_break"
    | "page_break";
  label: string;
  placeholder?: string;
  description?: string;
  required?: boolean;
  order: number;

  // Field-specific properties
  options?: string[]; // For select, radio, checkbox
  multiple?: boolean; // For select, file
  accept?: string; // For file inputs
  min?: number | string; // For number, date inputs
  max?: number | string; // For number, date inputs
  step?: number; // For number inputs

  // Advanced properties
  conditional_rules?: ConditionalRule[];
  validation?: FieldValidation;
  default_value?: any;
  readonly?: boolean;
  hidden?: boolean;

  // Layout properties
  width?: "full" | "half" | "third" | "quarter";
  column_span?: number;
  row_span?: number;

  // Styling
  css_class?: string;
  inline_style?: Record<string, string>;

  // Metadata
  metadata?: Record<string, any>;
}

export interface FormSection {
  id: string;
  title: string;
  description?: string;
  fields: FormField[];
  conditional_rules?: ConditionalRule[];
  collapsible?: boolean;
  collapsed?: boolean;
  order: number;
}

export interface FormPage {
  id: string;
  title: string;
  description?: string;
  sections: FormSection[];
  conditional_rules?: ConditionalRule[];
  order: number;
}

export interface FormSchema {
  version: string;
  pages?: FormPage[];
  sections?: FormSection[];
  fields: FormField[];
  global_rules?: ConditionalRule[];
  layout?: {
    columns?: number;
    responsive?: boolean;
    theme?: string;
  };
}

export interface Form {
  id: number;
  title: string;
  description?: string;
  schema: FormSchema;
  is_active: boolean;
  is_public: boolean;
  settings?: FormSettings;
  created_at: string;
  updated_at: string;
  user_id: number;
  metadata?: Record<string, any>;
}

export interface FormSettings {
  allow_multiple_submissions?: boolean;
  require_login?: boolean;
  capture_location?: boolean;
  send_email_notifications?: boolean;
  email_recipients?: string[];
  redirect_url?: string;
  custom_css?: string;
  submit_button_text?: string;
  success_message?: string;
  terms_and_conditions?: string;
  privacy_policy?: string;
}

export interface FormSubmission {
  id: number;
  form_id: number;
  data: Record<string, any>;
  metadata?: {
    ip_address?: string;
    user_agent?: string;
    location?: {
      latitude: number;
      longitude: number;
    };
    submission_time: string;
    validation_errors?: string[];
  };
  created_at: string;
  user_id?: number;
}

// Drag and Drop Types
export interface DragItem {
  type: "FIELD" | "SECTION" | "PAGE";
  id: string;
  fieldType?: string;
  field?: FormField;
  section?: FormSection;
  page?: FormPage;
}

export interface DropResult {
  draggedId: string;
  targetId?: string;
  position: "before" | "after" | "inside";
  action: "move" | "copy" | "create";
}

// Form Builder State
export interface FormBuilderState {
  form: Partial<Form>;
  selectedField: FormField | null;
  selectedSection: FormSection | null;
  selectedPage: FormPage | null;
  previewMode: boolean;
  currentPage: number;
  isDirty: boolean;
  validationErrors: Record<string, string[]>;
  conditionalState: Record<string, boolean>; // field visibility state
}

// Conditional Logic Engine Types
export interface RuleEvaluation {
  ruleId: string;
  passed: boolean;
  sourceValue: any;
  targetValue: any;
  condition: string;
}

export interface ConditionalContext {
  formData: Record<string, any>;
  fieldStates: Record<
    string,
    {
      visible: boolean;
      required: boolean;
      disabled: boolean;
      value: any;
    }
  >;
  evaluationResults: RuleEvaluation[];
}

// Field Type Definitions
export interface FieldTypeDefinition {
  type: string;
  label: string;
  icon: React.ComponentType;
  category: "basic" | "advanced" | "layout" | "special";
  description: string;
  defaultProps: Partial<FormField>;
  configurable: {
    hasOptions: boolean;
    hasValidation: boolean;
    hasConditionalLogic: boolean;
    hasCalculation: boolean;
  };
  preview: React.ComponentType<{ field: FormField; value?: any }>;
  editor: React.ComponentType<{
    field: FormField;
    onChange: (field: FormField) => void;
  }>;
}

// API Types
export interface FormBuilderAPI {
  getForms: (params?: { page?: number; limit?: number }) => Promise<{
    forms: Form[];
    total: number;
    page: number;
    limit: number;
  }>;
  getForm: (id: number) => Promise<Form>;
  createForm: (form: Partial<Form>) => Promise<Form>;
  updateForm: (id: number, form: Partial<Form>) => Promise<Form>;
  deleteForm: (id: number) => Promise<void>;
  duplicateForm: (id: number) => Promise<Form>;
  getFieldTypes: () => Promise<FieldTypeDefinition[]>;
  validateForm: (form: Partial<Form>) => Promise<{
    valid: boolean;
    errors: Record<string, string[]>;
  }>;
  previewForm: (schema: FormSchema) => Promise<{
    html: string;
    css: string;
    js: string;
  }>;
  testConditionalLogic: (
    schema: FormSchema,
    testData: Record<string, any>
  ) => Promise<ConditionalContext>;
}

// Utility Types
export type FormFieldValue =
  | string
  | number
  | boolean
  | string[]
  | File
  | File[];

export interface FormValidationResult {
  valid: boolean;
  errors: Record<string, string[]>;
  warnings: Record<string, string[]>;
}

export interface ConditionalLogicResult {
  fieldStates: Record<
    string,
    {
      visible: boolean;
      required: boolean;
      disabled: boolean;
    }
  >;
  calculatedValues: Record<string, any>;
  warnings: string[];
}

// Event Types
export interface FormBuilderEvent {
  type:
    | "field_added"
    | "field_removed"
    | "field_updated"
    | "rule_added"
    | "rule_removed";
  data: any;
  timestamp: Date;
}

export interface FormPreviewEvent {
  type: "value_changed" | "validation_triggered" | "rule_evaluated";
  fieldId: string;
  value: any;
  data: any;
}

// Export all types
export type {
  ConditionalRule,
  FieldValidation,
  FormField,
  FormSection,
  FormPage,
  FormSchema,
  Form,
  FormSettings,
  FormSubmission,
  DragItem,
  DropResult,
  FormBuilderState,
  RuleEvaluation,
  ConditionalContext,
  FieldTypeDefinition,
  FormBuilderAPI,
  FormFieldValue,
  FormValidationResult,
  ConditionalLogicResult,
  FormBuilderEvent,
  FormPreviewEvent,
};
