import axiosInstance from "./axiosInstance";

export interface GoogleForm {
  id: string;
  title: string;
  description: string;
  publishedUrl: string;
  responseCount: number;
  createdTime: string;
  lastModifiedTime: string;
}

export interface GoogleFormResponse {
  responseId: string;
  createTime: string;
  lastSubmittedTime: string;
  answers: Record<string, any>;
}

export interface GoogleFormAnalytics {
  totalResponses: number;
  responseRate: number;
  averageCompletionTime: number;
  questionAnalytics: Array<{
    questionId: string;
    title: string;
    type: string;
    responseCount: number;
    analytics: any;
  }>;
}

class GoogleFormsService {
  async initiateAuth(): Promise<{ auth_url: string; message: string }> {
    try {
      console.log("🔗 Making request to:", "/google-forms/auth");
      const response = await axiosInstance.get("/google-forms/auth");
      console.log("✅ Google Forms auth response:", response.data);
      return response.data;
    } catch (error: any) {
      console.error("❌ Google Forms auth error:", {
        message: error.message,
        status: error.response?.status,
        data: error.response?.data,
        url: error.config?.url,
        baseURL: error.config?.baseURL,
      });
      throw error;
    }
  }

  async handleCallback(
    code: string
  ): Promise<{ message: string; status: string }> {
    const response = await axiosInstance.get(
      `/google-forms/callback?code=${code}`
    );
    return response.data;
  }

  async getUserForms(): Promise<{ forms: GoogleForm[]; total: number }> {
    const response = await axiosInstance.get("/google-forms/forms");
    return response.data;
  }

  async getFormResponses(formId: string): Promise<{
    form_id: string;
    responses: GoogleFormResponse[];
    total: number;
  }> {
    const response = await axiosInstance.get(
      `/google-forms/${formId}/responses`
    );
    return response.data;
  }

  async getFormAnalytics(formId: string): Promise<{
    form_id: string;
    analytics: GoogleFormAnalytics;
  }> {
    const response = await axiosInstance.get(
      `/google-forms/${formId}/analytics`
    );
    return response.data;
  }

  async generateReport(data: {
    google_form_id: string;
    report_type: "summary" | "detailed" | "analytics" | "export";
    date_range?: "last_7_days" | "last_30_days" | "last_90_days" | "all_time";
    form_source: "google_form";
  }): Promise<{ message: string; report_id: number; status: string }> {
    const response = await axiosInstance.post("/reports", data);
    return response.data;
  }
}

export const googleFormsService = new GoogleFormsService();
export default googleFormsService;
