import apiService from './apiService';
import type {
  User,
  LoginRequest,
  LoginResponse,
  Report,
  ReportTemplate,
  ReportStats,
  DashboardStats,
  ChartData,
  FileInfo,
  FileStats,
  Form,
  FormField,
  WordTemplate,
  TemplateContent,
  ReportGenerationRequest,
  ReportGenerationResponse,
  ExcelReportGenerationRequest,
  ExcelReportGenerationResponse,
  AIAnalysisRequest,
  AIAnalysisResponse,
  DatabaseTestResponse,
  PaginatedResponse,
  RequestConfig
} from '../types/api.types';

// Re-export the apiService instance for backward compatibility
export const api = apiService;
export const authApi = apiService; // Use the same service for both

// No authentication required - all endpoints are public

// Re-export types for backward compatibility
export type {
  User,
  LoginRequest,
  LoginResponse,
  Report,
  ReportTemplate,
  ReportStats,
  DashboardStats,
  ChartData,
  FileInfo,
  FileStats,
  Form,
  FormField,
  WordTemplate,
  TemplateContent,
  ReportGenerationRequest,
  ReportGenerationResponse,
  ExcelReportGenerationRequest,
  ExcelReportGenerationResponse,
  AIAnalysisRequest,
  AIAnalysisResponse,
  DatabaseTestResponse,
  PaginatedResponse,
  RequestConfig
};

// All types are now imported from api.types.ts

// Authentication APIs
export const login = async (
  credentials: LoginRequest
): Promise<LoginResponse> => {
  return await apiService.login(credentials);
};

export const register = async (userData: {
  email: string;
  password: string;
  confirmPassword: string;
}): Promise<LoginResponse> => {
  return await apiService.register(userData);
};

export const getCurrentUser = async (): Promise<User> => {
  return await apiService.getCurrentUser();
};

export const logout = async (): Promise<void> => {
  await apiService.logout();
};

// Dashboard APIs
export const fetchDashboardStats = async (): Promise<DashboardStats> => {
  return await apiService.get<DashboardStats>("/dashboard/stats");
};

export const fetchChartData = async (
  type: string = "reports_by_status"
): Promise<ChartData> => {
  return await apiService.get<ChartData>(`/dashboard/charts?type=${type}`);
};

export const fetchRecentActivity = async (
  limit: number = 10
): Promise<{
  recent_activity: Report[];
  total: number;
}> => {
  return await apiService.get<{
    recent_activity: Report[];
    total: number;
  }>(`/dashboard/recent?limit=${limit}`);
};

export const fetchDashboardSummary = async (): Promise<{
  user: User;
  quickStats: Record<string, number>;
  recentReports: Report[];
  availableTemplates: ReportTemplate[];
}> => {
  return await apiService.get<{
    user: User;
    quickStats: Record<string, number>;
    recentReports: Report[];
    availableTemplates: ReportTemplate[];
  }>("/dashboard/summary");
};

export const refreshDashboard = async (): Promise<{
  message: string;
  timestamp: string;
}> => {
  return await apiService.post<{
    message: string;
    timestamp: string;
  }>("/dashboard/refresh");
};

export const fetchPerformanceMetrics = async (): Promise<
  Record<string, unknown>
> => {
  return await apiService.get<Record<string, unknown>>("/dashboard/performance");
};

export const fetchTimelineData = async (
  days: number = 30
): Promise<{
  timeline: Record<string, unknown>[];
  period: string;
}> => {
  return await apiService.get<{
    timeline: Record<string, unknown>[];
    period: string;
  }>(`/dashboard/timeline?days=${days}`);
};

// Reports APIs
export const fetchReports = async (): Promise<Report[]> => {
  return await apiService.get<Report[]>("/reports");
};

export const fetchRecentReports = async (): Promise<Report[]> => {
  return await apiService.get<Report[]>("/reports/recent");
};

export const fetchReportsHistory = async (
  page: number = 1,
  per_page: number = 20,
  status?: string,
  search?: string
): Promise<{
  reports: Report[];
  pagination: {
    page: number;
    pages: number;
    per_page: number;
    total: number;
    has_next: boolean;
    has_prev: boolean;
  };
}> => {
  const params = new URLSearchParams({
    page: page.toString(),
    per_page: per_page.toString(),
  });

  if (status) params.append("status", status);
  if (search) params.append("search", search);

  return await apiService.get<{
    reports: Report[];
    pagination: {
      page: number;
      pages: number;
      per_page: number;
      total: number;
      has_next: boolean;
      has_prev: boolean;
    };
  }>(`/reports/history?${params.toString()}`);
};

export const fetchReportStats = async (): Promise<ReportStats> => {
  return await apiService.get<ReportStats>("/reports/stats");
};

export const fetchReportTemplates = async (): Promise<ReportTemplate[]> => {
  return await apiService.get<ReportTemplate[]>("/production/reports/templates");
};

export const updateReportTemplate = async (
  id: string,
  templateData: Partial<ReportTemplate>
): Promise<ReportTemplate> => {
  return await apiService.put<ReportTemplate>(`/production/reports/templates/${id}`, templateData);
};

export const createReportTemplate = async (
  templateData: Partial<ReportTemplate>
): Promise<ReportTemplate> => {
  return await apiService.post<ReportTemplate>('/production/reports/templates', templateData);
};

export const uploadReportTemplate = async (
  file: File,
  name?: string,
  description?: string,
  type?: string
): Promise<ReportTemplate> => {
  const formData = new FormData();
  formData.append('template_file', file);
  if (name) formData.append('name', name);
  if (description) formData.append('description', description);
  if (type) formData.append('type', type);
  
  return await apiService.post<ReportTemplate>('/production/reports/templates/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
};

export const createReport = async (
  reportData: Partial<Report>
): Promise<Report> => {
  return await apiService.post<Report>("/reports", reportData);
};

export const updateReport = async (
  id: string,
  reportData: Partial<Report>
): Promise<Report> => {
  return await apiService.put<Report>(`/reports/${id}`, reportData);
};

export const deleteReport = async (id: string): Promise<void> => {
  await apiService.delete(`/reports/${id}`);
};

export const getReportStatus = async (
  taskId: string
): Promise<{
  status: string;
  result?: Record<string, unknown>;
}> => {
  return await apiService.get<{
    status: string;
    result?: Record<string, unknown>;
  }>(`/reports/${taskId}`);
};

// Users APIs
export const fetchUserProfile = async (): Promise<User> => {
  return await apiService.get<User>("/users/profile");
};

export interface UpdateUserProfileResponse {
  message: string;
  user: User;
}

export const updateUserProfile = async (
  userData: Partial<User>
): Promise<UpdateUserProfileResponse> => {
  return await apiService.put<UpdateUserProfileResponse>("/users/profile", userData);
};

export const fetchUserSettings = async (): Promise<Record<string, unknown>> => {
  return await apiService.get<Record<string, unknown>>("/users/settings");
};

export const updateUserSettings = async (
  settings: Record<string, unknown>
): Promise<Record<string, unknown>> => {
  return await apiService.put<Record<string, unknown>>("/users/settings", settings);
};

// Forms APIs
export const fetchForms = async (): Promise<Form[]> => {
  return await apiService.get<Form[]>("/forms/");
};

export const createForm = async (formData: Partial<Form>): Promise<Form> => {
  return await apiService.post<Form>("/forms/", formData);
};

export const updateForm = async (
  id: string,
  formData: Partial<Form>
): Promise<Form> => {
  return await apiService.put<Form>(`/forms/${id}`, formData);
};

export const deleteForm = async (id: string): Promise<void> => {
  await apiService.delete(`/forms/${id}`);
};

// Files APIs
export const fetchFiles = async (
  page: number = 1,
  perPage: number = 10
): Promise<{
  files: FileInfo[];
  pagination: {
    page: number;
    pages: number;
    per_page: number;
    total: number;
  };
}> => {
  return await apiService.get<{
    files: FileInfo[];
    pagination: {
      page: number;
      pages: number;
      per_page: number;
      total: number;
    };
  }>(`/files/?page=${page}&per_page=${perPage}`);
};

export const uploadFile = async (formData: FormData): Promise<FileInfo> => {
  return await apiService.post<FileInfo>("/files/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
};

export const downloadFile = async (fileId: string): Promise<Blob> => {
  // For blob downloads, we need to use axios directly with responseType
  const response = await apiService.get<Blob>(`/files/${fileId}/download`, {
    headers: {
      'Accept': 'application/octet-stream',
    },
  });
  return response;
};

export const deleteFile = async (fileId: string): Promise<void> => {
  await apiService.delete(`/files/${fileId}`);
};

export const fetchFileStats = async (): Promise<FileStats> => {
  return await apiService.get<FileStats>("/files/stats");
};

export const updateFileVisibility = async (
  fileId: string,
  isPublic: boolean
): Promise<{ message: string; is_public: boolean }> => {
  return await apiService.put<{ message: string; is_public: boolean }>(`/files/${fileId}/visibility`, {
    is_public: isPublic,
  });
};

export const renameFile = async (
  fileId: string,
  filename: string
): Promise<{ message: string; filename: string }> => {
  return await apiService.put<{ message: string; filename: string }>(`/files/${fileId}/rename`, { filename });
};

export const searchFiles = async (
  query: string,
  page: number = 1,
  perPage: number = 10
): Promise<{
  query: string;
  files: FileInfo[];
  pagination: {
    page: number;
    pages: number;
    per_page: number;
    total: number;
  };
}> => {
  return await apiService.get<{
    query: string;
    files: FileInfo[];
    pagination: {
      page: number;
      pages: number;
      per_page: number;
      total: number;
    };
  }>(`/files/search?q=${encodeURIComponent(
    query
  )}&page=${page}&per_page=${perPage}`);
};

// Fetch placeholders for a given template (Word docx)
export const fetchTemplatePlaceholders = async (
  templateName: string
): Promise<string[]> => {
  const result = await apiService.get<{ placeholders: string[] }>(
    `/mvp/templates/${encodeURIComponent(templateName)}/placeholders`
  );
  return result.placeholders;
};

// Fetch list of available Word templates
export const fetchWordTemplates = async (): Promise<
  Array<{
    id: string;
    name: string;
    description: string;
    filename: string;
    previewUrl?: string;
  }>
> => {
  return await apiService.get<Array<{
    id: string;
    name: string;
    description: string;
    filename: string;
    previewUrl?: string;
  }>>("/mvp/templates/list");
};

// Extract template content for frontend editing
export const fetchTemplateContent = async (
  templateName: string
): Promise<{
  content: Array<{ type: string; text: string; style: string }>;
  placeholders: string[];
}> => {
  return await apiService.get<{
    content: Array<{ type: string; text: string; style: string }>;
    placeholders: string[];
  }>(`/mvp/templates/${encodeURIComponent(templateName)}/content`);
};

// Generate live preview of filled template
export const generateLivePreview = async (
  templateName: string,
  data: Record<string, string>
): Promise<{
  preview: string;
  filename: string;
}> => {
  return await apiService.post<{
    preview: string;
    filename: string;
  }>(`/mvp/templates/${encodeURIComponent(templateName)}/preview`, {
    data,
  });
};

// Generate final report using MVP endpoint
export const generateReport = async (
  templateFilename: string,
  data: Record<string, string>
): Promise<{
  downloadUrl: string;
  message: string;
}> => {
  return await apiService.post<{
    downloadUrl: string;
    message: string;
  }>("/mvp/generate-report", {
    templateFilename,
    data,
  });
};

// Fetch a template file (e.g., Temp1.docx) as Blob from server templates dir
export const fetchTemplateBlob = async (templateName: string): Promise<Blob> => {
  // For blob downloads, we need to use axios directly with responseType
  const response = await apiService.get<Blob>(
    `/mvp/templates/${encodeURIComponent(templateName)}/download`,
    {
      headers: {
        'Accept': 'application/octet-stream',
      },
    }
  );
  return response;
};

// Generate report by uploading Excel + DOCX template to backend mapper
export const generateReportWithExcel = async (
  templateFilename: string,
  excelFile: File
): Promise<{
  success: boolean;
  downloadUrl: string;
  filename: string;
  message: string;
  context_used?: Record<string, unknown>;
  optimizations?: Record<string, unknown>;
  missing_fields?: string[];
}> => {
  try {
    // Get template blob from server so user doesn't need to upload it manually
    const templateBlob = await fetchTemplateBlob(templateFilename);
    const formData = new FormData();
    formData.append(
      "template_file",
      new File([templateBlob], templateFilename, {
        type:
          "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      })
    );
    formData.append("excel_file", excelFile);

    return await apiService.post<{
      success: boolean;
      downloadUrl: string;
      filename: string;
      message: string;
      context_used?: Record<string, unknown>;
      optimizations?: Record<string, unknown>;
      missing_fields?: string[];
    }>(`/mvp/templates/generate-with-excel`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  } catch (err: any) {
    const status = err?.response?.status;
    const server = err?.response?.data || {};
    const msg = server?.error || server?.message || err?.message || 'Generation failed';
    const hint = server?.hint ? ` Hint: ${server.hint}` : '';
    throw new Error(`${msg}${hint}${status ? ` (HTTP ${status})` : ''}`);
  }
};

// Download generated report
export const downloadReport = async (
  downloadUrl: string,
  filename?: string
): Promise<void> => {
  try {
    // If downloadUrl is relative, make it absolute
    const fullUrl = downloadUrl.startsWith("http")
      ? downloadUrl
      : `${apiService.getBaseURL()}${downloadUrl}`;

    // Fetch the file
    const response = await fetch(fullUrl);
    if (!response.ok) {
      throw Error(`Download failed: ${response.statusText}`);
    }

    // Get the blob
    const blob = await response.blob();

    // Create download link
    const link = document.createElement("a");
    const url = window.URL.createObjectURL(blob);
    link.href = url;
    link.download = filename || "generated_report.docx";
    document.body.appendChild(link);
    link.click();

    // Cleanup
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Download failed:", error);
    throw error;
  }
};

// Database test
export const testDatabaseConnection = async (): Promise<{
  status: string;
  message: string;
  table_count: number;
}> => {
  return await apiService.get<{
    status: string;
    message: string;
    table_count: number;
  }>("/test-db");
};

// AI Analysis (placeholder for future implementation)
export const analyzeData = async (
  data: Record<string, unknown>
): Promise<{
  summary: string;
  insights: string[];
  suggestions: string;
}> => {
  // This would connect to an AI service when implemented
  return await apiService.post<{
    summary: string;
    insights: string[];
    suggestions: string;
  }>("/ai/analyze", data);
};

// Note: Interceptors are now handled by the ApiService class
// No need for manual interceptor setup here
