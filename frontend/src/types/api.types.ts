// API Configuration Types
export interface ApiConfig {
  baseURL: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
  maxRetryDelay: number;
}

// Environment Configuration
export interface EnvironmentConfig {
  development: ApiConfig;
  production: ApiConfig;
  staging: ApiConfig;
  test: ApiConfig;
}

// JWT Token Types
export interface JwtToken {
  access_token: string;
  refresh_token?: string;
  expires_in: number;
  token_type: string;
}

export interface JwtPayload {
  sub: string;
  email: string;
  role: string;
  permissions: string[];
  exp: number;
  iat: number;
}

// Request/Response Interceptor Types
export interface RequestInterceptor {
  onRequest?: (config: any) => any;
  onRequestError?: (error: any) => any;
}

export interface ResponseInterceptor {
  onResponse?: (response: any) => any;
  onResponseError?: (error: any) => any;
}

// Error Handling Types
export interface ApiError {
  message: string;
  code: string;
  status: number;
  details?: Record<string, any>;
  timestamp: string;
  requestId?: string;
}

export interface ErrorResponse {
  error: ApiError;
  success: false;
}

// Success Response Types
export interface SuccessResponse<T = any> {
  data: T;
  success: true;
  message?: string;
  timestamp: string;
  requestId?: string;
}

// Generic API Response
export type ApiResponse<T = any> = SuccessResponse<T> | ErrorResponse;

// Pagination Types
export interface PaginationMeta {
  page: number;
  pages: number;
  per_page: number;
  total: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationMeta;
}

// Loading State Types
export interface LoadingState {
  isLoading: boolean;
  error: ApiError | null;
  retryCount: number;
  lastUpdated: string | null;
}

// Retry Configuration
export interface RetryConfig {
  maxAttempts: number;
  baseDelay: number;
  maxDelay: number;
  backoffMultiplier: number;
  retryableStatusCodes: number[];
}

// Request Configuration
export interface RequestConfig {
  timeout?: number;
  retry?: boolean;
  retryConfig?: Partial<RetryConfig>;
  headers?: Record<string, string>;
  params?: Record<string, any>;
  data?: any;
}

// HTTP Methods
export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS';

// API Endpoint Configuration
export interface ApiEndpoint {
  path: string;
  method: HttpMethod;
  requiresAuth: boolean;
  timeout?: number;
  retry?: boolean;
}

// User Types (Enhanced from existing)
export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  username?: string;
  phone?: string;
  company?: string;
  job_title?: string;
  bio?: string;
  avatar_url?: string;
  timezone?: string;
  language?: string;
  theme?: string;
  email_notifications?: boolean;
  push_notifications?: boolean;
  full_name?: string;
  role?: string;
  is_active?: boolean;
  created_at: string;
  updated_at?: string;
  last_login?: string;
  permissions?: string[];
}

// Authentication Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token?: string;
  user: User;
  expires_in: number;
}

export interface RegisterRequest {
  email: string;
  password: string;
  confirmPassword: string;
  first_name?: string;
  last_name?: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  expires_in: number;
}

// Report Types
export interface Report {
  id: string;
  title: string;
  description?: string;
  status: "draft" | "processing" | "completed" | "failed";
  createdAt: string;
  updatedAt: string;
  templateId: string;
  templateFilename?: string;
  outputUrl?: string;
  data?: Record<string, unknown>;
  analysis?: Record<string, unknown>;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description?: string;
  template_type: string;
  file_path: string;
  placeholder_schema?: Record<string, unknown>;
  category?: string;
  supports_charts?: boolean;
  supports_images?: boolean;
  max_participants?: number;
  usage_count?: number;
  version?: string;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ReportStats {
  totalReports: number;
  reportsThisMonth: number;
  activeTemplates: number;
  processingReports: number;
}

// Dashboard Types
export interface DashboardStats {
  totalReports: number;
  completedReports: number;
  pendingReports: number;
  recentActivity: number;
  successRate: number;
  avgProcessingTime: number;
}

export interface ChartData {
  type: string;
  data: {
    labels: string[];
    data: number[];
    backgroundColor?: string[];
    borderColor?: string;
  };
}

// File Types
export interface FileInfo {
  id: string;
  filename: string;
  file_size: number;
  mime_type: string;
  created_at: string;
  uploader_id: string;
  is_public: boolean;
  url: string;
}

export interface FileStats {
  total_files: number;
  total_size_bytes: number;
  total_size_mb: number;
  public_files: number;
  private_files: number;
  weekly_uploads: number;
}

// Form Types
export interface Form {
  id: string;
  title: string;
  description?: string;
  fields: FormField[];
  created_at: string;
  is_active: boolean;
  is_public?: boolean;
}

export interface FormField {
  id: string;
  name: string;
  type: string;
  label: string;
  required: boolean;
  options?: string[];
}

// Template Types
export interface WordTemplate {
  id: string;
  name: string;
  description: string;
  filename: string;
  previewUrl?: string;
}

export interface TemplateContent {
  content: Array<{ type: string; text: string; style: string }>;
  placeholders: string[];
}

export interface TemplatePlaceholders {
  placeholders: string[];
}

// Report Generation Types
export interface ReportGenerationRequest {
  templateFilename: string;
  data: Record<string, string>;
}

export interface ReportGenerationResponse {
  downloadUrl: string;
  message: string;
  success: boolean;
}

export interface ExcelReportGenerationRequest {
  templateFilename: string;
  excelFile: File;
}

export interface ExcelReportGenerationResponse {
  success: boolean;
  downloadUrl: string;
  filename: string;
  message: string;
  context_used?: Record<string, unknown>;
  optimizations?: Record<string, unknown>;
  missing_fields?: string[];
}

// AI Analysis Types
export interface AIAnalysisRequest {
  data: Record<string, unknown>;
  analysisType?: string;
  options?: Record<string, any>;
}

export interface AIAnalysisResponse {
  summary: string;
  insights: string[];
  suggestions: string;
  confidence: number;
  processingTime: number;
}

// Database Test Types
export interface DatabaseTestResponse {
  status: string;
  message: string;
  table_count: number;
  connection_time: number;
}

// API Service Interface
export interface IApiService {
  // Configuration
  setBaseURL(url: string): void;
  getBaseURL(): string;
  setAuthToken(token: string): void;
  clearAuthToken(): void;
  setRequestTimeout(timeout: number): void;
  
  // Authentication
  login(credentials: LoginRequest): Promise<LoginResponse>;
  register(userData: RegisterRequest): Promise<LoginResponse>;
  logout(): Promise<void>;
  refreshToken(): Promise<RefreshTokenResponse>;
  getCurrentUser(): Promise<User>;
  
  // HTTP Methods
  get<T>(url: string, config?: RequestConfig): Promise<T>;
  post<T>(url: string, data?: any, config?: RequestConfig): Promise<T>;
  put<T>(url: string, data?: any, config?: RequestConfig): Promise<T>;
  patch<T>(url: string, data?: any, config?: RequestConfig): Promise<T>;
  delete<T>(url: string, config?: RequestConfig): Promise<T>;
  
  // Utility Methods
  isAuthenticated(): boolean;
  getAuthToken(): string | null;
  getTokenExpiry(): number | null;
  isTokenExpired(): boolean;
}

// Hook Return Types
export interface UseApiReturn<T> {
  data: T | null;
  loading: LoadingState;
  error: ApiError | null;
  refetch: () => Promise<void>;
  mutate: (data: T) => void;
}

export interface UseApiMutationReturn<T, V> {
  mutate: (variables: V) => Promise<T>;
  loading: boolean;
  error: ApiError | null;
  reset: () => void;
}
