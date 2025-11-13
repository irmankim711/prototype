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
    // Use the proxy endpoint to avoid CORS issues with Firebase Storage
    // The backend will fetch from Firebase Storage and stream to frontend
    const downloadUrl = `${API_BASE_URL}/api/firebase-reports/${reportId}/download-proxy`;

    try {
      console.log(`📥 Downloading report ${reportId} via proxy endpoint`);

      // Check if token exists and is valid
      // Try both firebaseToken (new auth) and accessToken (legacy auth)
      const firebaseToken = localStorage.getItem("firebaseToken");
      const accessToken = localStorage.getItem("accessToken");
      const token = firebaseToken || accessToken;

      if (!token) {
        throw new Error('Authentication required. Please log in again.');
      }

      // Check if token is expired
      try {
        const decoded = JSON.parse(atob(token.split(".")[1]));
        const currentTime = Math.floor(Date.now() / 1000);
        if (decoded.exp && decoded.exp <= currentTime) {
          console.warn("⚠️ Token expired, attempting to refresh...");
          // Dispatch event to trigger token refresh
          window.dispatchEvent(new CustomEvent('auth:token-refresh-needed'));
          throw new Error('Your session has expired. Please log in again.');
        }
      } catch (tokenCheckError) {
        console.error("Token validation error:", tokenCheckError);
      }

      const response = await axiosInstance.get(downloadUrl, {
        responseType: 'blob',
        headers: {
          'Accept': 'application/pdf, application/vnd.openxmlformats-officedocument.wordprocessingml.document, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/octet-stream'
        }
      });

      // Extract filename from Content-Disposition header
      const contentDisposition = response.headers['content-disposition'];
      let filename = `report-${reportId}.${fileType}`;

      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      // Create blob URL and trigger download
      const blob = new Blob([response.data], { type: response.headers['content-type'] });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();

      // Cleanup
      setTimeout(() => {
        window.URL.revokeObjectURL(url);
        document.body.removeChild(link);
      }, 100);

      console.log(`✅ Report ${reportId} downloaded successfully as ${filename}`);
      return blob;

    } catch (error: any) {
      console.error('Download error:', error);
      console.error('Download error response:', error.response?.data);

      // Provide more detailed error message
      if (error.response?.status === 401) {
        const errorData = error.response.data;
        const errorMessage = errorData?.error || 'Authentication failed';
        const errorCode = errorData?.code;

        if (errorCode === 'MISSING_AUTH_HEADER' || errorCode === 'INVALID_TOKEN') {
          throw new Error('Your session has expired. Please log out and log in again to continue.');
        }
        throw new Error(`Authentication error: ${errorMessage}`);
      } else if (error.response?.status === 404) {
        throw new Error('Report not found or has been deleted');
      } else if (error.response?.status === 403) {
        throw new Error('You do not have permission to download this report');
      } else if (error.response?.status === 400) {
        throw new Error('Report is not ready for download yet');
      } else {
        throw new Error(`Download failed: ${error.response?.data?.error || error.message || 'Unknown error'}`);
      }
    }
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

