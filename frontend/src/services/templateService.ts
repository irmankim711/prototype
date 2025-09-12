import type { ReportTemplate } from '../types/api.types';
import { fetchReportTemplates, createReportTemplate, updateReportTemplate } from './api';

// Local Template interface for the service
interface Template {
  id: string;
  name: string;
  type: 'latex' | 'jinja2' | 'docx';
  description: string;
  content: string;
  createdAt: string;
  updatedAt: string;
}

// Template service for managing templates
export class TemplateService {
  private static readonly STORAGE_KEY = 'report_templates';

  // Get all templates from API
  static async getTemplates(): Promise<Template[]> {
    try {
      // Try to get templates from API first
      const apiTemplates = await fetchReportTemplates();
      if (apiTemplates && apiTemplates.length > 0) {
        // Convert API format to local format and cache
        const convertedTemplates = apiTemplates.map((t: ReportTemplate) => ({
          id: t.id,
          name: t.name,
          type: (t.template_type as 'latex' | 'jinja2' | 'docx') || 'jinja2',
          description: t.description || '',
          content: '', // API doesn't provide content, will need to fetch separately
          createdAt: t.created_at || new Date().toISOString(),
          updatedAt: t.updated_at || new Date().toISOString()
        }));
        
        // Cache the templates
        this.saveTemplates(convertedTemplates);
        return convertedTemplates;
      }
    } catch (error) {
      console.error('Error fetching templates from API:', error);
    }

    // Fallback to local storage
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('Error loading templates from storage:', error);
    }
    return [];
  }

  // Save templates to local storage (for caching)
  static saveTemplates(templates: Template[]): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(templates));
    } catch (error) {
      console.error('Error saving templates to storage:', error);
    }
  }

  // Add a new template via API
  static async addTemplate(template: Template): Promise<Template[]> {
    try {
      // Create template via API
      const newTemplate = await createReportTemplate({
        name: template.name,
        description: template.description,
        template_type: template.type,
        file_path: template.name,
        is_active: true
      });
      
      // Update local cache
      const templates = await this.getTemplates();
      const newTemplates = [...templates, template];
      this.saveTemplates(newTemplates);
      return newTemplates;
    } catch (error) {
      console.error('Error creating template via API:', error);
      // Fallback to local storage
      const templates = await this.getTemplates();
      const newTemplates = [...templates, template];
      this.saveTemplates(newTemplates);
      return newTemplates;
    }
  }

  // Update an existing template via API
  static async updateTemplate(updatedTemplate: Template): Promise<Template[]> {
    try {
      // Update template via API
      await updateReportTemplate(updatedTemplate.id, {
        name: updatedTemplate.name,
        description: updatedTemplate.description,
        template_type: updatedTemplate.type,
        file_path: updatedTemplate.name
      });
      
      // Update local cache
      const templates = await this.getTemplates();
      const newTemplates = templates.map(t => 
        t.id === updatedTemplate.id ? updatedTemplate : t
      );
      this.saveTemplates(newTemplates);
      return newTemplates;
    } catch (error) {
      console.error('Error updating template via API:', error);
      // Fallback to local storage
      const templates = await this.getTemplates();
      const newTemplates = templates.map(t => 
        t.id === updatedTemplate.id ? updatedTemplate : t
      );
      this.saveTemplates(newTemplates);
      return newTemplates;
    }
  }

  // Delete a template
  static async deleteTemplate(templateId: string): Promise<Template[]> {
    try {
      // For now, just remove from local cache since we don't have a delete endpoint
      const templates = await this.getTemplates();
      const newTemplates = templates.filter(t => t.id !== templateId);
      this.saveTemplates(newTemplates);
      return newTemplates;
    } catch (error) {
      console.error('Error deleting template:', error);
      // Fallback to local storage
      const templates = await this.getTemplates();
      const newTemplates = templates.filter(t => t.id !== templateId);
      this.saveTemplates(newTemplates);
      return newTemplates;
    }
  }

  // Get template by ID
  static async getTemplateById(templateId: string): Promise<Template | undefined> {
    const templates = await this.getTemplates();
    return templates.find(t => t.id === templateId);
  }

  // Import templates from files
  static async importTemplatesFromFiles(files: File[]): Promise<Template[]> {
    const newTemplates: Template[] = [];
    
    for (const file of files) {
      try {
        const content = await this.readFileContent(file);
        const template: Template = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          name: file.name.replace(/\.[^/.]+$/, ''), // Remove file extension
          type: this.getTemplateTypeFromFile(file),
          description: `Imported from ${file.name}`,
          content: content,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        newTemplates.push(template);
      } catch (error) {
        console.error(`Error importing template from ${file.name}:`, error);
      }
    }

    // Add to existing templates
    const existingTemplates = await this.getTemplates();
    const allTemplates = [...existingTemplates, ...newTemplates];
    this.saveTemplates(allTemplates);
    
    return allTemplates;
  }

  // Export template to file
  static exportTemplate(template: Template): void {
    const blob = new Blob([template.content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${template.name}.${template.type}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Export all templates as a zip file
  static async exportAllTemplates(): Promise<void> {
    const templates = await this.getTemplates();
    if (templates.length === 0) {
      alert('No templates to export');
      return;
    }

    // For now, we'll export as individual files
    // In a production environment, you might want to use a library like JSZip
    templates.forEach(template => {
      this.exportTemplate(template);
    });
  }

  // Validate template content
  static validateTemplate(template: Template): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!template.name?.trim()) {
      errors.push('Template name is required');
    }

    if (!template.description?.trim()) {
      errors.push('Template description is required');
    }

    if (!template.content?.trim()) {
      errors.push('Template content is required');
    }

    if (!template.type) {
      errors.push('Template type is required');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  // Get template type from file
  private static getTemplateTypeFromFile(file: File): 'latex' | 'jinja2' | 'docx' {
    const extension = file.name.split('.').pop()?.toLowerCase();
    
    switch (extension) {
      case 'tex':
        return 'latex';
      case 'jinja':
      case 'jinja2':
        return 'jinja2';
      case 'docx':
        return 'docx';
      default:
        return 'jinja2'; // Default to jinja2
    }
  }

  // Read file content
  private static async readFileContent(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          resolve(e.target.result as string);
        } else {
          reject(new Error('Failed to read file'));
        }
      };
      reader.onerror = () => reject(new Error('Failed to read file'));
      reader.readAsText(file);
    });
  }

  // Search templates
  static async searchTemplates(query: string): Promise<Template[]> {
    const templates = await this.getTemplates();
    if (!query.trim()) return templates;

    const lowerQuery = query.toLowerCase();
    return templates.filter(template => 
      template.name.toLowerCase().includes(lowerQuery) ||
      template.description.toLowerCase().includes(lowerQuery) ||
      template.content.toLowerCase().includes(lowerQuery)
    );
  }

  // Get templates by type
  static async getTemplatesByType(type: 'latex' | 'jinja2' | 'docx'): Promise<Template[]> {
    const templates = await this.getTemplates();
    return templates.filter(t => t.type === type);
  }

  // Get template statistics
  static async getTemplateStats(): Promise<{
    total: number;
    byType: Record<string, number>;
    recentlyUpdated: Template[];
  }> {
    const templates = await this.getTemplates();
    
    const byType = templates.reduce((acc, template) => {
      acc[template.type] = (acc[template.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const recentlyUpdated = templates
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
      .slice(0, 5);

    return {
      total: templates.length,
      byType,
      recentlyUpdated
    };
  }
}

export default TemplateService;
