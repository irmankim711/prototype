/**
 * Production API Service - Frontend
 * Connects to production backend endpoints (no mock data)
 */

import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

// Create axios instance with production configuration
const productionApi = axios.create({
  baseURL: `${API_BASE_URL}/api/production`,
  timeout: 30000,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

// Request interceptor to add auth token
productionApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
productionApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

interface GoogleForm {
  id: string;
  title: string;
  description: string;
  published_url: string;
  response_count: number;
  question_count: number;
  created_time: string;
  modified_time: string;
  type: "google_form";
  status: string;
}

interface FormResponse {
  response_id: string;
  create_time: string;
  last_submitted_time: string;
  answers: Record<string, any>;
}

interface AIAnalysis {
  status: string;
  ai_powered: boolean;
  analysis: any;
  response_count: number;
  timestamp: string;
  model_used?: string;
}

interface ReportResult {
  success: boolean;
  report_id?: number;
  form_info: any;
  response_count: number;
  template_validation: any;
  analysis: any;
  generated_at: string;
}

interface Template {
  id: string;
  name: string;
  description: string;
  placeholders: string[];
  required_sections: string[];
  optional_sections: string[];
}

export class ProductionAPIService {
  /**
   * Health check for production services
   */
  static async healthCheck(): Promise<any> {
    try {
      const response = await productionApi.get("/health");
      return response.data;
    } catch (error) {
      console.error("Health check failed:", error);
      throw error;
    }
  }

  /**
   * Google Forms Integration - Production Methods
   */

  // Get real Google OAuth authorization URL
  static async getGoogleAuthURL(): Promise<{
    success: boolean;
    authorization_url: string;
    user_id: string;
  }> {
    try {
      const response = await productionApi.post("/google-forms/auth-url");
      return response.data;
    } catch (error) {
      console.error("Failed to get Google auth URL:", error);
      throw error;
    }
  }

  // Handle Google OAuth callback
  static async handleGoogleCallback(
    code: string,
    state: string
  ): Promise<{ success: boolean; message: string }> {
    try {
      const response = await productionApi.post("/google-forms/callback", {
        code,
        state,
      });
      return response.data;
    } catch (error) {
      console.error("Google OAuth callback failed:", error);
      throw error;
    }
  }

  // Get real user Google Forms
  static async getUserGoogleForms(
    pageSize: number = 50
  ): Promise<{ success: boolean; forms: GoogleForm[]; total_count: number }> {
    try {
      const response = await productionApi.get("/google-forms/forms", {
        params: { page_size: pageSize },
      });
      return response.data;
    } catch (error) {
      console.error("Failed to fetch Google Forms:", error);
      throw error;
    }
  }

  // Get real form responses
  static async getFormResponses(
    formId: string,
    limit: number = 100,
    includeAnalysis: boolean = false
  ): Promise<{
    success: boolean;
    form_info: any;
    responses: FormResponse[];
    total_count: number;
    analysis?: any;
  }> {
    try {
      const response = await productionApi.get(
        `/google-forms/${formId}/responses`,
        {
          params: { limit, include_analysis: includeAnalysis },
        }
      );
      return response.data;
    } catch (error) {
      console.error("Failed to fetch form responses:", error);
      throw error;
    }
  }

  /**
   * AI Analysis - Production Methods
   */

  // Analyze data with real AI or intelligent fallback
  static async analyzeDataWithAI(
    formTitle: string,
    formData: any
  ): Promise<AIAnalysis> {
    try {
      const response = await productionApi.post("/ai/analyze", {
        form_title: formTitle,
        form_data: formData,
      });
      return response.data;
    } catch (error) {
      console.error("AI analysis failed:", error);
      throw error;
    }
  }

  /**
   * Report Generation - Production Methods
   */

  // Generate report with real data
  static async generateReport(
    formId: string,
    template: string = "Temp1.docx",
    config: any = {}
  ): Promise<ReportResult> {
    try {
      const response = await productionApi.post("/reports/generate", {
        form_id: formId,
        template,
        config,
      });
      return response.data;
    } catch (error) {
      console.error("Report generation failed:", error);
      throw error;
    }
  }

  // Get user reports (no mock data)
  static async getUserReports(
    page: number = 1,
    perPage: number = 10,
    status?: string
  ): Promise<{
    success: boolean;
    reports: any[];
    pagination: any;
  }> {
    try {
      const params: any = { page, per_page: perPage };
      if (status) params.status = status;

      const response = await productionApi.get("/reports", { params });
      return response.data;
    } catch (error) {
      console.error("Failed to fetch reports:", error);
      throw error;
    }
  }

  // Get detailed report information
  static async getReportDetails(
    reportId: number
  ): Promise<{ success: boolean; report: any }> {
    try {
      const response = await productionApi.get(`/reports/${reportId}`);
      return response.data;
    } catch (error) {
      console.error("Failed to fetch report details:", error);
      throw error;
    }
  }

  /**
   * Template Management - Production Methods
   */

  // Get available templates (no mock data)
  static async getAvailableTemplates(): Promise<{
    success: boolean;
    templates: Template[];
    total_count: number;
  }> {
    try {
      const response = await productionApi.get("/templates");
      return response.data;
    } catch (error) {
      console.error("Failed to fetch templates:", error);
      throw error;
    }
  }

  // Validate template data against requirements
  static async validateTemplateData(
    templateId: string,
    formData: any
  ): Promise<{
    success: boolean;
    validation: any;
    completeness: number;
  }> {
    try {
      const response = await productionApi.post(
        `/templates/${templateId}/validate`,
        {
          form_data: formData,
        }
      );
      return response.data;
    } catch (error) {
      console.error("Template validation failed:", error);
      throw error;
    }
  }

  /**
   * Analytics and Dashboard - Production Methods
   */

  // Get dashboard analytics with real data
  static async getDashboardAnalytics(): Promise<{
    success: boolean;
    analytics: any;
  }> {
    try {
      const response = await productionApi.get("/analytics/dashboard");
      return response.data;
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
      throw error;
    }
  }

  /**
   * Utility Methods
   */

  // Check if services are production-ready
  static async checkProductionStatus(): Promise<{
    google_forms: boolean;
    ai_analysis: boolean;
    mock_disabled: boolean;
    environment: string;
  }> {
    try {
      const health = await this.healthCheck();
      return health.features;
    } catch (error) {
      console.error("Production status check failed:", error);
      return {
        google_forms: false,
        ai_analysis: false,
        mock_disabled: false,
        environment: "unknown",
      };
    }
  }

  // Comprehensive workflow: From Google Form to Generated Report
  static async completeWorkflow(
    formId: string,
    templateId: string = "Temp1.docx"
  ): Promise<{
    success: boolean;
    steps: {
      form_data: any;
      ai_analysis: any;
      report_generation: any;
      validation: any;
    };
    report_id?: number;
  }> {
    try {
      console.log("🚀 Starting complete production workflow");

      // Step 1: Get real form responses
      console.log("📊 Fetching real form responses...");
      const formData = await this.getFormResponses(formId, 100, true);

      if (!formData.success) {
        throw new Error("Failed to fetch form data");
      }

      // Step 2: AI analysis of real data
      console.log("🧠 Analyzing data with AI...");
      const aiAnalysis = await this.analyzeDataWithAI(
        formData.form_info.title,
        formData
      );

      // Step 3: Validate template with real data
      console.log("📋 Validating template with real data...");
      const validation = await this.validateTemplateData(templateId, formData);

      // Step 4: Generate report with real data
      console.log("📄 Generating report with real data...");
      const reportResult = await this.generateReport(formId, templateId, {
        include_ai_analysis: true,
        include_charts: true,
      });

      console.log("✅ Production workflow completed successfully");

      return {
        success: true,
        steps: {
          form_data: formData,
          ai_analysis: aiAnalysis,
          report_generation: reportResult,
          validation: validation,
        },
        report_id: reportResult.report_id,
      };
    } catch (error) {
      console.error("❌ Production workflow failed:", error);
      throw error;
    }
  }
}

export default ProductionAPIService;
