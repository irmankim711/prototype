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

// Check if we're in the deployed environment without a backend
const isDeployed = window.location.hostname !== 'localhost';

// Mock data for deployed environment
const mockReports: Report[] = [
  {
    id: '1',
    title: 'Q1 Financial Report',
    status: 'completed',
    createdAt: '2025-01-15T10:30:00Z',
    updatedAt: '2025-01-15T11:30:00Z',
    templateId: '1',
    outputUrl: '#'
  },
  {
    id: '2',
    title: 'Customer Satisfaction Survey',
    status: 'processing',
    createdAt: '2025-04-10T09:15:00Z',
    updatedAt: '2025-04-10T09:15:00Z',
    templateId: '2'
  },
  {
    id: '3',
    title: 'Employee Performance Review',
    status: 'completed',
    createdAt: '2025-03-22T14:45:00Z',
    updatedAt: '2025-03-22T16:30:00Z',
    templateId: '3',
    outputUrl: '#'
  }
];

const mockStats: ReportStats = {
  totalReports: 42,
  reportsThisMonth: 8,
  activeTemplates: 6,
  processingReports: 3
};

const mockTemplates: ReportTemplate[] = [
  {
    id: '1',
    name: 'Financial Report',
    description: 'Quarterly financial performance report',
    schema: {
      fields: [
        { name: 'revenue', label: 'Revenue', type: 'number', required: true },
        { name: 'expenses', label: 'Expenses', type: 'number', required: true },
        { name: 'quarter', label: 'Quarter', type: 'text', required: true }
      ]
    },
    isActive: true
  },
  {
    id: '2',
    name: 'Survey Results',
    description: 'Customer satisfaction survey results',
    schema: {
      fields: [
        { name: 'respondents', label: 'Number of Respondents', type: 'number', required: true },
        { name: 'averageScore', label: 'Average Score', type: 'number', required: true },
        { name: 'period', label: 'Time Period', type: 'text', required: true }
      ]
    },
    isActive: true
  },
  {
    id: '3',
    name: 'Employee Review',
    description: 'Annual employee performance review',
    schema: {
      fields: [
        { name: 'employeeName', label: 'Employee Name', type: 'text', required: true },
        { name: 'department', label: 'Department', type: 'text', required: true },
        { name: 'rating', label: 'Performance Rating', type: 'number', required: true },
        { name: 'comments', label: 'Manager Comments', type: 'text', required: false }
      ]
    },
    isActive: true
  }
];

// API Functions
export const fetchRecentReports = async (): Promise<Report[]> => {
  if (isDeployed) {
    return new Promise(resolve => setTimeout(() => resolve(mockReports), 500));
  }
  
  const { data } = await api.get('/reports/recent');
  return data;
};

export const fetchReportStats = async (): Promise<ReportStats> => {
  if (isDeployed) {
    return new Promise(resolve => setTimeout(() => resolve(mockStats), 500));
  }
  
  const { data } = await api.get('/reports/stats');
  return data;
};

export const fetchReportTemplates = async (): Promise<ReportTemplate[]> => {
  if (isDeployed) {
    return new Promise(resolve => setTimeout(() => resolve(mockTemplates), 500));
  }
  
  const { data } = await api.get('/reports/templates');
  return data;
};

export const createReport = async (reportData: Partial<Report>): Promise<Report> => {
  if (isDeployed) {
    const newReport: Report = {
      id: Math.floor(Math.random() * 10000).toString(),
      title: reportData.title || 'New Report',
      status: 'processing',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      templateId: reportData.templateId || '1',
      ...reportData
    };
    return new Promise(resolve => setTimeout(() => resolve(newReport), 800));
  }
  
  const { data } = await api.post('/reports', reportData);
  return data;
};

export const getReportStatus = async (taskId: string): Promise<{ status: string; result?: any }> => {
  if (isDeployed) {
    return new Promise(resolve => 
      setTimeout(() => resolve({ status: 'completed', result: { id: taskId } }), 700)
    );
  }
  
  const { data } = await api.get(`/reports/${taskId}`);
  return data;
};

export const updateReportTemplate = async (
  templateId: string,
  templateData: Partial<ReportTemplate>
): Promise<ReportTemplate> => {
  if (isDeployed) {
    const template = mockTemplates.find(t => t.id === templateId);
    if (!template) {
      throw new Error('Template not found');
    }
    
    const updatedTemplate = { ...template, ...templateData };
    return new Promise(resolve => setTimeout(() => resolve(updatedTemplate), 600));
  }
  
  const { data } = await api.put(`/reports/templates/${templateId}`, templateData);
  return data;
};

export const analyzeData = async (data: any): Promise<any> => {
  if (isDeployed) {
    return new Promise(resolve => 
      setTimeout(() => resolve({
        summary: 'Based on the provided data, this analysis shows positive trends in key metrics.',
        insights: [
          'Revenue is increasing quarter over quarter',
          'Customer satisfaction has improved by 12%',
          'Operational costs have decreased',
        ],
        suggestions: 'Consider expanding marketing efforts in the regions showing the highest growth.'
      }), 1200)
    );
  }
  
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
