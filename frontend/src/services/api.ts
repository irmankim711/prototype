import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Report Types
export interface Report {
  id: string;
  title: string;
  description?: string;
  status: 'draft' | 'processing' | 'completed' | 'failed';
  createdAt: string;
  updatedAt: string;
  templateId: string;
  outputUrl?: string;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description?: string;
  schema: any;
  isActive: boolean;
}

export interface ReportStats {
  totalReports: number;
  reportsThisMonth: number;
  activeTemplates: number;
  processingReports: number;
}

// API Functions
export const fetchRecentReports = async (): Promise<Report[]> => {
  const { data } = await api.get('/reports/recent');
  return data;
};

export const fetchReportStats = async (): Promise<ReportStats> => {
  const { data } = await api.get('/reports/stats');
  return data;
};

export const fetchReportTemplates = async (): Promise<ReportTemplate[]> => {
  const { data } = await api.get('/reports/templates');
  return data;
};

export const createReport = async (reportData: Partial<Report>): Promise<Report> => {
  const { data } = await api.post('/reports', reportData);
  return data;
};

export const getReportStatus = async (taskId: string): Promise<{ status: string; result?: any }> => {
  const { data } = await api.get(`/reports/${taskId}`);
  return data;
};

export const updateReportTemplate = async (
  templateId: string,
  templateData: Partial<ReportTemplate>
): Promise<ReportTemplate> => {
  const { data } = await api.put(`/reports/templates/${templateId}`, templateData);
  return data;
};

export const analyzeData = async (data: any): Promise<any> => {
  const { data: result } = await api.post('/ai/analyze', data);
  return result;
};

// Error handler
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
