import axiosInstance from "./axiosInstance";
import type {
  Report,
  ReportGenerationRequest,
  ReportUpdateRequest,
  FormSubmission,
  FormAnalytics,
} from "../types/reports";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000";

class ReportService {
  private baseURL: string;

  constructor() {
    // Fix: Use the correct API reports endpoint
    this.baseURL = `${API_BASE_URL}/api/reports`;
  }

  async getAllReports(): Promise<Report[]> {
    const response = await axiosInstance.get(`${this.baseURL}`);
    return response.data.reports || response.data;
  }

  async getFormReports(formId: string): Promise<Report[]> {
    const response = await axiosInstance.get(
      `${this.baseURL}/user/${formId}`
    );
    return response.data.reports || response.data;
  }

  async getReport(reportId: string): Promise<Report> {
    const response = await axiosInstance.get(`${this.baseURL}/${reportId}`);
    return response.data.report || response.data;
  }

  async generateReport(request: ReportGenerationRequest): Promise<Report> {
    const response = await axiosInstance.post(
      `${this.baseURL}/generate`,
      request
    );
    return response.data;
  }

  async generateLatexReport(request: {
    title: string;
    latex_file_path: string;
    description?: string;
    config: any;
  }): Promise<Report> {
    const response = await axiosInstance.post(
      `${this.baseURL}/generate/latex`,
      request
    );
    return response.data;
  }

  async getReportStatus(reportId: string): Promise<Report> {
    const response = await axiosInstance.get(`${this.baseURL}/${reportId}/status`);
    return response.data.report || response.data;
  }

  async previewReport(reportId: string): Promise<any> {
    const response = await axiosInstance.get(`${this.baseURL}/${reportId}/preview`);
    return response.data.preview || response.data;
  }

  async convertLatexReport(reportId: string, latexFilePath: string): Promise<any> {
    const response = await axiosInstance.post(`${this.baseURL}/${reportId}/convert/latex`, {
      latex_file_path: latexFilePath
    });
    return response.data;
  }

  async updateReport(
    reportId: string,
    update: ReportUpdateRequest
  ): Promise<Report> {
    const response = await axiosInstance.put(
      `${this.baseURL}/${reportId}/edit`,
      update
    );
    return response.data;
  }

  async downloadReport(reportId: string, fileType: 'pdf' | 'docx' | 'excel' = 'pdf'): Promise<Blob> {
    const response = await axiosInstance.get(
      `${this.baseURL}/${reportId}/download/${fileType}`,
      {
        responseType: "blob",
      }
    );
    return response.data;
  }

  async emailReport(reportId: string, emails: string[]): Promise<void> {
    await axiosInstance.post(`${this.baseURL}/${reportId}/email`, {
      emails,
    });
  }

  async deleteReport(reportId: string): Promise<void> {
    await axiosInstance.delete(`${this.baseURL}/${reportId}`);
  }

  // Excel to DOCX conversion methods
  async convertExcelToDocx(file: File, options: {
    title?: string;
    template?: string;
  } = {}): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (options.title) formData.append('title', options.title);
    if (options.template) formData.append('template', options.template);

    const response = await axiosInstance.post(`${API_BASE_URL}/api/excel-to-docx/convert`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getDocxTemplates(): Promise<any> {
    const response = await axiosInstance.get(`${API_BASE_URL}/api/excel-to-docx/templates`);
    return response.data;
  }

  // Document preview methods
  async getDocumentPreview(reportId: string | number): Promise<any> {
    const response = await axiosInstance.get(`${API_BASE_URL}/api/excel-to-docx/${reportId}/preview`);
    return response.data;
  }

  async getPreviewContent(reportId: string | number): Promise<string> {
    const response = await axiosInstance.get(`${API_BASE_URL}/api/excel-to-docx/preview-content/${reportId}`, {
      responseType: 'text',
    });
    return response.data;
  }

  // Lifecycle management endpoints
  async getStorageUsage(): Promise<any> {
    const response = await axiosInstance.get(`${this.baseURL}/lifecycle/storage`);
    return response.data.storage_usage || response.data;
  }

  async cleanupReports(force: boolean = false): Promise<any> {
    const response = await axiosInstance.post(`${this.baseURL}/lifecycle/cleanup`, {
      force
    });
    return response.data.result || response.data;
  }

  async updateRetentionPolicy(retentionDays: number): Promise<any> {
    const response = await axiosInstance.put(`${this.baseURL}/lifecycle/retention`, {
      retention_days: retentionDays
    });
    return response.data;
  }

  async getFormSubmissions(formId: string): Promise<FormSubmission[]> {
    // Fix: Use the correct forms endpoint
    const response = await axiosInstance.get(
      `${API_BASE_URL}/api/forms/${formId}/submissions`
    );
    return response.data.submissions || response.data;
  }

  async getFormAnalytics(formId: string): Promise<FormAnalytics> {
    // Fix: Use the correct forms endpoint
    const response = await axiosInstance.get(
      `${API_BASE_URL}/api/forms/${formId}/analytics`
    );
    return response.data.analytics || response.data;
  }

  async submitPublicForm(
    formData: Record<string, unknown>
  ): Promise<{ success: boolean; submissionId: string }> {
    // Fix: Use the correct public forms endpoint
    const response = await axiosInstance.post(`${API_BASE_URL}/api/public/forms/submit`, formData);
    return response.data;
  }

  // Helper method to get download URL for a report
  getDownloadUrl(reportId: string, fileType: 'pdf' | 'docx' | 'excel' = 'pdf'): string {
    return `${this.baseURL}/${reportId}/download/${fileType}`;
  }

  // Helper method to get preview URL for a report
  getPreviewUrl(reportId: string): string {
    return `${this.baseURL}/${reportId}/preview`;
  }

  // File upload method for DOCX report generation
  async uploadFile(formData: FormData): Promise<{ file_path: string; success: boolean }> {
    const response = await axiosInstance.post(`${API_BASE_URL}/api/upload/file`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Convert existing DOCX to other formats
  async convertDocxReport(reportId: string, docxFilePath: string): Promise<any> {
    const response = await axiosInstance.post(`${this.baseURL}/${reportId}/convert/docx`, {
      docx_file_path: docxFilePath
    });
    return response.data;
  }
}

export const reportService = new ReportService();

