import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000/api";

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
  private getAuthHeaders() {
    const token = localStorage.getItem("token");
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }

  async getDashboardStats(): Promise<AnalyticsStats> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/analytics/dashboard/stats`,
        {
          headers: this.getAuthHeaders(),
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error fetching dashboard stats:", error);
      throw error;
    }
  }

  async getSubmissionTrends(days: number = 30): Promise<SubmissionTrend> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/analytics/trends?days=${days}`,
        {
          headers: this.getAuthHeaders(),
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error fetching submission trends:", error);
      throw error;
    }
  }

  async getTopPerformingForms(
    limit: number = 5
  ): Promise<{ forms: TopFormData[] }> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/analytics/top-forms?limit=${limit}`,
        {
          headers: this.getAuthHeaders(),
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error fetching top performing forms:", error);
      throw error;
    }
  }

  async getFieldAnalytics(formId: number): Promise<FieldAnalytics> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/analytics/field-analytics/${formId}`,
        {
          headers: this.getAuthHeaders(),
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error fetching field analytics:", error);
      throw error;
    }
  }

  async getGeographicDistribution(): Promise<GeographicData> {
    try {
      const response = await axios.get(`${API_BASE_URL}/analytics/geographic`, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching geographic distribution:", error);
      throw error;
    }
  }

  async getTimeOfDayAnalytics(): Promise<TimeOfDayData> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/analytics/time-of-day`,
        {
          headers: this.getAuthHeaders(),
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error fetching time of day analytics:", error);
      throw error;
    }
  }

  async getPerformanceComparison(): Promise<PerformanceComparison> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/analytics/performance-comparison`,
        {
          headers: this.getAuthHeaders(),
        }
      );
      return response.data;
    } catch (error) {
      console.error("Error fetching performance comparison:", error);
      throw error;
    }
  }

  async getRealTimeStats(): Promise<AnalyticsStats> {
    try {
      const response = await axios.get(`${API_BASE_URL}/analytics/real-time`, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error("Error fetching real-time stats:", error);
      throw error;
    }
  }

  async getChartData(
    chartType: string,
    params?: Record<string, string | number>
  ): Promise<ChartData> {
    try {
      const queryParams = params
        ? new URLSearchParams(
            Object.entries(params).map(([key, value]) => [key, String(value)])
          ).toString()
        : "";
      const url = `${API_BASE_URL}/analytics/charts/${chartType}${
        queryParams ? `?${queryParams}` : ""
      }`;
      const response = await axios.get(url, {
        headers: this.getAuthHeaders(),
      });
      return response.data;
    } catch (error) {
      console.error(`Error fetching ${chartType} chart data:`, error);
      throw error;
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
