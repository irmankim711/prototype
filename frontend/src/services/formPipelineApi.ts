/**
 * API service for Form Data Pipeline operations
 */

import axios from "axios";

// Use existing API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface DataSource {
  id: number;
  name: string;
  source_type: string;
  source_id: string;
  source_url?: string;
  is_active: boolean;
  auto_sync: boolean;
  sync_interval: number;
  last_sync?: string;
  created_at: string;
  submission_count: number;
}

export interface ExcelExport {
  id: number;
  name: string;
  description?: string;
  export_status: string;
  export_progress: number;
  file_name?: string;
  file_size?: number;
  total_submissions: number;
  processed_submissions: number;
  error_count: number;
  started_at?: string;
  completed_at?: string;
  export_duration?: number;
  created_at: string;
  is_auto_generated: boolean;
  auto_schedule?: string;
  next_auto_export?: string;
}

export interface CreateDataSourceRequest {
  name: string;
  source_type: string;
  source_id: string;
  source_url?: string;
  webhook_secret?: string;
  api_config?: Record<string, unknown>;
  field_mapping?: Record<string, string>;
  auto_sync?: boolean;
  sync_interval?: number;
}

export interface CreateExportRequest {
  name: string;
  description?: string;
  data_sources: number[];
  date_range_start?: string;
  date_range_end?: string;
  filters?: Record<string, unknown>;
  template_config?: Record<string, unknown>;
  is_auto_generated?: boolean;
  auto_schedule?: string;
}

export interface AnalyticsSummary {
  total_data_sources: number;
  total_submissions: number;
  recent_submissions: number;
  active_exports: number;
  last_sync?: string;
  data_sources: DataSource[];
}

export const formPipelineApi = {
  // Data Sources
  async getDataSources(params?: {
    source_type?: string;
    is_active?: boolean;
    page?: number;
    per_page?: number;
  }) {
    const response = await apiClient.get("/api/forms/data-sources", { params });
    return response.data;
  },

  async createDataSource(data: CreateDataSourceRequest) {
    const response = await apiClient.post("/api/forms/data-sources", data);
    return response.data;
  },

  async updateDataSource(id: number, data: Partial<CreateDataSourceRequest>) {
    const response = await apiClient.put(`/api/forms/data-sources/${id}`, data);
    return response.data;
  },

  async deleteDataSource(id: number) {
    const response = await apiClient.delete(`/api/forms/data-sources/${id}`);
    return response.data;
  },

  async manualSync(dataSourceId: number) {
    const response = await apiClient.post(
      `/api/forms/data-sources/${dataSourceId}/sync`
    );
    return response.data;
  },

  // Excel Exports
  async getExcelExports(params?: {
    status?: string;
    page?: number;
    per_page?: number;
  }) {
    const response = await apiClient.get("/api/forms/export", { params });
    return response.data;
  },

  async createExcelExport(data: CreateExportRequest) {
    const response = await apiClient.post("/api/forms/export", data);
    return response.data;
  },

  async downloadExport(exportId: number): Promise<Blob> {
    const response = await apiClient.get(
      `/api/forms/export/${exportId}/download`,
      {
        responseType: "blob",
      }
    );
    return response.data;
  },

  async deleteExport(exportId: number) {
    const response = await apiClient.delete(`/api/forms/export/${exportId}`);
    return response.data;
  },

  // Analytics
  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const response = await apiClient.get("/api/forms/analytics/summary");
    return response.data;
  },

  // Webhook testing
  async testWebhook(sourceType: string, testData: Record<string, unknown>) {
    const response = await apiClient.post(
      `/api/forms/webhook/test/${sourceType}`,
      testData
    );
    return response.data;
  },
};
