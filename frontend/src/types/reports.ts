export type ReportStatus = "pending" | "generating" | "completed" | "failed";

export interface Report {
  id: string;
  formId: string;
  formTitle: string;
  title: string;
  description?: string;
  status: ReportStatus;
  report_type?: string;
  submissionCount: number;
  createdAt: string;
  created_at?: string;
  updatedAt: string;
  completedAt?: string;
  filePath?: string;
  // Multi-format file paths
  pdf_file_path?: string;
  docx_file_path?: string;
  excel_file_path?: string;
  // File sizes
  pdf_file_size?: number;
  docx_file_size?: number;
  excel_file_size?: number;
  aiInsights?: {
    summary: string;
    trends: string[];
    recommendations: string[];
    keyMetrics: {
      [key: string]: number | string;
    };
  };
  content?: any;
  errorMessage?: string;
}

export interface ReportGenerationRequest {
  formId: string;
  title?: string;
  includeCharts?: boolean;
  analysisType?: "basic" | "detailed" | "comprehensive";
}

export interface ReportUpdateRequest {
  title?: string;
  content?: string;
  aiInsights?: Report["aiInsights"];
}

export interface FormSubmission {
  id: string;
  formId: string;
  data: Record<string, any>;
  source: "google_forms" | "microsoft_forms" | "public" | "custom";
  submittedAt: string;
  ipAddress?: string;
  userAgent?: string;
  normalizedData?: Record<string, any>;
}

export interface FormAnalytics {
  totalSubmissions: number;
  submissionsThisWeek: number;
  submissionsThisMonth: number;
  avgSubmissionsPerDay: number;
  topFieldValues: Record<string, Array<{ value: string; count: number }>>;
  submissionTrends: Array<{ date: string; count: number }>;
  completionRate: number;
}
