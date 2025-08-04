import axiosInstance from './axiosInstance';

export interface AutomatedReport {
  id: number;
  title: string;
  description: string;
  form_id: number;
  form_title: string;
  report_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  output_url?: string;
  task_id?: string;
  analysis?: any;
  submissions_count?: number;
  date_range?: string;
}

export interface GenerateReportRequest {
  form_id: number;
  report_type: 'summary' | 'detailed' | 'trends';
  date_range: 'last_7_days' | 'last_30_days' | 'last_90_days';
}

export interface ReportStatus {
  status: 'pending' | 'processing' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

export const automatedReportsAPI = {
  // Get all automated reports
  getReports: async (params?: { page?: number; per_page?: number }) => {
    const response = await axiosInstance.get('/reports/automated', { params });
    return response.data;
  },

  // Get a specific report
  getReport: async (reportId: number) => {
    const response = await axiosInstance.get(`/reports/automated/${reportId}`);
    return response.data;
  },

  // Generate a new automated report
  generateReport: async (data: GenerateReportRequest) => {
    const response = await axiosInstance.post('/reports/automated/generate', data);
    return response.data;
  },

  // Check report generation status
  getReportStatus: async (taskId: string) => {
    const response = await axiosInstance.get(`/reports/automated/status/${taskId}`);
    return response.data;
  },

  // Download report file
  downloadReport: async (reportId: number) => {
    const response = await axiosInstance.get(`/reports/automated/${reportId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },

  // Get form submissions for analysis
  getFormSubmissions: async (formId: number, params?: { page?: number; per_page?: number }) => {
    const response = await axiosInstance.get(`/forms/${formId}/submissions`, { params });
    return response.data;
  },

  // Submit form data from external sources
  submitFormData: async (data: {
    form_id: number;
    data: any;
    submitter?: {
      email?: string;
      name?: string;
    };
    source?: string;
  }) => {
    const response = await axiosInstance.post('/forms/submit', data);
    return response.data;
  },

  // Update form automation settings
  updateFormSettings: async (formId: number, settings: {
    auto_generate_reports?: boolean;
    report_schedule?: 'daily' | 'weekly' | 'monthly';
    report_type?: string;
  }) => {
    const response = await axiosInstance.put(`/forms/${formId}/settings`, settings);
    return response.data;
  },

  // Get report templates
  getReportTemplates: async () => {
    const response = await axiosInstance.get('/reports/templates');
    return response.data;
  },

  // Create custom report template
  createReportTemplate: async (template: {
    name: string;
    description?: string;
    schema: any;
  }) => {
    const response = await axiosInstance.post('/reports/templates', template);
    return response.data;
  },

  // Get report analytics
  getReportAnalytics: async (params?: {
    date_range?: string;
    report_type?: string;
  }) => {
    const response = await axiosInstance.get('/reports/analytics', { params });
    return response.data;
  },

  // Export report data
  exportReportData: async (reportId: number, format: 'csv' | 'excel' | 'json') => {
    const response = await axiosInstance.get(`/reports/automated/${reportId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },

  // Schedule recurring reports
  scheduleRecurringReport: async (data: {
    form_id: number;
    schedule: 'daily' | 'weekly' | 'monthly';
    report_type: string;
    recipients?: string[];
  }) => {
    const response = await axiosInstance.post('/reports/automated/schedule', data);
    return response.data;
  },

  // Cancel scheduled report
  cancelScheduledReport: async (scheduleId: number) => {
    const response = await axiosInstance.delete(`/reports/automated/schedule/${scheduleId}`);
    return response.data;
  },

  // Get scheduled reports
  getScheduledReports: async () => {
    const response = await axiosInstance.get('/reports/automated/schedule');
    return response.data;
  },

  // Send report via email
  sendReportEmail: async (reportId: number, data: {
    recipients: string[];
    subject?: string;
    message?: string;
  }) => {
    const response = await axiosInstance.post(`/reports/automated/${reportId}/send-email`, data);
    return response.data;
  },

  // Get report generation history
  getReportHistory: async (params?: {
    form_id?: number;
    date_range?: string;
    status?: string;
    page?: number;
    per_page?: number;
  }) => {
    const response = await axiosInstance.get('/reports/automated/history', { params });
    return response.data;
  },

  // Delete report
  deleteReport: async (reportId: number) => {
    const response = await axiosInstance.delete(`/reports/automated/${reportId}`);
    return response.data;
  },

  // Duplicate report
  duplicateReport: async (reportId: number, data?: {
    title?: string;
    description?: string;
  }) => {
    const response = await axiosInstance.post(`/reports/automated/${reportId}/duplicate`, data);
    return response.data;
  },

  // Get report insights
  getReportInsights: async (reportId: number) => {
    const response = await axiosInstance.get(`/reports/automated/${reportId}/insights`);
    return response.data;
  },

  // Update report
  updateReport: async (reportId: number, data: {
    title?: string;
    description?: string;
    data?: any;
  }) => {
    const response = await axiosInstance.put(`/reports/automated/${reportId}`, data);
    return response.data;
  },

  // Regenerate report
  regenerateReport: async (reportId: number, data?: {
    report_type?: string;
    date_range?: string;
  }) => {
    const response = await axiosInstance.post(`/reports/automated/${reportId}/regenerate`, data);
    return response.data;
  },

  // Get report comparison
  compareReports: async (reportIds: number[]) => {
    const response = await axiosInstance.post('/reports/automated/compare', { report_ids: reportIds });
    return response.data;
  },

  // Get report trends
  getReportTrends: async (params?: {
    form_id?: number;
    date_range?: string;
    metric?: string;
  }) => {
    const response = await axiosInstance.get('/reports/automated/trends', { params });
    return response.data;
  },

  // Export report template
  exportReportTemplate: async (templateId: number, format: 'json' | 'xml') => {
    const response = await axiosInstance.get(`/reports/templates/${templateId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  },

  // Import report template
  importReportTemplate: async (templateData: any) => {
    const response = await axiosInstance.post('/reports/templates/import', templateData);
    return response.data;
  },

  // Validate report data
  validateReportData: async (data: any) => {
    const response = await axiosInstance.post('/reports/automated/validate', data);
    return response.data;
  },

  // Get report generation queue
  getReportQueue: async () => {
    const response = await axiosInstance.get('/reports/automated/queue');
    return response.data;
  },

  // Cancel report generation
  cancelReportGeneration: async (taskId: string) => {
    const response = await axiosInstance.post(`/reports/automated/cancel/${taskId}`);
    return response.data;
  },

  // Get report generation statistics
  getReportStats: async () => {
    const response = await axiosInstance.get('/reports/automated/stats');
    return response.data;
  },

  // Test report generation
  testReportGeneration: async (data: GenerateReportRequest) => {
    const response = await axiosInstance.post('/reports/automated/test', data);
    return response.data;
  },

  // Get report preview
  getReportPreview: async (reportId: number) => {
    const response = await axiosInstance.get(`/reports/automated/${reportId}/preview`);
    return response.data;
  },

  // Share report
  shareReport: async (reportId: number, data: {
    share_type: 'public' | 'private';
    expires_at?: string;
    password?: string;
  }) => {
    const response = await axiosInstance.post(`/reports/automated/${reportId}/share`, data);
    return response.data;
  },

  // Get shared report
  getSharedReport: async (shareToken: string) => {
    const response = await axiosInstance.get(`/reports/automated/shared/${shareToken}`);
    return response.data;
  },
}; 