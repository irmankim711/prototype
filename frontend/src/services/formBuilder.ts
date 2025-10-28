import axiosInstance from "./axiosInstance";

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
  // Additional fields for submissions page
  name?: string;
  email?: string;
  date?: string;
  score?: number;
  form_id?: number;
  form_title?: string;
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

// API Base URL - Using relative path since Vite proxy handles routing to backend
const API_BASE_URL = "/api";

// Use the configured axios instance instead of creating a new one
const api = axiosInstance;

// Token getter function that can be set from outside
let getAuthToken: () => string | null = () =>
  localStorage.getItem("accessToken");

// Function to set the token getter (called from AuthContext)
export const setTokenGetter = (getter: () => string | null) => {
  getAuthToken = getter;
};

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
    const response = await api.get(`/forms/${formId}`);
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
    const response = await api.post("/forms/", formData);
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
    const response = await api.put(`/forms/${formId}`, formData);
    return response.data;
  },

  // Delete a form (soft delete)
  deleteForm: async (formId: number) => {
    const response = await api.delete(`/forms/${formId}`);
    return response.data;
  },

  // Toggle form status (admin only)
  toggleFormStatus: async (
    formId: number,
    data: {
      is_public?: boolean;
      is_active?: boolean;
    }
  ) => {
    const response = await api.patch(
      `/forms/admin/toggle-status/${formId}`,
      data
    );
    return response.data;
  },

  // Get public forms (no authentication required)
  getPublicForms: async () => {
    // Use a separate axios instance without auth for public endpoint
    const publicResponse = await api.get("/forms/public", {
      baseURL: API_BASE_URL,
      timeout: 10000,
    });

    // Extract forms array from API response
    const responseData = publicResponse.data;
    if (
      responseData &&
      responseData.success &&
      Array.isArray(responseData.forms)
    ) {
      return responseData.forms;
    }

    // Fallback: return empty array if response structure is unexpected
    return [];
  },

  // Get available field types
  getFieldTypes: async (): Promise<FormBuilderConfig> => {
    const response = await api.get("/forms/field-types");
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
    const response = await api.post(`/forms/${formId}/submissions`, data);
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
    const response = await api.get(`/forms/${formId}/submissions`, {
      params,
    });
    return response.data;
  },

  // Update submission status
  updateSubmissionStatus: async (submissionId: number, status: string) => {
    const response = await api.put(
      `/forms/submissions/${submissionId}/status`,
      {
        status,
      }
    );
    return response.data;
  },

  // Get all submissions across all forms
  getAllSubmissions: async (params?: {
    page?: number;
    per_page?: number;
    status?: string;
    date_from?: string;
    date_to?: string;
    form_id?: number;
  }) => {
    const response = await api.get("/forms/submissions", {
      params,
    });
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
    const response = await api.post(`/forms/${formId}/qr-codes`, qrData);
    return response.data;
  },

  getFormQRCodes: async (
    formId: number
  ): Promise<{ qr_codes: FormQRCode[]; count: number }> => {
    const response = await api.get(`/forms/${formId}/qr-codes`);
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
    const response = await api.put(`/forms/${formId}/qr-codes/${qrId}`, qrData);
    return response.data;
  },

  deleteFormQRCode: async (formId: number, qrId: number) => {
    const response = await api.delete(`/forms/${formId}/qr-codes/${qrId}`);
    return response.data;
  },

  trackQRScan: async (qrId: number) => {
    const response = await api.post(`/forms/qr/${qrId}/scan`);
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
    const response = await api.get(`/forms/${formId}/export`, {
      params: { format },
      responseType: format === "json" ? "json" : "blob",
    });
    return response.data;
  },

  // ========================================
  // FORM DATA FETCHING AND EXCEL EXPORT
  // ========================================

  // Fetch form data with filtering and pagination
  fetchFormData: async (
    formId: number,
    params?: {
      page?: number;
      per_page?: number;
      status?: string;
      date_from?: string;
      date_to?: string;
      submitter_email?: string;
      include_metadata?: boolean;
      include_analytics?: boolean;
    }
  ) => {
    const response = await api.get(`/forms/${formId}/fetch-data`, {
      params,
    });
    return response.data;
  },

  // ========================================
  // PROFESSIONAL FORM DATA EXPORT API
  // ========================================

  /**
   * Export form data to Excel, CSV, or Google Sheets
   * @param formId - The form ID to export
   * @param options - Export options
   * @returns Export result with download URL
   */
  exportFormDataToExcel: async (formId: number, options: {
    format?: 'excel' | 'csv' | 'googlesheets';
    date_range?: { start?: string; end?: string };
    filters?: { status?: string; submitter_email?: string };
    include_analytics?: boolean;
    excel_options?: {
      include_form_schema?: boolean;
      include_submission_metadata?: boolean;
      formatting?: 'professional' | 'basic' | 'custom';
      compression?: boolean;
    };
    max_records?: number;
  }): Promise<any> => {
    try {
      const response = await axiosInstance.post(`/api/forms/${formId}/export`, {
        format: options.format || 'excel',
        date_range: options.date_range,
        filters: options.filters,
        include_analytics: options.include_analytics !== false,
        excel_options: options.excel_options || {
          include_form_schema: true,
          include_submission_metadata: true,
          formatting: 'professional',
          compression: true
        },
        max_records: options.max_records || 10000
      });
      return response.data;
    } catch (error: any) {
      console.error('Error exporting form data:', error);
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Export failed'
      };
    }
  },

  /**
   * Export Google Forms responses to Excel or CSV
   * @param googleFormId - The Google Form ID
   * @param options - Export options
   * @returns Export result with download URL
   */
  exportGoogleFormsToExcel: async (googleFormId: string, options: {
    format?: 'excel' | 'csv';
    date_range?: { start?: string; end?: string };
    include_analytics?: boolean;
    max_records?: number;
  }): Promise<any> => {
    try {
      const response = await axiosInstance.post(
        `/api/forms/google-forms/${googleFormId}/export`,
        {
          format: options.format || 'excel',
          date_range: options.date_range,
          include_analytics: options.include_analytics !== false,
          max_records: options.max_records || 1000
        },
        {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        }
      );
      return response.data;
    } catch (error: any) {
      console.error('Error exporting Google Forms data:', error);
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Google Forms export failed'
      };
    }
  },

  /**
   * Download exported file (Excel, CSV, etc.)
   * @param downloadUrl - The download URL from export response
   * @param filename - Optional filename for the download
   * @returns Blob data for file download
   */
  downloadExcelFile: async (downloadUrl: string, filename?: string): Promise<Blob> => {
    try {
      const response = await axiosInstance.get(downloadUrl, {
        responseType: 'blob'
      });

      // Automatically trigger browser download
      const blob = response.data;
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;

      // Extract filename from downloadUrl if not provided
      if (!filename) {
        const urlParts = downloadUrl.split('/');
        filename = urlParts[urlParts.length - 1] || 'export.xlsx';
      }

      link.download = filename;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      return blob;
    } catch (error) {
      console.error('Error downloading file:', error);
      throw error;
    }
  },

  /**
   * Complete export and download flow with progress tracking
   * @param formId - The form ID to export
   * @param options - Export options
   * @param onProgress - Optional progress callback
   * @returns Export result
   */
  exportAndDownload: async (
    formId: number,
    options: Parameters<typeof formBuilderAPI.exportFormDataToExcel>[1],
    onProgress?: (stage: string, progress: number) => void
  ): Promise<{ success: boolean; message?: string; error?: string }> => {
    try {
      // Stage 1: Initiate export
      onProgress?.('Preparing export...', 10);

      const exportResult = await formBuilderAPI.exportFormDataToExcel(formId, options);

      if (!exportResult.success) {
        return {
          success: false,
          error: exportResult.error || 'Export failed'
        };
      }

      // Stage 2: Download file
      onProgress?.('Downloading file...', 50);

      await formBuilderAPI.downloadExcelFile(exportResult.download_url);

      // Stage 3: Complete
      onProgress?.('Complete', 100);

      return {
        success: true,
        message: exportResult.message || 'Export completed successfully'
      };
    } catch (error: any) {
      console.error('Error in export and download flow:', error);
      return {
        success: false,
        error: error.message || 'An error occurred during export'
      };
    }
  },

  /**
   * Preview form data before exporting
   * @param formId - The form ID
   * @param options - Filter options
   * @returns Preview data with sample submissions
   */
  previewFormData: async (formId: number, options?: {
    date_range?: { start?: string; end?: string };
    filters?: { status?: string; submitter_email?: string };
    include_analytics?: boolean;
  }): Promise<any> => {
    try {
      const response = await axiosInstance.post(`/api/forms/${formId}/preview`, {
        date_range: options?.date_range,
        filters: options?.filters,
        include_analytics: options?.include_analytics !== false
      });
      return response.data;
    } catch (error: any) {
      console.error('Error previewing form data:', error);
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Preview failed'
      };
    }
  },

  /**
   * Preview Google Forms responses before exporting
   * @param googleFormId - The Google Form ID
   * @param options - Preview options
   * @returns Preview data with sample responses
   */
  previewGoogleFormData: async (googleFormId: string, options?: {
    limit?: number;
    include_analysis?: boolean;
  }): Promise<any> => {
    try {
      const response = await axiosInstance.get(`/api/forms/google-forms/${googleFormId}/preview`, {
        params: {
          limit: options?.limit || 10,
          include_analysis: options?.include_analysis !== false
        }
      });
      return response.data;
    } catch (error: any) {
      console.error('Error previewing Google Forms data:', error);
      return {
        success: false,
        error: error.response?.data?.error || error.message || 'Google Forms preview failed'
      };
    }
  },

  // Google Forms API methods
  getGoogleFormsStatus: async (): Promise<any> => {
    try {
      const response = await axiosInstance.get('/api/google-forms/status');
      return response.data;
    } catch (error) {
      console.error('Error getting Google Forms status:', error);
      throw error;
    }
  },

  getGoogleForms: async (pageSize: number = 10): Promise<any> => {
    try {
      const response = await axiosInstance.get('/api/google-forms/forms', {
        params: { page_size: pageSize }
      });
      return response.data;
    } catch (error) {
      console.error('Error fetching Google Forms:', error);
      throw error;
    }
  },

  getGoogleFormInfo: async (formId: string): Promise<any> => {
    try {
      const response = await axiosInstance.get(`/api/google-forms/forms/${formId}/info`);
      return response.data;
    } catch (error) {
      console.error('Error fetching Google Form info:', error);
      throw error;
    }
  },

  getGoogleFormResponses: async (formId: string, options: any = {}): Promise<any> => {
    try {
      const params = {
        limit: options.limit || 100,
        include_analysis: options.include_analysis || false
      };
      const response = await axiosInstance.get(`/api/google-forms/forms/${formId}/responses`, { params });
      return response.data;
    } catch (error) {
      console.error('Error fetching Google Form responses:', error);
      throw error;
    }
  },

  initiateGoogleAuth: async (): Promise<any> => {
    try {
      const response = await axiosInstance.post('/api/google-forms/oauth/authorize', {}, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      return response.data;
    } catch (error) {
      console.error('Error initiating Google auth:', error);
      throw error;
    }
  },

  // Get all forms for the current user
  getAllForms: async (): Promise<any> => {
    try {
      const response = await axiosInstance.get('/api/forms');
      return response.data;
    } catch (error) {
      console.error('Error fetching all forms:', error);
      throw error;
    }
  },

  // User Profile Management
  getUserProfile: async (): Promise<any> => {
    try {
      const response = await axiosInstance.get('/api/users/profile');
      return response.data;
    } catch (error) {
      console.error('Error fetching user profile:', error);
      throw error;
    }
  },

  updateUserProfile: async (profileData: any): Promise<any> => {
    try {
      const response = await axiosInstance.put('/api/users/profile', profileData);
      return response.data;
    } catch (error) {
      console.error('Error updating user profile:', error);
      throw error;
    }
  },

  uploadAvatar: async (formData: FormData): Promise<any> => {
    try {
      const response = await axiosInstance.post('/api/users/avatar', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return response.data;
    } catch (error) {
      console.error('Error uploading avatar:', error);
      throw error;
    }
  },

  changePassword: async (passwordData: { currentPassword: string; newPassword: string }): Promise<any> => {
    try {
      const response = await axiosInstance.post('/api/users/change-password', passwordData);
      return response.data;
    } catch (error) {
      console.error('Error changing password:', error);
      throw error;
    }
  },

  deleteAccount: async (): Promise<any> => {
    try {
      const response = await axiosInstance.delete('/api/users/account');
      return response.data;
    } catch (error) {
      console.error('Error deleting account:', error);
      throw error;
    }
  },

  // Get form analytics summary
  getFormAnalytics: async (formId: number, dateRange?: { start: string; end: string }) => {
    const params: any = { include_analytics: true };
    if (dateRange) {
      params.date_from = dateRange.start;
      params.date_to = dateRange.end;
    }
    
    const response = await api.get(`/forms/${formId}/fetch-data`, { params });
    return response.data.analytics;
  },

  // ========================================
  // ACCESS CODE MANAGEMENT
  // ========================================

  // Create generic access code for multiple forms
  createGenericAccessCode: async (accessCodeData: {
    title: string;
    description?: string;
    expires_at?: string;
    max_uses?: number;
    allowed_form_ids: number[];
    allowed_external_forms: Array<{
      id?: string;
      title: string;
      url: string;
      description?: string;
      created_at?: string;
    }>;
  }) => {
    const response = await api.post("/forms/access-codes", accessCodeData);
    return response.data;
  },

  // Get all access codes
  getAllAccessCodes: async () => {
    const response = await api.get("/forms/access-codes");
    return response.data;
  },

  // Get access codes for specific form
  getAccessCodesForForm: async (formId: number) => {
    const response = await api.get(`/forms/${formId}/access-codes`);
    return response.data;
  },

  // Delete access code
  deleteAccessCode: async (codeId: number) => {
    const response = await api.delete(`/forms/access-codes/${codeId}`);
    return response.data;
  },

  // Toggle access code status
  toggleAccessCode: async (codeId: number) => {
    const response = await api.patch(`/forms/access-codes/${codeId}/toggle`);
    return response.data;
  },

  // ========================================
  // PUBLIC ACCESS WITH CODES
  // ========================================

  // Verify access code and get accessible forms
  verifyAccessCode: async (code: string) => {
    const response = await api.post("/forms/public/verify-code", { code });
    return response.data;
  },

  // Get accessible forms with current access code
  getAccessibleForms: async (accessToken: string) => {
    const response = await api.get("/forms/public/code-access/forms", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return response.data;
  },

  // Get specific form with access code
  getFormWithAccessCode: async (formId: number, accessToken: string) => {
    const response = await api.get(`/forms/public/code-access/${formId}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    return response.data;
  },

  // Submit form with access code
  submitFormWithAccessCode: async (
    formId: number,
    formData: Record<string, unknown>,
    accessToken: string
  ) => {
    const response = await api.post(
      `/forms/public/code-access/${formId}/submit`,
      { data: formData },
      { headers: { Authorization: `Bearer ${accessToken}` } }
    );
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

    schema.fields.forEach((field: any) => {
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

    schema.fields.forEach((field: any) => {
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
        throw Error("Invalid form structure");
      }
      return form;
    } catch (error) {
      throw Error("Invalid JSON format");
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

  // User Profile Management
  getUserProfile: async () => {
    const response = await api.get("/api/users/profile");
    return response.data;
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
