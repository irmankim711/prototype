import axios from "axios";
import type {
  Report,
  ReportGenerationRequest,
  ReportUpdateRequest,
  FormSubmission,
  FormAnalytics,
} from "../types/reports";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000/api";

class ReportService {
  private baseURL: string;

  constructor() {
    this.baseURL = `${API_BASE_URL}/public-forms`;
  }

  async getAllReports(): Promise<Report[]> {
    const response = await axios.get(`${this.baseURL}/reports`);
    return response.data;
  }

  async getFormReports(formId: string): Promise<Report[]> {
    const response = await axios.get(
      `${this.baseURL}/reports?form_id=${formId}`
    );
    return response.data;
  }

  async getReport(reportId: string): Promise<Report> {
    const response = await axios.get(`${this.baseURL}/reports/${reportId}`);
    return response.data;
  }

  async generateReport(request: ReportGenerationRequest): Promise<Report> {
    const response = await axios.post(
      `${this.baseURL}/generate-report`,
      request
    );
    return response.data;
  }

  async updateReport(
    reportId: string,
    update: ReportUpdateRequest
  ): Promise<Report> {
    const response = await axios.put(
      `${this.baseURL}/reports/${reportId}`,
      update
    );
    return response.data;
  }

  async downloadReport(reportId: string): Promise<Blob> {
    const response = await axios.get(
      `${this.baseURL}/reports/${reportId}/download`,
      {
        responseType: "blob",
      }
    );
    return response.data;
  }

  async emailReport(reportId: string, emails: string[]): Promise<void> {
    await axios.post(`${this.baseURL}/reports/${reportId}/email`, {
      emails,
    });
  }

  async deleteReport(reportId: string): Promise<void> {
    await axios.delete(`${this.baseURL}/reports/${reportId}`);
  }

  async getFormSubmissions(formId: string): Promise<FormSubmission[]> {
    const response = await axios.get(
      `${this.baseURL}/forms/${formId}/submissions`
    );
    return response.data;
  }

  async getFormAnalytics(formId: string): Promise<FormAnalytics> {
    const response = await axios.get(
      `${this.baseURL}/forms/${formId}/analytics`
    );
    return response.data;
  }

  async submitPublicForm(
    formData: Record<string, unknown>
  ): Promise<{ success: boolean; submissionId: string }> {
    const response = await axios.post(`${this.baseURL}/submit`, formData);
    return response.data;
  }

  async batchSubmitForms(
    submissions: Array<{ formId: string; data: Record<string, unknown> }>
  ): Promise<{
    success: boolean;
    submissionIds: string[];
  }> {
    const response = await axios.post(`${this.baseURL}/batch-submit`, {
      submissions,
    });
    return response.data;
  }

  // Real-time updates using EventSource (Server-Sent Events)
  createReportStatusStream(reportId: string): EventSource {
    return new EventSource(`${this.baseURL}/reports/${reportId}/status-stream`);
  }

  createFormSubmissionStream(formId: string): EventSource {
    return new EventSource(`${this.baseURL}/forms/${formId}/submission-stream`);
  }
}

export const reportService = new ReportService();
