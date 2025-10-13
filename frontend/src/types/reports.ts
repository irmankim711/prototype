export type ReportStatus = "pending" | "generating" | "completed" | "failed";

export interface Report {
  id: string;
  formId: string;
  formTitle: string;
  title: string;
  status: ReportStatus;
  submissionCount: number;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  filePath?: string;
  aiInsights?: {
    summary: string;
    trends: string[];
    recommendations: string[];
    keyMetrics: {
      [key: string]: number | string;
    };
  };
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
