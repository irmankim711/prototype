import axios from "axios";

// Types for Form Builder
export interface FormField {
  id: string;
  label: string;
  type: string;
  required: boolean;
  options?: string[];
  placeholder?: string;
  description?: string;
  validation?: {
    minLength?: number;
    maxLength?: number;
    pattern?: string;
    min?: number;
    max?: number;
    fileType?: string[];
    maxSize?: number;
  };
  styling?: {
    width?: "full" | "half" | "third" | "quarter";
    color?: string;
    backgroundColor?: string;
    borderRadius?: number;
    fontSize?: number;
  };
  conditional?: {
    dependsOn?: string;
    showWhen?: string;
    value?: any;
  };
  defaultValue?: any;
  helpText?: string;
  icon?: string;
  order: number;
}

export interface FormSchema {
  fields: FormField[];
  settings?: {
    theme?: string;
    submitButtonText?: string;
    showProgressBar?: boolean;
    allowMultipleSubmissions?: boolean;
  };
}

export interface FormQRCode {
  id: number;
  qr_code_data: string;
  external_url: string;
  title: string;
  description?: string;
  created_at: string;
  updated_at: string;
  scan_count: number;
  last_scanned?: string;
  is_active: boolean;
  settings: {
    size: number;
    error_correction: string;
    border: number;
    background_color: string;
    foreground_color: string;
  };
}

export interface Form {
  id: number;
  title: string;
  description?: string;
  schema: FormSchema;
  is_active: boolean;
  is_public: boolean;
  creator_id: number;
  creator_name: string;
  created_at: string;
  updated_at: string;
  submission_count: number;

  // Enhanced form fields
  external_url?: string;
  qr_code_data?: string;
  form_settings?: Record<string, any>;
  access_key?: string;
  view_count: number;
  submission_limit?: number;
  expires_at?: string;

  statistics?: {
    total_submissions: number;
    recent_submissions: number;
    submission_rate: number;
  };
}

export interface FormSubmission {
  id: number;
  data: Record<string, any>;
  submitter_id?: number;
  submitter_email?: string;
  submitted_at: string;
  status: "submitted" | "reviewed" | "approved" | "rejected";
}

export interface FieldType {
  label: string;
  description: string;
  icon: string;
  category: string;
  color: string;
  validation: string[];
}

export interface FormBuilderConfig {
  field_types: Record<string, FieldType>;
  categories: Record<string, string[]>;
}

// API Base URL
const API_BASE_URL = "/api";

// Create axios instance with auth
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("accessToken");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle token refresh or redirect to login
      localStorage.removeItem("accessToken");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

// Form Builder API Functions
export const formBuilderAPI = {
  // Get all forms with filtering and pagination
  getForms: async ({ page = 1, limit = 10 }) => {
    const response = await api.get("/forms", {
      params: { page, per_page: limit },
    });
    return response.data;
  },

  // Get a specific form
  getForm: async (formId: number) => {
    const response = await api.get(`/api/forms/${formId}`);
    return response.data;
  },

  // Create a new form
  createForm: async (formData: {
    title: string;
    description?: string;
    schema: FormSchema;
    is_active?: boolean;
    is_public?: boolean;
  }) => {
    const response = await api.post("/api/forms/", formData);
    return response.data;
  },

  // Update a form
  updateForm: async (
    formId: number,
    formData: Partial<{
      title: string;
      description: string;
      schema: FormSchema;
      is_active: boolean;
      is_public: boolean;
    }>
  ) => {
    const response = await api.put(`/api/forms/${formId}`, formData);
    return response.data;
  },

  // Delete a form (soft delete)
  deleteForm: async (formId: number) => {
    const response = await api.delete(`/api/forms/${formId}`);
    return response.data;
  },

  // Get available field types
  getFieldTypes: async (): Promise<FormBuilderConfig> => {
    const response = await api.get("/api/forms/field-types");
    return response.data;
  },

  // Submit a form (public endpoint)
  submitForm: async (
    formId: number,
    data: {
      data: Record<string, any>;
      email?: string;
    }
  ) => {
    const response = await api.post(`/api/forms/${formId}/submissions`, data);
    return response.data;
  },

  // Get form submissions
  getFormSubmissions: async (
    formId: number,
    params?: {
      page?: number;
      per_page?: number;
      status?: string;
      date_from?: string;
      date_to?: string;
    }
  ) => {
    const response = await api.get(`/api/forms/${formId}/submissions`, {
      params,
    });
    return response.data;
  },

  // Update submission status
  updateSubmissionStatus: async (submissionId: number, status: string) => {
    const response = await api.put(
      `/api/forms/submissions/${submissionId}/status`,
      {
        status,
      }
    );
    return response.data;
  },

  // QR Code Management APIs
  createFormQRCode: async (
    formId: number,
    qrData: {
      external_url: string;
      title?: string;
      description?: string;
      size?: number;
      error_correction?: string;
      border?: number;
      background_color?: string;
      foreground_color?: string;
    }
  ) => {
    const response = await api.post(`/api/forms/${formId}/qr-codes`, qrData);
    return response.data;
  },

  getFormQRCodes: async (
    formId: number
  ): Promise<{ qr_codes: FormQRCode[]; count: number }> => {
    const response = await api.get(`/api/forms/${formId}/qr-codes`);
    return response.data;
  },

  updateFormQRCode: async (
    formId: number,
    qrId: number,
    qrData: {
      title?: string;
      description?: string;
      external_url?: string;
      size?: number;
      error_correction?: string;
      border?: number;
      background_color?: string;
      foreground_color?: string;
    }
  ) => {
    const response = await api.put(
      `/api/forms/${formId}/qr-codes/${qrId}`,
      qrData
    );
    return response.data;
  },

  deleteFormQRCode: async (formId: number, qrId: number) => {
    const response = await api.delete(`/api/forms/${formId}/qr-codes/${qrId}`);
    return response.data;
  },

  trackQRScan: async (qrId: number) => {
    const response = await api.post(`/api/forms/qr/${qrId}/scan`);
    return response.data;
  },

  // Enhanced form operations
  duplicateForm: async (formId: number, newTitle?: string) => {
    const form = await formBuilderAPI.getForm(formId);
    const duplicatedForm = formBuilderUtils.duplicateForm(form);
    if (newTitle) {
      duplicatedForm.title = newTitle;
    }
    return await formBuilderAPI.createForm(duplicatedForm);
  },

  exportFormData: async (
    formId: number,
    format: "json" | "csv" | "xlsx" = "json"
  ) => {
    const response = await api.get(`/api/forms/${formId}/export`, {
      params: { format },
      responseType: format === "json" ? "json" : "blob",
    });
    return response.data;
  },
};

// Form Builder Utilities
export const formBuilderUtils = {
  // Generate unique field ID
  generateFieldId: (): string => {
    return `field_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  },

  // Validate form schema
  validateFormSchema: (schema: FormSchema): string[] => {
    const errors: string[] = [];

    if (!schema.fields || !Array.isArray(schema.fields)) {
      errors.push("Form must have at least one field");
      return errors;
    }

    if (schema.fields.length === 0) {
      errors.push("Form must have at least one field");
    }

    const fieldIds = new Set<string>();
    schema.fields.forEach((field, index) => {
      if (!field.id) {
        errors.push(`Field ${index + 1} must have an ID`);
      } else if (fieldIds.has(field.id)) {
        errors.push(`Field ID '${field.id}' is duplicated`);
      } else {
        fieldIds.add(field.id);
      }

      if (!field.label || field.label.trim() === "") {
        errors.push(`Field ${index + 1} must have a label`);
      }

      if (!field.type) {
        errors.push(`Field ${index + 1} must have a type`);
      }
    });

    return errors;
  },

  // Validate form data against schema
  validateFormData: (
    schema: FormSchema,
    data: Record<string, any>
  ): string[] => {
    const errors: string[] = [];

    schema.fields.forEach((field) => {
      const value = data[field.id];

      // Check required fields
      if (
        field.required &&
        (value === undefined || value === null || value === "")
      ) {
        errors.push(`Field '${field.label}' is required`);
        return;
      }

      // Skip validation for empty optional fields
      if (value === undefined || value === null || value === "") {
        return;
      }

      // Type-specific validation
      switch (field.type) {
        case "email":
          const emailPattern =
            /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
          if (!emailPattern.test(String(value))) {
            errors.push(`Field '${field.label}' must be a valid email address`);
          }
          break;

        case "number":
          const numValue = Number(value);
          if (isNaN(numValue)) {
            errors.push(`Field '${field.label}' must be a number`);
          } else {
            if (
              field.validation?.min !== undefined &&
              numValue < field.validation.min
            ) {
              errors.push(
                `Field '${field.label}' must be at least ${field.validation.min}`
              );
            }
            if (
              field.validation?.max !== undefined &&
              numValue > field.validation.max
            ) {
              errors.push(
                `Field '${field.label}' must be at most ${field.validation.max}`
              );
            }
          }
          break;

        case "text":
        case "textarea":
          const textValue = String(value);
          if (
            field.validation?.minLength &&
            textValue.length < field.validation.minLength
          ) {
            errors.push(
              `Field '${field.label}' must be at least ${field.validation.minLength} characters`
            );
          }
          if (
            field.validation?.maxLength &&
            textValue.length > field.validation.maxLength
          ) {
            errors.push(
              `Field '${field.label}' must be at most ${field.validation.maxLength} characters`
            );
          }
          break;

        case "select":
        case "radio":
          if (field.options && !field.options.includes(String(value))) {
            errors.push(`Field '${field.label}' has an invalid option`);
          }
          break;

        case "rating":
          const ratingValue = Number(value);
          if (isNaN(ratingValue) || ratingValue < 1 || ratingValue > 5) {
            errors.push(
              `Field '${field.label}' must be a number between 1 and 5`
            );
          }
          break;
      }
    });

    return errors;
  },

  // Generate form preview data
  generatePreviewData: (schema: FormSchema): Record<string, any> => {
    const previewData: Record<string, any> = {};

    schema.fields.forEach((field) => {
      switch (field.type) {
        case "text":
          previewData[field.id] = "Sample text input";
          break;
        case "textarea":
          previewData[field.id] = "Sample multi-line text input";
          break;
        case "email":
          previewData[field.id] = "user@example.com";
          break;
        case "number":
          previewData[field.id] = 42;
          break;
        case "select":
        case "radio":
          previewData[field.id] = field.options?.[0] || "";
          break;
        case "checkbox":
          previewData[field.id] = field.options?.slice(0, 2) || [];
          break;
        case "date":
          previewData[field.id] = new Date().toISOString().split("T")[0];
          break;
        case "time":
          previewData[field.id] = "12:00";
          break;
        case "datetime":
          previewData[field.id] = new Date().toISOString().slice(0, 16);
          break;
        case "phone":
          previewData[field.id] = "+1 (555) 123-4567";
          break;
        case "url":
          previewData[field.id] = "https://example.com";
          break;
        case "rating":
          previewData[field.id] = 4;
          break;
        default:
          previewData[field.id] = "";
      }
    });

    return previewData;
  },

  // Export form as JSON
  exportForm: (form: Form): string => {
    return JSON.stringify(form, null, 2);
  },

  // Import form from JSON
  importForm: (jsonString: string): Form => {
    try {
      const form = JSON.parse(jsonString);
      // Validate the imported form structure
      if (!form.title || !form.schema) {
        throw new Error("Invalid form structure");
      }
      return form;
    } catch (error) {
      throw new Error("Invalid JSON format");
    }
  },

  // Duplicate a form
  duplicateForm: (
    form: Form
  ): Omit<Form, "id" | "created_at" | "updated_at"> => {
    const { id, created_at, updated_at, ...formData } = form;
    return {
      ...formData,
      title: `${formData.title} (Copy)`,
      submission_count: 0,
    };
  },
};

// Form Builder Constants
export const FORM_BUILDER_CONSTANTS = {
  DEFAULT_FIELD_TYPES: [
    "text",
    "textarea",
    "email",
    "number",
    "select",
    "radio",
    "checkbox",
    "date",
    "time",
    "datetime",
    "file",
    "phone",
    "url",
    "rating",
    "location",
  ],
  MAX_FIELDS_PER_FORM: 50,
  MAX_OPTIONS_PER_FIELD: 20,
  MAX_FORM_TITLE_LENGTH: 200,
  MAX_FIELD_LABEL_LENGTH: 100,
  MAX_DESCRIPTION_LENGTH: 1000,
  DEFAULT_SUBMIT_BUTTON_TEXT: "Submit",
  DEFAULT_THEME: "default",
};

export default formBuilderAPI;
