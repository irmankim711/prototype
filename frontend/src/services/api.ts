import axios from "axios";

// API Configuration
const API_BASE_URL = "http://localhost:5000";

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// Auth API instance for authentication endpoints
const authApi = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// No authentication required - all endpoints are public

// Types
export interface User {
  id: string;
  email: string;
  created_at: string;
  role?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  user: User;
}

export interface Report {
  id: string;
  title: string;
  description?: string;
  status: "draft" | "processing" | "completed" | "failed";
  createdAt: string;
  updatedAt: string;
  templateId: string;
  templateFilename?: string;
  outputUrl?: string;
  data?: Record<string, unknown>;
  analysis?: any;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description?: string;
  schema: Record<string, unknown>;
  isActive: boolean;
}

export interface ReportStats {
  totalReports: number;
  reportsThisMonth: number;
  activeTemplates: number;
  processingReports: number;
}

export interface DashboardStats {
  totalReports: number;
  completedReports: number;
  pendingReports: number;
  recentActivity: number;
  successRate: number;
  avgProcessingTime: number;
}

export interface ChartData {
  type: string;
  data: {
    labels: string[];
    data: number[];
    backgroundColor?: string[];
    borderColor?: string;
  };
}

export interface FileInfo {
  id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  created_at: string;
  uploader_id: string;
  is_public: boolean;
  url: string;
}

export interface FileStats {
  total_files: number;
  total_size_bytes: number;
  total_size_mb: number;
  public_files: number;
  private_files: number;
  weekly_uploads: number;
}

export interface Form {
  id: string;
  title: string;
  description?: string;
  fields: FormField[];
  created_at: string;
  is_active: boolean;
  is_public?: boolean;
}

export interface FormField {
  id: string;
  name: string;
  type: string;
  label: string;
  required: boolean;
  options?: string[];
}

// Authentication APIs
export const login = async (
  credentials: LoginRequest
): Promise<LoginResponse> => {
  const { data } = await authApi.post("/auth/login", credentials);
  if (data.access_token) {
    localStorage.setItem("token", data.access_token);
  }
  return data;
};

export const register = async (userData: {
  email: string;
  password: string;
  confirmPassword: string;
}): Promise<LoginResponse> => {
  const { data } = await authApi.post("/auth/register", userData);
  if (data.access_token) {
    localStorage.setItem("token", data.access_token);
  }
  return data;
};

export const getCurrentUser = async (): Promise<User> => {
  const { data } = await authApi.get("/auth/me");
  return data;
};

export const logout = (): void => {
  localStorage.removeItem("token");
};

// Dashboard APIs
export const fetchDashboardStats = async (): Promise<DashboardStats> => {
  const { data } = await api.get("/dashboard/stats");
  return data;
};

export const fetchChartData = async (
  type: string = "reports_by_status"
): Promise<ChartData> => {
  const { data } = await api.get(`/dashboard/charts?type=${type}`);
  return data;
};

export const fetchRecentActivity = async (
  limit: number = 10
): Promise<{
  recent_activity: Report[];
  total: number;
}> => {
  const { data } = await api.get(`/dashboard/recent?limit=${limit}`);
  return data;
};

export const fetchDashboardSummary = async (): Promise<{
  user: User;
  quickStats: Record<string, number>;
  recentReports: Report[];
  availableTemplates: ReportTemplate[];
}> => {
  const { data } = await api.get("/dashboard/summary");
  return data;
};

export const refreshDashboard = async (): Promise<{
  message: string;
  timestamp: string;
}> => {
  const { data } = await api.post("/dashboard/refresh");
  return data;
};

export const fetchPerformanceMetrics = async (): Promise<
  Record<string, unknown>
> => {
  const { data } = await api.get("/dashboard/performance");
  return data;
};

export const fetchTimelineData = async (
  days: number = 30
): Promise<{
  timeline: Record<string, unknown>[];
  period: string;
}> => {
  const { data } = await api.get(`/api/dashboard/timeline?days=${days}`);
  return data;
};

// Reports APIs
export const fetchReports = async (): Promise<Report[]> => {
  const { data } = await api.get("/reports");
  return data;
};

export const fetchRecentReports = async (): Promise<Report[]> => {
  const { data } = await api.get("/reports/recent");
  return data;
};

export const fetchReportStats = async (): Promise<ReportStats> => {
  const { data } = await api.get("/reports/stats");
  return data;
};

export const fetchReportTemplates = async (): Promise<ReportTemplate[]> => {
  const { data } = await api.get("/reports/templates");
  return data;
};

export const updateReportTemplate = async (
  id: string,
  templateData: Partial<ReportTemplate>
): Promise<ReportTemplate> => {
  const { data } = await api.put(`/reports/templates/${id}`, templateData);
  return data;
};

export const createReport = async (
  reportData: Partial<Report>
): Promise<Report> => {
  const { data } = await api.post("/reports", reportData);
  return data;
};

export const updateReport = async (
  id: string,
  reportData: Partial<Report>
): Promise<Report> => {
  const { data } = await api.put(`/reports/${id}`, reportData);
  return data;
};

export const deleteReport = async (id: string): Promise<void> => {
  await api.delete(`/reports/${id}`);
};

export const getReportStatus = async (
  taskId: string
): Promise<{
  status: string;
  result?: Record<string, unknown>;
}> => {
  const { data } = await api.get(`/reports/${taskId}`);
  return data;
};

// Users APIs
export const fetchUserProfile = async (): Promise<User> => {
  const { data } = await api.get("/api/users/profile");
  return data;
};

export const updateUserProfile = async (
  userData: Partial<User>
): Promise<User> => {
  const { data } = await api.put("/api/users/profile", userData);
  return data;
};

export const fetchUserSettings = async (): Promise<Record<string, unknown>> => {
  const { data } = await api.get("/api/users/settings");
  return data;
};

export const updateUserSettings = async (
  settings: Record<string, unknown>
): Promise<Record<string, unknown>> => {
  const { data } = await api.put("/api/users/settings", settings);
  return data;
};

// Forms APIs
export const fetchForms = async (): Promise<Form[]> => {
  const { data } = await api.get("/api/forms/");
  return data;
};

export const createForm = async (formData: Partial<Form>): Promise<Form> => {
  const { data } = await api.post("/api/forms/", formData);
  return data;
};

export const updateForm = async (
  id: string,
  formData: Partial<Form>
): Promise<Form> => {
  const { data } = await api.put(`/api/forms/${id}`, formData);
  return data;
};

export const deleteForm = async (id: string): Promise<void> => {
  await api.delete(`/api/forms/${id}`);
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
  const { data } = await api.get(
    `/api/files/?page=${page}&per_page=${perPage}`
  );
  return data;
};

export const uploadFile = async (formData: FormData): Promise<FileInfo> => {
  const { data } = await api.post("/api/files/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return data;
};

export const downloadFile = async (fileId: string): Promise<Blob> => {
  const response = await api.get(`/api/files/${fileId}/download`, {
    responseType: "blob",
  });
  return response.data;
};

export const deleteFile = async (fileId: string): Promise<void> => {
  await api.delete(`/api/files/${fileId}`);
};

export const fetchFileStats = async (): Promise<FileStats> => {
  const { data } = await api.get("/api/files/stats");
  return data;
};

export const updateFileVisibility = async (
  fileId: string,
  isPublic: boolean
): Promise<{ message: string; is_public: boolean }> => {
  const { data } = await api.put(`/api/files/${fileId}/visibility`, {
    is_public: isPublic,
  });
  return data;
};

export const renameFile = async (
  fileId: string,
  filename: string
): Promise<{ message: string; filename: string }> => {
  const { data } = await api.put(`/api/files/${fileId}/rename`, { filename });
  return data;
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
  const { data } = await api.get(
    `/api/files/search?q=${encodeURIComponent(
      query
    )}&page=${page}&per_page=${perPage}`
  );
  return data;
};

// Fetch placeholders for a given template (Word docx)
export const fetchTemplatePlaceholders = async (
  templateName: string
): Promise<string[]> => {
  const { data } = await api.get(
    `/mvp/templates/${encodeURIComponent(templateName)}/placeholders`
  );
  return data.placeholders;
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
  const { data } = await api.get("/mvp/templates/list");
  return data;
};

// Extract template content for frontend editing
export const fetchTemplateContent = async (
  templateName: string
): Promise<{
  content: Array<{ type: string; text: string; style: string }>;
  placeholders: string[];
}> => {
  const { data } = await api.get(
    `/mvp/templates/${encodeURIComponent(templateName)}/content`
  );
  return data;
};

// Generate live preview of filled template
export const generateLivePreview = async (
  templateName: string,
  data: Record<string, string>
): Promise<{
  preview: string;
  filename: string;
}> => {
  const { data: result } = await api.post(
    `/mvp/templates/${encodeURIComponent(templateName)}/preview`,
    {
      data,
    }
  );
  return result;
};

// Generate final report using MVP endpoint
export const generateReport = async (
  templateFilename: string,
  data: Record<string, string>
): Promise<{
  downloadUrl: string;
  message: string;
}> => {
  const { data: result } = await api.post("/mvp/generate-report", {
    templateFilename,
    data,
  });
  return result;
};

// Download generated report
export const downloadReport = async (downloadUrl: string): Promise<void> => {
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = "generated_report.docx";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Database test
export const testDatabaseConnection = async (): Promise<{
  status: string;
  message: string;
  table_count: number;
}> => {
  const { data } = await api.get("/test-db");
  return data;
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
  const { data: result } = await api.post("/ai/analyze", data);
  return result;
};

// Error handler
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem("token");
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);

authApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem("token");
      window.location.href = "/";
    }
    return Promise.reject(error);
  }
);
