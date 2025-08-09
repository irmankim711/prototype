/**
 * Enhanced Report Service with Advanced Editing Features
 * Handles report versioning, template management, and collaborative editing
 */

import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_API_URL || "http://localhost:5000/api";

// Types for the enhanced report editing system
export interface ReportVersion {
  id: number;
  report_id: number;
  version_number: number;
  content: any;
  template_id?: number;
  created_by: number;
  created_at: string;
  change_summary: string;
  is_current: boolean;
  file_size?: number;
  creator_name?: string;
}

export interface ReportTemplate {
  id: number;
  name: string;
  description?: string;
  layout_config: any;
  style_config?: any;
  is_public: boolean;
  created_by: number;
  created_at: string;
  usage_count: number;
  creator_name?: string;
  preview_url?: string;
}

export interface EditHistoryItem {
  id: number;
  edit_type: string;
  editor: string;
  timestamp: string;
  has_changes: boolean;
}

export interface VersionComparison {
  changes: Array<{
    type: "added" | "removed" | "modified";
    path: string;
    old_value?: any;
    new_value?: any;
    value?: any;
  }>;
  stats: {
    added: number;
    removed: number;
    modified: number;
    total_changes: number;
  };
}

class EnhancedReportService {
  private getAuthHeaders() {
    const token =
      localStorage.getItem("access_token") ||
      localStorage.getItem("accessToken");
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  }

  // Report Version Management
  async updateReportContent(
    reportId: number,
    content: any,
    changeSummary?: string,
    templateId?: number
  ): Promise<ReportVersion> {
    try {
      const response = await axios.put(
        `${API_BASE_URL}/reports/${reportId}/edit`,
        {
          content,
          change_summary: changeSummary,
          template_id: templateId,
        },
        { headers: this.getAuthHeaders() }
      );
      return response.data.version;
    } catch (error) {
      console.error("Error updating report content:", error);
      throw error;
    }
  }

  async getReportVersions(reportId: number): Promise<{
    versions: ReportVersion[];
    report_name: string;
    total_versions: number;
  }> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/reports/${reportId}/versions`,
        { headers: this.getAuthHeaders() }
      );
      return response.data;
    } catch (error) {
      console.error("Error fetching report versions:", error);
      throw error;
    }
  }

  async getSpecificVersion(
    reportId: number,
    versionId: number
  ): Promise<ReportVersion> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/reports/${reportId}/versions/${versionId}`,
        { headers: this.getAuthHeaders() }
      );
      return response.data.version;
    } catch (error) {
      console.error("Error fetching specific version:", error);
      throw error;
    }
  }

  async rollbackToVersion(
    reportId: number,
    versionId: number
  ): Promise<ReportVersion> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/reports/${reportId}/versions/${versionId}/rollback`,
        {},
        { headers: this.getAuthHeaders() }
      );
      return response.data.new_version;
    } catch (error) {
      console.error("Error rolling back version:", error);
      throw error;
    }
  }

  async compareVersions(
    reportId: number,
    version1Id: number,
    version2Id: number
  ): Promise<VersionComparison> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/reports/${reportId}/versions/compare/${version1Id}/${version2Id}`,
        { headers: this.getAuthHeaders() }
      );
      return response.data.comparison;
    } catch (error) {
      console.error("Error comparing versions:", error);
      throw error;
    }
  }

  // Auto-save functionality
  async autoSaveReport(reportId: number, content: any): Promise<void> {
    try {
      await axios.post(
        `${API_BASE_URL}/reports/${reportId}/auto-save`,
        { content },
        { headers: this.getAuthHeaders() }
      );
    } catch (error) {
      console.error("Error auto-saving report:", error);
      // Don't throw error for auto-save failures to avoid disrupting user experience
    }
  }

  // Template Management
  async getTemplates(): Promise<ReportTemplate[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/templates`, {
        headers: this.getAuthHeaders(),
      });
      return response.data.templates;
    } catch (error) {
      console.error("Error fetching templates:", error);
      throw error;
    }
  }

  async createTemplate(
    name: string,
    layoutConfig: any,
    description?: string,
    styleConfig?: any,
    isPublic: boolean = false
  ): Promise<ReportTemplate> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/templates`,
        {
          name,
          description,
          layout_config: layoutConfig,
          style_config: styleConfig,
          is_public: isPublic,
        },
        { headers: this.getAuthHeaders() }
      );
      return response.data.template;
    } catch (error) {
      console.error("Error creating template:", error);
      throw error;
    }
  }

  async applyTemplate(
    reportId: number,
    templateId: number
  ): Promise<ReportVersion> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/reports/${reportId}/apply-template`,
        { template_id: templateId },
        { headers: this.getAuthHeaders() }
      );
      return response.data.version;
    } catch (error) {
      console.error("Error applying template:", error);
      throw error;
    }
  }

  // Edit History
  async getEditHistory(reportId: number): Promise<EditHistoryItem[]> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/reports/${reportId}/edit-history`,
        { headers: this.getAuthHeaders() }
      );
      return response.data.edit_history;
    } catch (error) {
      console.error("Error fetching edit history:", error);
      throw error;
    }
  }

  // Utility methods for content manipulation
  validateReportContent(content: any): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!content) {
      errors.push("Content cannot be empty");
      return { isValid: false, errors };
    }

    // Basic validation - can be enhanced based on report structure requirements
    if (typeof content !== "object") {
      errors.push("Content must be a valid object");
    }

    // Add more validation rules as needed
    if (content.title && typeof content.title !== "string") {
      errors.push("Title must be a string");
    }

    if (content.sections && !Array.isArray(content.sections)) {
      errors.push("Sections must be an array");
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  }

  // Content diff utility for frontend display
  generateContentDiff(oldContent: any, newContent: any): VersionComparison {
    const changes: any[] = [];
    const stats = { added: 0, removed: 0, modified: 0, total_changes: 0 };

    const compareObjects = (obj1: any, obj2: any, path: string = ""): void => {
      if (
        typeof obj1 === "object" &&
        typeof obj2 === "object" &&
        obj1 !== null &&
        obj2 !== null
      ) {
        const allKeys = new Set([...Object.keys(obj1), ...Object.keys(obj2)]);

        for (const key of allKeys) {
          const newPath = path ? `${path}.${key}` : key;

          if (!(key in obj1)) {
            changes.push({
              type: "added",
              path: newPath,
              value: obj2[key],
            });
            stats.added++;
          } else if (!(key in obj2)) {
            changes.push({
              type: "removed",
              path: newPath,
              value: obj1[key],
            });
            stats.removed++;
          } else {
            compareObjects(obj1[key], obj2[key], newPath);
          }
        }
      } else if (obj1 !== obj2) {
        changes.push({
          type: "modified",
          path: path,
          old_value: obj1,
          new_value: obj2,
        });
        stats.modified++;
      }
    };

    compareObjects(oldContent, newContent);
    stats.total_changes = stats.added + stats.removed + stats.modified;

    return { changes, stats };
  }

  // Content serialization for storage
  serializeContent(content: any): string {
    try {
      return JSON.stringify(content, null, 2);
    } catch (error) {
      console.error("Error serializing content:", error);
      return "{}";
    }
  }

  deserializeContent(serializedContent: string): any {
    try {
      return JSON.parse(serializedContent);
    } catch (error) {
      console.error("Error deserializing content:", error);
      return {};
    }
  }
}

export const enhancedReportService = new EnhancedReportService();
export default enhancedReportService;
