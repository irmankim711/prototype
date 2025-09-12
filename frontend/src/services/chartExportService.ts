/**
 * Chart Export Service
 * Handles exporting charts in various formats (PNG, SVG, PDF, Excel, CSV)
 */
import type { ChartData, ChartConfig } from '../components/NextGenReportBuilder/types';
import type { ChartExportOptions } from './advancedChartService';

export interface ExportResult {
  success: boolean;
  data: Blob | string;
  format: string;
  filename: string;
  size: number;
  metadata?: Record<string, any>;
  error?: string;
}

export interface ExportMetadata {
  title: string;
  description?: string;
  author?: string;
  createdDate: Date;
  version?: string;
  tags?: string[];
}

export interface ExportTemplate {
  id: string;
  name: string;
  description: string;
  format: string;
  options: Partial<ChartExportOptions>;
  isDefault: boolean;
  createdAt: Date;
}

class ChartExportService {
  private exportTemplates: Map<string, ExportTemplate> = new Map();
  private defaultOptions: ChartExportOptions = {
    format: 'png',
    width: 1200,
    height: 800,
    dpi: 300,
    backgroundColor: '#ffffff',
    includeLegend: true,
    includeTitle: true,
    includeData: true
  };

  constructor() {
    this.initializeExportTemplates();
  }

  private initializeExportTemplates(): void {
    const templates: ExportTemplate[] = [
      {
        id: 'high-quality-png',
        name: 'High Quality PNG',
        description: 'High resolution PNG export for presentations',
        format: 'png',
        options: {
          width: 1920,
          height: 1080,
          dpi: 300,
          backgroundColor: '#ffffff'
        },
        isDefault: true,
        createdAt: new Date()
      },
      {
        id: 'print-ready-pdf',
        name: 'Print Ready PDF',
        description: 'PDF optimized for printing',
        format: 'pdf',
        options: {
          width: 8.5 * 96, // 8.5 inches in pixels
          height: 11 * 96, // 11 inches in pixels
          dpi: 300,
          backgroundColor: '#ffffff'
        },
        isDefault: false,
        createdAt: new Date()
      },
      {
        id: 'web-optimized-svg',
        name: 'Web Optimized SVG',
        description: 'Scalable vector graphics for web use',
        format: 'svg',
        options: {
          width: 800,
          height: 600,
          backgroundColor: 'transparent'
        },
        isDefault: false,
        createdAt: new Date()
      }
    ];

    templates.forEach(template => {
      this.exportTemplates.set(template.id, template);
    });
  }

  async exportAsPNG(chartElement: HTMLElement, options: Partial<ChartExportOptions> = {}): Promise<ExportResult> {
    try {
      const config = { ...this.defaultOptions, ...options, format: 'png' as const };
      const canvas = await this.htmlToCanvas(chartElement, config);
      const blob = await new Promise<Blob>((resolve) => {
        canvas.toBlob((blob) => {
          if (blob) resolve(blob);
          else throw new Error('Failed to create blob from canvas');
        }, 'image/png');
      });

      return {
        success: true,
        data: blob,
        format: 'png',
        filename: this.generateFilename('png'),
        size: blob.size,
        metadata: {
          width: config.width,
          height: config.height,
          dpi: config.dpi
        }
      };
    } catch (error) {
      return {
        success: false,
        data: new Blob(),
        format: 'png',
        filename: this.generateFilename('png'),
        size: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async exportAsSVG(chartElement: HTMLElement, options: Partial<ChartExportOptions> = {}): Promise<ExportResult> {
    try {
      const config = { ...this.defaultOptions, ...options, format: 'svg' as const };
      const svgString = await this.htmlToSVG(chartElement, config);
      const blob = new Blob([svgString], { type: 'image/svg+xml' });

      return {
        success: true,
        data: blob,
        format: 'svg',
        filename: this.generateFilename('svg'),
        size: blob.size,
        metadata: {
          width: config.width,
          height: config.height
        }
      };
    } catch (error) {
      return {
        success: false,
        data: new Blob(),
        format: 'svg',
        filename: this.generateFilename('svg'),
        size: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async exportAsPDF(chartElement: HTMLElement, options: Partial<ChartExportOptions> = {}, metadata?: ExportMetadata): Promise<ExportResult> {
    try {
      const config = { ...this.defaultOptions, ...options, format: 'pdf' as const };
      const pdfBlob = await this.generatePDF(chartElement, config, metadata);
      
      return {
        success: true,
        data: pdfBlob,
        format: 'pdf',
        filename: this.generateFilename('pdf'),
        size: pdfBlob.size,
        metadata: {
          ...metadata,
          width: config.width,
          height: config.height
        }
      };
    } catch (error) {
      return {
        success: false,
        data: new Blob(),
        format: 'pdf',
        filename: this.generateFilename('pdf'),
        size: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async exportAsExcel(chartData: ChartData, chartConfig: ChartConfig, options: Partial<ChartExportOptions> = {}, metadata?: ExportMetadata): Promise<ExportResult> {
    try {
      const config = { ...this.defaultOptions, ...options, format: 'excel' as const };
      const excelBlob = await this.generateExcel(chartData, chartConfig, config, metadata);
      
      return {
        success: true,
        data: excelBlob,
        format: 'excel',
        filename: this.generateFilename('xlsx'),
        size: excelBlob.size,
        metadata: {
          ...metadata,
          chartType: chartConfig.type,
          dataPoints: chartData.datasets.reduce((sum, dataset) => sum + dataset.data.length, 0)
        }
      };
    } catch (error) {
      return {
        success: false,
        data: new Blob(),
        format: 'excel',
        filename: this.generateFilename('xlsx'),
        size: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async exportAsCSV(chartData: ChartData, chartConfig: ChartConfig, options: Partial<ChartExportOptions> = {}): Promise<ExportResult> {
    try {
      const config = { ...this.defaultOptions, ...options, format: 'csv' as const };
      const csvString = this.generateCSV(chartData, chartConfig, config);
      const blob = new Blob([csvString], { type: 'text/csv' });

      return {
        success: true,
        data: blob,
        format: 'csv',
        filename: this.generateFilename('csv'),
        size: blob.size,
        metadata: {
          chartType: chartConfig.type,
          dataPoints: chartData.datasets.reduce((sum, dataset) => sum + dataset.data.length, 0)
        }
      };
    } catch (error) {
      return {
        success: false,
        data: new Blob(),
        format: 'csv',
        filename: this.generateFilename('csv'),
        size: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  async exportAsJSON(chartData: ChartData, chartConfig: ChartConfig, metadata?: ExportMetadata): Promise<ExportResult> {
    try {
      const exportData = {
        chartConfig,
        chartData,
        metadata: {
          ...metadata,
          exportDate: new Date().toISOString(),
          version: '1.0'
        }
      };

      const jsonString = JSON.stringify(exportData, null, 2);
      const blob = new Blob([jsonString], { type: 'application/json' });

      return {
        success: true,
        data: blob,
        format: 'json',
        filename: this.generateFilename('json'),
        size: blob.size,
        metadata: {
          ...metadata,
          chartType: chartConfig.type,
          dataPoints: chartData.datasets.reduce((sum, dataset) => sum + dataset.data.length, 0)
        }
      };
    } catch (error) {
      return {
        success: false,
        data: new Blob(),
        format: 'json',
        filename: this.generateFilename('json'),
        size: 0,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }

  getExportTemplates(): ExportTemplate[] {
    return Array.from(this.exportTemplates.values());
  }

  getExportTemplate(id: string): ExportTemplate | undefined {
    return this.exportTemplates.get(id);
  }

  createCustomExportTemplate(name: string, description: string, format: string, options: Partial<ChartExportOptions>): ExportTemplate {
    const template: ExportTemplate = {
      id: `custom-${Date.now()}`,
      name,
      description,
      format,
      options,
      isDefault: false,
      createdAt: new Date()
    };

    this.exportTemplates.set(template.id, template);
    return template;
  }

  downloadExport(result: ExportResult): void {
    if (!result.success || !result.data) {
      console.error('Cannot download failed export:', result.error);
      return;
    }

    // Handle both Blob and string data types
    if (result.data instanceof Blob) {
      const url = URL.createObjectURL(result.data);
      const link = document.createElement('a');
      link.href = url;
      link.download = result.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } else if (typeof result.data === 'string') {
      // For string data (like SVG), create a blob first
      const blob = new Blob([result.data], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = result.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    }
  }

  private generateFilename(format: string): string {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    return `chart-export-${timestamp}.${format}`;
  }

  private async htmlToCanvas(element: HTMLElement, options: ChartExportOptions): Promise<HTMLCanvasElement> {
    // Placeholder implementation - in a real app, you'd use html2canvas or similar
    const canvas = document.createElement('canvas');
    canvas.width = options.width;
    canvas.height = options.height;
    const ctx = canvas.getContext('2d');
    
    if (ctx) {
      ctx.fillStyle = options.backgroundColor;
      ctx.fillRect(0, 0, options.width, options.height);
      ctx.fillStyle = '#000000';
      ctx.font = '16px Arial';
      ctx.fillText('Chart Export', 10, 30);
    }
    
    return canvas;
  }

  private async htmlToSVG(element: HTMLElement, options: ChartExportOptions): Promise<string> {
    // Placeholder implementation - in a real app, you'd convert HTML to SVG
    return `<svg width="${options.width}" height="${options.height}" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="${options.backgroundColor}"/>
      <text x="10" y="30" font-family="Arial" font-size="16" fill="black">Chart Export</text>
    </svg>`;
  }

  private async generatePDF(
    element: HTMLElement,
    options: ChartExportOptions,
    metadata?: ExportMetadata
  ): Promise<Blob> {
    // Placeholder implementation - in a real app, you'd use jsPDF or similar
    const canvas = await this.htmlToCanvas(element, options);
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        if (blob) resolve(blob);
        else resolve(new Blob(['PDF content'], { type: 'application/pdf' }));
      }, 'image/png');
    });
  }

  private async generateExcel(
    chartData: ChartData,
    chartConfig: ChartConfig,
    options: ChartExportOptions,
    metadata?: ExportMetadata
  ): Promise<Blob> {
    // Placeholder implementation - in a real app, you'd use SheetJS or similar
    const csvContent = this.generateCSV(chartData, chartConfig, options);
    return new Blob([csvContent], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
  }

  private generateCSV(chartData: ChartData, chartConfig: ChartConfig, options: ChartExportOptions): string {
    const headers = ['Label', ...chartData.datasets.map(dataset => dataset.label)];
    const rows = chartData.labels.map((label, index) => {
      const row = [label];
      chartData.datasets.forEach(dataset => {
        row.push(dataset.data[index]?.toString() || '');
      });
      return row.join(',');
    });

    return [headers.join(','), ...rows].join('\n');
  }

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  validateExportOptions(options: ChartExportOptions): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (options.width <= 0) {
      errors.push('Width must be greater than 0');
    }

    if (options.height <= 0) {
      errors.push('Height must be greater than 0');
    }

    if (options.dpi < 72 || options.dpi > 600) {
      errors.push('DPI must be between 72 and 600');
    }

    if (!options.backgroundColor) {
      errors.push('Background color is required');
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }
}

export const chartExportService = new ChartExportService();
export default chartExportService;
