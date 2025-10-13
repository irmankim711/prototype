import axiosInstance from "./axiosInstance";

export interface GoogleForm {
  formId: string;
  info: {
    title: string;
    description: string;
    documentTitle?: string;
    linkedSheetId?: string;
  };
  responderUri?: string;
  settings?: any;
}

export interface GoogleFormResponse {
  responseId: string;
  createTime: string;
  lastSubmittedTime: string;
  answers: Record<string, any>;
}

export interface FormAnalysis {
  response_patterns: Record<string, number>;
  completion_stats: {
    completion_rate: number;
    complete_responses: number;
    partial_responses: number;
  };
  quality_metrics: {
    average_completion_time: number;
    blank_responses: number;
  };
  temporal_analysis: {
    peak_hour: string;
    peak_day: string;
  };
  question_insights: Array<{
    question_id: string;
    title: string;
    type: string;
    insight: string;
  }>;
}

export interface AuthStatus {
  is_authorized: boolean;
  has_valid_token: boolean;
  last_sync?: string;
  forms_count: number;
}

export interface ReportConfig {
  format: "pdf" | "docx";
  include_charts: boolean;
  include_ai_analysis: boolean;
  title?: string;
  description?: string;
  chart_types?: string[];
}

export interface ReportResult {
  success: boolean;
  report_id?: number;
  download_url?: string;
  summary?: {
    total_responses: number;
    analysis_points: number;
    charts_generated: number;
    ai_insights_count: number;
  };
  error?: string;
}

class GoogleFormsService {
  // Check authorization status
  async getAuthorizationStatus(): Promise<AuthStatus> {
    try {
      const response = await axiosInstance.get("/google-forms/status");
      return response.data;
    } catch (error: any) {
      console.error("Error checking authorization status:", error);
      throw error;
    }
  }

  // Initiate Google OAuth authorization
  async initiateAuth(): Promise<{
    success: boolean;
    authorization_url: string;
    state: string;
    error?: string;
  }> {
    try {
      console.log("🔗 Initiating Google Forms authorization");
      const response = await axiosInstance.post(
        "/google-forms/oauth/authorize"
      );
      console.log("✅ Authorization response:", response.data);
      return response.data;
    } catch (error: any) {
      console.error("❌ Authorization error:", error);
      throw error;
    }
  }

  // Handle OAuth callback
  async handleCallback(
    code: string,
    state?: string
  ): Promise<{
    success: boolean;
    message: string;
    error?: string;
  }> {
    try {
      const response = await axiosInstance.post(
        "/google-forms/oauth/callback",
        {
          code,
          state,
        }
      );
      return response.data;
    } catch (error: any) {
      console.error("OAuth callback error:", error);
      throw error;
    }
  }

  // Get user's Google Forms
  async getUserForms(pageSize?: number): Promise<{
    success: boolean;
    forms: GoogleForm[];
    total_count: number;
    error?: string;
  }> {
    try {
      const params = pageSize ? { page_size: pageSize } : {};
      const response = await axiosInstance.get("/google-forms/forms", {
        params,
      });
      return response.data;
    } catch (error: any) {
      console.error("Error fetching forms:", error);
      throw error;
    }
  }

  // Get form information
  async getFormInfo(formId: string): Promise<{
    success: boolean;
    form_info: any;
    error?: string;
  }> {
    try {
      const response = await axiosInstance.get(
        `/google-forms/forms/${formId}/info`
      );
      return response.data;
    } catch (error: any) {
      console.error("Error fetching form info:", error);
      throw error;
    }
  }

  // Get form responses
  async getFormResponses(
    formId: string,
    options?: {
      limit?: number;
      include_analysis?: boolean;
    }
  ): Promise<{
    success: boolean;
    responses: GoogleFormResponse[];
    form_info: any;
    analysis?: FormAnalysis;
    total_count: number;
    error?: string;
  }> {
    try {
      const params = {
        limit: options?.limit || 100,
        include_analysis: options?.include_analysis || false,
      };

      const response = await axiosInstance.get(
        `/google-forms/forms/${formId}/responses`,
        { params }
      );
      return response.data;
    } catch (error: any) {
      console.error("Error fetching responses:", error);
      throw error;
    }
  }

  // Preview report data
  async previewReportData(formId: string): Promise<{
    success: boolean;
    preview: {
      form_info: any;
      response_count: number;
      analysis_summary: FormAnalysis;
      insights_preview: any[];
      completion_stats: any;
      temporal_analysis: any;
      available_charts: string[];
    };
    error?: string;
  }> {
    try {
      const response = await axiosInstance.post(
        `/google-forms/forms/${formId}/preview-report`
      );
      return response.data;
    } catch (error: any) {
      console.error("Error previewing report:", error);
      throw error;
    }
  }

  // Generate automated report
  async generateAutomatedReport(
    formId: string,
    config: ReportConfig
  ): Promise<ReportResult> {
    try {
      console.log(`🔄 Generating report for form ${formId}`, config);
      const response = await axiosInstance.post(
        `/google-forms/forms/${formId}/generate-report`,
        config
      );
      console.log("✅ Report generated:", response.data);
      return response.data;
    } catch (error: any) {
      console.error("❌ Report generation error:", error);
      throw error;
    }
  }

  // Download report
  async downloadReport(downloadUrl: string): Promise<Blob> {
    try {
      const response = await axiosInstance.get(downloadUrl, {
        responseType: "blob",
      });
      return response.data;
    } catch (error: any) {
      console.error("Error downloading report:", error);
      throw error;
    }
  }

  // Batch generate reports for multiple forms
  async generateBatchReports(
    formIds: string[],
    config: ReportConfig
  ): Promise<{
    success: boolean;
    results: Array<{
      formId: string;
      success: boolean;
      report_id?: number;
      download_url?: string;
      error?: string;
    }>;
  }> {
    try {
      const results = [];

      for (const formId of formIds) {
        try {
          const result = await this.generateAutomatedReport(formId, config);
          results.push({
            formId,
            success: result.success,
            report_id: result.report_id,
            download_url: result.download_url,
          });
        } catch (error: any) {
          results.push({
            formId,
            success: false,
            error: error.message || "Failed to generate report",
          });
        }
      }

      return {
        success: true,
        results,
      };
    } catch (error: any) {
      console.error("Batch report generation error:", error);
      throw error;
    }
  }

  // Legacy method for backward compatibility
  async getFormAnalytics(formId: string): Promise<{
    form_id: string;
    analytics: any;
  }> {
    try {
      const response = await this.getFormResponses(formId, {
        include_analysis: true,
      });
      return {
        form_id: formId,
        analytics: response.analysis,
      };
    } catch (error) {
      throw error;
    }
  }

  // Legacy report generation for backward compatibility
  async generateReport(data: {
    google_form_id: string;
    report_type: "summary" | "detailed" | "analytics" | "export";
    date_range?: "last_7_days" | "last_30_days" | "last_90_days" | "all_time";
    form_source: "google_form";
  }): Promise<{ message: string; report_id: number; status: string }> {
    try {
      const config: ReportConfig = {
        format: "pdf",
        include_charts: true,
        include_ai_analysis: data.report_type === "analytics",
        title: `${data.report_type} Report`,
      };

      const result = await this.generateAutomatedReport(
        data.google_form_id,
        config
      );

      return {
        message: result.success
          ? "Report generated successfully"
          : result.error || "Failed to generate report",
        report_id: result.report_id || 0,
        status: result.success ? "completed" : "failed",
      };
    } catch (error: any) {
      throw error;
    }
  }
}

export const googleFormsService = new GoogleFormsService();
export default googleFormsService;
