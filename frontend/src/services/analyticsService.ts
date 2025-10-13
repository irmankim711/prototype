import axios, { AxiosError } from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000";

// Debug logging for environment variables
console.log('🔧 Environment Debug Info:');
console.log('  VITE_API_URL:', import.meta.env.VITE_API_URL);
console.log('  Final API_BASE_URL:', API_BASE_URL);
console.log('  Environment Mode:', import.meta.env.MODE);

// Enhanced axios instance with retry logic and better error handling
const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  timeout: 15000, // 15 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Authentication interceptor - automatically adds JWT token to all requests
apiClient.interceptors.request.use(
  (config) => {
    // Get token from localStorage
    const token = localStorage.getItem("accessToken");
    
    if (token) {
      // Add Authorization header with Bearer token
      config.headers.Authorization = `Bearer ${token}`;
      console.log('🔑 [Auth Interceptor] Token added to request:', {
        ...config.headers,
        Authorization: `${token.substring(0, 20)}...`
      });
    } else {
      console.warn('⚠️ [Auth Interceptor] No token found in localStorage');
    }
    
    return config;
  },
  (error) => {
    console.error('🚨 Auth Interceptor Error:', error);
    return Promise.reject(error);
  }
);

// Enhanced request interceptor with detailed logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`🔄 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    
    // 1. Log request headers (especially Authorization token)
    const authHeader = config.headers.Authorization;
    const authValue = typeof authHeader === 'string' ? authHeader : String(authHeader || '');
    console.log('📋 Request Headers:', {
      ...config.headers,
      Authorization: authValue ? 
        `${authValue.substring(0, 20)}...` : 'Not set'
    });
    
    // 2. Log request parameters/query strings
    if (config.params) {
      console.log('🔍 Request Params:', config.params);
    }
    if (config.url && config.url.includes('?')) {
      const queryString = config.url.split('?')[1];
      console.log('🔍 Query String:', queryString);
    }
    
    // 3. Log request body (if any)
    if (config.data) {
      console.log('📦 Request Body:', config.data);
    }
    
    // Log full request configuration for debugging
    console.log('🔧 Full Request Config:', {
      method: config.method,
      url: config.url,
      baseURL: config.baseURL,
      timeout: config.timeout,
      withCredentials: config.withCredentials
    });
    
    return config;
  },
  (error) => {
    console.error('🚨 Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for enhanced error handling
apiClient.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error: AxiosError) => {
    console.error('🚨 API Error:', error.message);
    
    if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
      const errorMessage = 'Backend service unavailable. Please ensure the server is running on port 5000.';
      console.error('🔥 Connection Error:', errorMessage);
      throw new Error(errorMessage);
    }
    
    if (error.code === 'ECONNABORTED') {
      const errorMessage = 'Request timeout. The server took too long to respond.';
      console.error('⏰ Timeout Error:', errorMessage);
      throw new Error(errorMessage);
    }
    
    return Promise.reject(error);
  }
);

export interface AnalyticsStats {
  submissions_24h: number;
  submissions_1h: number;
  active_forms: number;
  total_forms: number;
  last_updated: string;
  activity_feed: ActivityFeedItem[];
  is_active: boolean;
}

export interface ActivityFeedItem {
  id: number;
  form_title: string;
  created_at: string;
  time_ago: string;
}

export interface SubmissionTrend {
  labels: string[];
  data: number[];
  total_submissions: number;
  average_daily: number;
  peak_day: string | null;
}

export interface TopFormData {
  form_id: number;
  form_name: string;
  submissions: number;
  completion_rate: number;
  recent_activity: number;
  trend: "up" | "down" | "stable";
}

export interface TimeOfDayData {
  hourly_data: number[];
  labels: string[];
  peak_hour: string;
  peak_submissions: number;
  total_submissions: number;
}

export interface GeographicData {
  countries: Array<{
    name: string;
    submissions: number;
    percentage: number;
  }>;
  total_countries: number;
  most_active_country: string;
}

export interface PerformanceComparison {
  forms: Array<{
    form_id: number;
    form_title: string;
    total_submissions: number;
    days_active: number;
    avg_per_day: number;
    recent_submissions: number;
    performance_score: number;
  }>;
  best_performer: {
    form_id: number;
    form_title: string;
    total_submissions: number;
    days_active: number;
    avg_per_day: number;
    recent_submissions: number;
    performance_score: number;
  } | null;
  total_forms_analyzed: number;
}

export interface FieldAnalytics {
  field_stats: Record<
    string,
    {
      completion_rate: number;
      field_type: string;
      is_required: boolean;
      completed_count: number;
      total_submissions: number;
      abandonment_rate: number;
    }
  >;
  form_title: string;
  total_submissions: number;
  overall_completion: number;
}

export interface ChartData {
  type: string;
  title: string;
  data: {
    labels: string[];
    datasets: Array<{
      label?: string;
      data: number[];
      backgroundColor?: string | string[];
      borderColor?: string;
      borderWidth?: number;
      fill?: boolean;
      tension?: number;
      yAxisID?: string;
    }>;
  };
  options?: Record<string, unknown>;
}

class AnalyticsService {
  // Remove the getAuthHeaders method since we now use interceptors
  
  // Enhanced response validation helper
  private isValidResponse(data: any, expectedStructure: string): boolean {
    try {
      switch (expectedStructure) {
        case 'analyticsStats':
          return data && typeof data.submissions_24h === 'number' && Array.isArray(data.activity_feed);
        case 'submissionTrend':
          return data && Array.isArray(data.labels) && Array.isArray(data.data);
        case 'topForms':
          return data && Array.isArray(data.forms);
        case 'fieldAnalytics':
          return data && typeof data.form_title === 'string' && data.field_stats;
        case 'geographicData':
          return data && Array.isArray(data.countries);
        case 'timeOfDayData':
          return data && Array.isArray(data.hourly_data) && Array.isArray(data.labels);
        case 'performanceComparison':
          return data && Array.isArray(data.forms);
        case 'chartData':
          return data && data.type && data.data && Array.isArray(data.data.labels);
        default:
          return data !== null && data !== undefined;
      }
    } catch (error) {
      console.error('Response validation error:', error);
      return false;
    }
  }

  // Enhanced error handling with detailed logging
  private handleApiError(error: any, operation: string, endpoint: string): never {
    console.error(`🚨 [AnalyticsService] ${operation} failed:`, {
      endpoint,
      error: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      headers: error.response?.headers,
      config: error.config
    });

    // Check for specific error types
    if (error.response?.status === 404) {
      throw new Error(`Endpoint not found: ${endpoint}. Please check if the backend service is running.`);
    }
    
    if (error.response?.status === 500) {
      throw new Error(`Server error: ${endpoint}. The backend service encountered an internal error.`);
    }
    
    if (error.code === 'ERR_NETWORK') {
      throw new Error(`Network error: Unable to connect to ${endpoint}. Please check your internet connection and ensure the backend is running.`);
    }
    
    if (error.code === 'ECONNABORTED') {
      throw new Error(`Request timeout: ${endpoint} took too long to respond. Please try again.`);
    }

    throw new Error(`Failed to ${operation.toLowerCase()}. ${error.message || 'Unknown error occurred.'}`);
  }

  async getDashboardStats(): Promise<AnalyticsStats> {
    const endpoint = "/analytics/dashboard/stats";
    try {
      console.log('📊 [AnalyticsService] Fetching dashboard stats...');
      console.log('🔗 Endpoint:', endpoint);
      
      const response = await apiClient.get(endpoint);
      
      // Log raw response for debugging
      console.log('📥 Raw API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data
      });
      
      // Validate response structure
      if (!this.isValidResponse(response.data, 'analyticsStats')) {
        console.error('❌ Invalid response structure:', response.data);
        throw new Error('Invalid response format from dashboard stats endpoint');
      }
      
      console.log('✅ Dashboard stats fetched successfully');
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'fetch dashboard stats', endpoint);
    }
  }

  async getSubmissionTrends(days: number = 30): Promise<SubmissionTrend> {
    const endpoint = `/analytics/trends?days=${days}`;
    try {
      console.log('📈 [AnalyticsService] Fetching submission trends for', days, 'days...');
      console.log('📝 Query Parameters:', { days });
      console.log('🔗 Endpoint:', endpoint);
      
      const response = await apiClient.get(endpoint);
      
      // Log raw response for debugging
      console.log('📥 Raw API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data
      });
      
      // Validate response structure
      if (!this.isValidResponse(response.data, 'submissionTrend')) {
        console.error('❌ Invalid response structure:', response.data);
        throw new Error('Invalid response format from submission trends endpoint');
      }
      
      console.log('✅ Submission trends fetched successfully');
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'fetch submission trends', endpoint);
    }
  }

  async getTopPerformingForms(
    limit: number = 5
  ): Promise<{ forms: TopFormData[] }> {
    const endpoint = `/analytics/top-forms?limit=${limit}`;
    try {
      console.log('🏆 [AnalyticsService] Fetching top performing forms with limit:', limit);
      console.log('📝 Query Parameters:', { limit });
      console.log('🔗 Endpoint:', endpoint);
      
      const response = await apiClient.get(endpoint);
      
      // Log raw response for debugging
      console.log('📥 Raw API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data
      });
      
      // Validate response structure
      if (!this.isValidResponse(response.data, 'topForms')) {
        console.error('❌ Invalid response structure:', response.data);
        throw new Error('Invalid response format from top forms endpoint');
      }
      
      console.log('✅ Top performing forms fetched successfully');
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'fetch top performing forms', endpoint);
    }
  }

  async getFieldAnalytics(formId: number): Promise<FieldAnalytics> {
    const endpoint = `/analytics/field-analytics/${formId}`;
    try {
      console.log('📋 [AnalyticsService] Fetching field analytics for form ID:', formId);
      console.log('📝 Path Parameters:', { formId });
      console.log('🔗 Endpoint:', endpoint);
      
      const response = await apiClient.get(endpoint);
      
      // Log raw response for debugging
      console.log('📥 Raw API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data
      });
      
      // Validate response structure
      if (!this.isValidResponse(response.data, 'fieldAnalytics')) {
        console.error('❌ Invalid response structure:', response.data);
        throw new Error('Invalid response format from field analytics endpoint');
      }
      
      console.log('✅ Field analytics fetched successfully');
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'fetch field analytics', endpoint);
    }
  }

  async getGeographicDistribution(): Promise<GeographicData> {
    const endpoint = `/analytics/geographic`;
    try {
      console.log('🌍 [AnalyticsService] Fetching geographic distribution...');
      console.log('🔗 Endpoint:', endpoint);
      
      const response = await apiClient.get(endpoint);
      
      // Log raw response for debugging
      console.log('📥 Raw API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data
      });
      
      // Validate response structure
      if (!this.isValidResponse(response.data, 'geographicData')) {
        console.error('❌ Invalid response structure:', response.data);
        throw new Error('Invalid response format from geographic distribution endpoint');
      }
      
      console.log('✅ Geographic distribution fetched successfully');
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'fetch geographic distribution', endpoint);
    }
  }

  async getTimeOfDayAnalytics(): Promise<TimeOfDayData> {
    const endpoint = `/analytics/time-of-day`;
    try {
      console.log('⏰ [AnalyticsService] Fetching time of day analytics...');
      console.log('🔗 Endpoint:', endpoint);
      
      const response = await apiClient.get(endpoint);
      
      // Log raw response for debugging
      console.log('📥 Raw API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data
      });
      
      // Validate response structure
      if (!this.isValidResponse(response.data, 'timeOfDayData')) {
        console.error('❌ Invalid response structure:', response.data);
        throw new Error('Invalid response format from time of day analytics endpoint');
      }
      
      console.log('✅ Time of day analytics fetched successfully');
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'fetch time of day analytics', endpoint);
    }
  }

  async getPerformanceComparison(): Promise<PerformanceComparison> {
    const endpoint = `/analytics/performance-comparison`;
    try {
      console.log('📊 [AnalyticsService] Fetching performance comparison...');
      console.log('🔗 Endpoint:', endpoint);
      
      const response = await apiClient.get(endpoint);
      
      // Log raw response for debugging
      console.log('📥 Raw API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data
      });
      
      // Validate response structure
      if (!this.isValidResponse(response.data, 'performanceComparison')) {
        console.error('❌ Invalid response structure:', response.data);
        throw new Error('Invalid response format from performance comparison endpoint');
      }
      
      console.log('✅ Performance comparison fetched successfully');
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'fetch performance comparison', endpoint);
    }
  }

  async getRealTimeStats(): Promise<AnalyticsStats> {
    const endpoint = `/analytics/real-time`;
    try {
      console.log('⚡ [AnalyticsService] Fetching real-time stats...');
      console.log('🔗 Endpoint:', endpoint);
      
      const response = await apiClient.get(endpoint);
      
      // Log raw response for debugging
      console.log('📥 Raw API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data
      });
      
      // Validate response structure
      if (!this.isValidResponse(response.data, 'analyticsStats')) {
        console.error('❌ Invalid response structure:', response.data);
        throw new Error('Invalid response format from real-time stats endpoint');
      }
      
      console.log('✅ Real-time stats fetched successfully');
      return response.data;
    } catch (error) {
      this.handleApiError(error, 'fetch real-time stats', endpoint);
    }
  }

  async getChartData(
    chartType: string,
    params?: Record<string, string | number>
  ): Promise<ChartData> {
    try {
      console.log('📊 [AnalyticsService] Fetching chart data for type:', chartType);
      console.log('📝 Chart Parameters:', { chartType, params });
      
      const queryParams = params
        ? new URLSearchParams(
            Object.entries(params).map(([key, value]) => [key, String(value)])
          ).toString()
        : "";
      const url = `/analytics/charts/${chartType}${
        queryParams ? `?${queryParams}` : ""
      }`;
      console.log('🔗 Final URL:', url);
      
      const response = await apiClient.get(url);
      
      // Log raw response for debugging
      console.log('📥 Raw API response:', {
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data
      });
      
      // Validate response structure
      if (!this.isValidResponse(response.data, 'chartData')) {
        console.error('❌ Invalid response structure:', response.data);
        throw new Error(`Invalid response format from ${chartType} chart endpoint`);
      }
      
      console.log('✅ Chart data fetched successfully');
      return response.data;
    } catch (error) {
      this.handleApiError(error, `fetch ${chartType} chart data`, `/analytics/charts/${chartType}`);
    }
  }

  // Convenience methods for specific chart types
  async getSubmissionTrendChart(days: number = 30): Promise<ChartData> {
    return this.getChartData("submissions-trend", { days });
  }

  async getTimeDistributionChart(): Promise<ChartData> {
    return this.getChartData("time-distribution");
  }

  async getTopFormsChart(limit: number = 5): Promise<ChartData> {
    return this.getChartData("top-forms", { limit });
  }

  async getPerformanceComparisonChart(): Promise<ChartData> {
    return this.getChartData("performance-comparison");
  }

  async getGeographicChart(): Promise<ChartData> {
    return this.getChartData("geographic");
  }
}

export const analyticsService = new AnalyticsService();
export default analyticsService;
