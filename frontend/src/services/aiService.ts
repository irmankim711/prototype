import axios from "axios";

// API Configuration
const API_BASE_URL = "http://localhost:5000";

const aiApi = axios.create({
  baseURL: `${API_BASE_URL}/api/mvp`,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
  timeout: 30000, // 30 seconds timeout for AI operations
});

// AI Response Types
export interface AIAnalysisResult {
  success: boolean;
  summary: string;
  insights: string[];
  patterns: string[];
  anomalies: string[];
  recommendations: string[];
  risks: string[];
  opportunities: string[];
  confidence_score: number;
  data_quality: "high" | "medium" | "low";
  analysis_type: string;
  ai_powered: boolean;
  fallback_reason?: string;
  timestamp: string;
  error?: string;
}

export interface AIReportSuggestion {
  key_metrics: Array<{
    metric: string;
    value: string;
    importance: "high" | "medium" | "low";
    description: string;
  }>;
  visualizations: Array<{
    type: string;
    data_fields: string[];
    purpose: string;
  }>;
  trends: string[];
  critical_areas: string[];
  executive_points: string[];
  detailed_sections: string[];
  next_steps: string[];
  report_quality_score: number;
}

export interface AIReportSuggestionsResult {
  success: boolean;
  suggestions: AIReportSuggestion;
  report_type: string;
  ai_powered: boolean;
  fallback_reason?: string;
  timestamp: string;
  error?: string;
}

export interface AIPlaceholder {
  name: string;
  description: string;
  example: string;
  required?: boolean;
  format?: string;
  context?: string;
  optional?: boolean;
  dynamic?: boolean;
}

export interface AIPlaceholdersResult {
  success: boolean;
  placeholders: {
    basic_placeholders: AIPlaceholder[];
    financial_metrics: AIPlaceholder[];
    operational_details: AIPlaceholder[];
    analytical_insights: AIPlaceholder[];
    industry_specific: AIPlaceholder[];
    compliance_regulatory: AIPlaceholder[];
  };
  context: string;
  industry: string;
  ai_powered: boolean;
  fallback_reason?: string;
  timestamp: string;
  error?: string;
}

export interface AIValidationIssue {
  type: string;
  field?: string;
  severity: "high" | "medium" | "low";
  description: string;
  suggestion?: string;
}

export interface AIValidationResult {
  success: boolean;
  validation: {
    overall_quality_score: number;
    completeness_score?: number;
    consistency_score?: number;
    accuracy_score?: number;
    validity_score?: number;
    issues_found: AIValidationIssue[];
    critical_issues: string[];
    warnings: string[];
    recommendations: string[];
    data_readiness: "ready" | "needs_attention" | "not_ready" | "unknown";
    improvement_suggestions: string[];
  };
  ai_powered: boolean;
  fallback_reason?: string;
  timestamp: string;
  error?: string;
}

export interface AIHealthStatus {
  success: boolean;
  status: "healthy" | "unhealthy";
  services: {
    openai: {
      configured: boolean;
      status: "ready" | "not_configured" | "error";
    };
    google_ai: {
      configured: boolean;
      status: "ready" | "not_configured" | "error";
    };
  };
  features_available: string[];
  error?: string;
}

// AI Service Class
export class AIService {
  /**
   * Check AI service health and availability
   */
  static async getHealthStatus(): Promise<AIHealthStatus> {
    try {
      const response = await aiApi.get("/ai/health");
      return response.data;
    } catch (error) {
      console.error("AI Health Check failed:", error);
      return {
        success: false,
        status: "unhealthy",
        services: {
          openai: { configured: false, status: "error" },
          google_ai: { configured: false, status: "error" },
        },
        features_available: [],
        error: error instanceof Error ? error.message : "Unknown error",
      };
    }
  }

  /**
   * Analyze data using AI
   */
  static async analyzeData(
    data: Record<string, any>,
    context: string = "general"
  ): Promise<AIAnalysisResult> {
    try {
      const response = await aiApi.post("/ai/analyze", {
        context,
        data,
      });
      return response.data;
    } catch (error) {
      console.error("AI Analysis failed:", error);
      throw new Error(
        error instanceof Error ? error.message : "Analysis failed"
      );
    }
  }

  /**
   * Get AI-powered report suggestions
   */
  static async getReportSuggestions(
    data: Record<string, any>,
    reportType: string = "general"
  ): Promise<AIReportSuggestionsResult> {
    try {
      const response = await aiApi.post("/ai/report-suggestions", {
        report_type: reportType,
        data,
      });
      return response.data;
    } catch (error) {
      console.error("AI Report Suggestions failed:", error);
      throw new Error(
        error instanceof Error ? error.message : "Report suggestions failed"
      );
    }
  }

  /**
   * Generate smart placeholders for templates
   */
  static async getSmartPlaceholders(
    context: string,
    industry: string = "general"
  ): Promise<AIPlaceholdersResult> {
    try {
      const response = await aiApi.post("/ai/smart-placeholders", {
        context,
        industry,
      });
      return response.data;
    } catch (error) {
      console.error("AI Placeholder generation failed:", error);
      throw new Error(
        error instanceof Error ? error.message : "Placeholder generation failed"
      );
    }
  }

  /**
   * Validate data quality using AI
   */
  static async validateDataQuality(
    data: Record<string, any>
  ): Promise<AIValidationResult> {
    try {
      const response = await aiApi.post("/ai/validate-data", {
        data,
      });
      return response.data;
    } catch (error) {
      console.error("AI Data Validation failed:", error);
      throw new Error(
        error instanceof Error ? error.message : "Data validation failed"
      );
    }
  }

  /**
   * Optimize template using AI
   */
  static async optimizeTemplate(
    templateContent: string,
    placeholders: string[],
    templateType: string = "general"
  ): Promise<any> {
    try {
      const response = await aiApi.post("/ai/optimize-template", {
        template_content: templateContent,
        placeholders,
        template_type: templateType,
      });
      return response.data;
    } catch (error) {
      console.error("AI Template Optimization failed:", error);
      throw new Error(
        error instanceof Error ? error.message : "Template optimization failed"
      );
    }
  }
}

// Utility functions for AI integration
export const AIUtils = {
  /**
   * Format confidence score as percentage
   */
  formatConfidence: (score: number): string => {
    return `${(score * 100).toFixed(1)}%`;
  },

  /**
   * Get quality score color
   */
  getQualityColor: (quality: string): string => {
    switch (quality) {
      case "high":
        return "#10B981"; // green
      case "medium":
        return "#F59E0B"; // yellow
      case "low":
        return "#EF4444"; // red
      default:
        return "#6B7280"; // gray
    }
  },

  /**
   * Get severity color
   */
  getSeverityColor: (severity: string): string => {
    switch (severity) {
      case "high":
        return "#EF4444"; // red
      case "medium":
        return "#F59E0B"; // yellow
      case "low":
        return "#10B981"; // green
      default:
        return "#6B7280"; // gray
    }
  },

  /**
   * Get importance icon
   */
  getImportanceIcon: (importance: string): string => {
    switch (importance) {
      case "high":
        return "🔴";
      case "medium":
        return "🟡";
      case "low":
        return "🟢";
      default:
        return "⭕";
    }
  },

  /**
   * Format timestamp
   */
  formatTimestamp: (timestamp: string): string => {
    return new Date(timestamp).toLocaleString();
  },

  /**
   * Check if analysis is AI-powered
   */
  isAIPowered: (result: any): boolean => {
    return result.ai_powered === true;
  },

  /**
   * Get fallback reason message
   */
  getFallbackMessage: (result: any): string | null => {
    if (result.fallback_reason) {
      return `Note: ${result.fallback_reason}`;
    }
    if (!result.ai_powered) {
      return "Note: Using rule-based analysis (AI service unavailable)";
    }
    return null;
  },
};

export default AIService;
