/**
 * Advanced Chart Service
 * Handles advanced chart types, 3D visualizations, and specialized chart configurations
 */
import type { ChartData, ChartConfig } from '../components/NextGenReportBuilder/types';

export interface AdvancedChartConfig extends ChartConfig {
  // 3D Chart Options
  threeD?: {
    enabled: boolean;
    rotationX: number;
    rotationY: number;
    rotationZ: number;
    depth: number;
    perspective: number;
  };
  
  // Heatmap Options
  heatmap?: {
    colorScale: 'viridis' | 'plasma' | 'inferno' | 'magma' | 'coolwarm' | 'rainbow';
    minValue: number;
    maxValue: number;
    showValues: boolean;
    cellPadding: number;
  };
  
  // Radar Chart Options
  radar?: {
    fillArea: boolean;
    pointRadius: number;
    lineTension: number;
    scaleStart: number;
    scaleEnd: number;
    showScaleLabels: boolean;
  };
  
  // Bubble Chart Options
  bubble?: {
    minRadius: number;
    maxRadius: number;
    showLabels: boolean;
    labelThreshold: number;
  };
  
  // Scatter Plot Options
  scatter?: {
    pointShape: 'circle' | 'square' | 'triangle' | 'diamond' | 'cross';
    pointSize: number;
    showTrendLine: boolean;
    trendLineType: 'linear' | 'polynomial' | 'exponential';
    trendLineColor: string;
  };
  
  // Area Chart Options
  area?: {
    fillOpacity: number;
    gradient: boolean;
    gradientColors: string[];
    showBoundaries: boolean;
  };
  
  // Candlestick Options
  candlestick?: {
    upColor: string;
    downColor: string;
    wickColor: string;
    borderColor: string;
    showVolume: boolean;
  };
  
  // Gantt Chart Options
  gantt?: {
    showProgress: boolean;
    showDependencies: boolean;
    milestoneColor: string;
    criticalPathColor: string;
  };
}

export interface ChartTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  config: AdvancedChartConfig;
  thumbnail?: string;
  tags: string[];
  usageCount: number;
  rating: number;
}

export interface ChartPreset {
  id: string;
  name: string;
  description: string;
  category: string;
  config: Partial<AdvancedChartConfig>;
  isDefault: boolean;
  isCustom: boolean;
  createdBy?: string;
  createdAt: Date;
  lastUsed?: Date;
}

export interface ChartExportOptions {
  format: 'png' | 'svg' | 'pdf' | 'excel' | 'csv' | 'json';
  width: number;
  height: number;
  dpi: number;
  backgroundColor: string;
  includeLegend: boolean;
  includeTitle: boolean;
  includeData: boolean;
  watermark?: string;
  metadata?: Record<string, any>;
}

export interface ChartAnimation {
  duration: number;
  easing: 'linear' | 'easeIn' | 'easeOut' | 'easeInOut';
  delay: number;
  loop: boolean;
  direction: 'normal' | 'reverse' | 'alternate' | 'alternate-reverse';
}

class AdvancedChartService {
  private chartTemplates: Map<string, ChartTemplate> = new Map();
  private chartPresets: Map<string, ChartPreset> = new Map();
  private customPresets: Map<string, ChartPreset> = new Map();

  constructor() {
    this.initializeDefaultTemplates();
    this.initializeDefaultPresets();
  }

  private initializeDefaultTemplates(): void {
    const defaultTemplates: ChartTemplate[] = [
      {
        id: '3d-bar',
        name: '3D Bar Chart',
        description: 'Three-dimensional bar chart with rotation controls',
        category: '3D Charts',
        config: {
          type: 'bar',
          title: '3D Bar Chart',
          threeD: {
            enabled: true,
            rotationX: 15,
            rotationY: 15,
            rotationZ: 0,
            depth: 50,
            perspective: 1000
          }
        },
        thumbnail: '/templates/3d-bar.png',
        tags: ['3D', 'bar', 'interactive'],
        usageCount: 0,
        rating: 4.5
      },
      {
        id: 'heatmap-basic',
        name: 'Basic Heatmap',
        description: 'Color-coded matrix visualization',
        category: 'Heatmaps',
        config: {
          type: 'bar', // Using bar as base type for heatmap
          title: 'Heatmap Chart',
          heatmap: {
            colorScale: 'viridis',
            minValue: 0,
            maxValue: 100,
            showValues: true,
            cellPadding: 2
          }
        },
        thumbnail: '/templates/heatmap.png',
        tags: ['heatmap', 'matrix', 'color-coded'],
        usageCount: 0,
        rating: 4.2
      },
      {
        id: 'radar-multi',
        name: 'Multi-Series Radar',
        description: 'Radar chart with multiple data series',
        category: 'Radar Charts',
        config: {
          type: 'line', // Using line as base type for radar
          title: 'Radar Chart',
          radar: {
            fillArea: true,
            pointRadius: 4,
            lineTension: 0.4,
            scaleStart: 0,
            scaleEnd: 100,
            showScaleLabels: true
          }
        },
        thumbnail: '/templates/radar.png',
        tags: ['radar', 'spider', 'multi-series'],
        usageCount: 0,
        rating: 4.0
      }
    ];

    defaultTemplates.forEach(template => {
      this.chartTemplates.set(template.id, template);
    });
  }

  private initializeDefaultPresets(): void {
    const defaultPresets: ChartPreset[] = [
      {
        id: 'bubble-basic',
        name: 'Basic Bubble Chart',
        description: 'Simple bubble chart with size encoding',
        category: 'Bubble Charts',
        config: {
          type: 'bubble',
          title: 'Bubble Chart',
          bubble: {
            minRadius: 5,
            maxRadius: 20,
            showLabels: true,
            labelThreshold: 15
          }
        },
        isDefault: true,
        isCustom: false,
        createdAt: new Date()
      },
      {
        id: 'scatter-trend',
        name: 'Scatter with Trend Line',
        description: 'Scatter plot with trend line analysis',
        category: 'Scatter Plots',
        config: {
          type: 'scatter',
          title: 'Scatter Plot with Trend',
          scatter: {
            pointShape: 'circle',
            pointSize: 6,
            showTrendLine: true,
            trendLineType: 'linear',
            trendLineColor: '#ff6b6b'
          }
        },
        isDefault: true,
        isCustom: false,
        createdAt: new Date()
      },
      {
        id: 'area-gradient',
        name: 'Gradient Area Chart',
        description: 'Area chart with gradient fill',
        category: 'Area Charts',
        config: {
          type: 'area',
          title: 'Gradient Area Chart',
          area: {
            fillOpacity: 0.7,
            gradient: true,
            gradientColors: ['#4facfe', '#00f2fe'],
            showBoundaries: true
          }
        },
        isDefault: true,
        isCustom: false,
        createdAt: new Date()
      }
    ];

    defaultPresets.forEach(preset => {
      this.chartPresets.set(preset.id, preset);
    });
  }

  getChartTemplates(): ChartTemplate[] {
    return Array.from(this.chartTemplates.values());
  }

  getChartTemplate(id: string): ChartTemplate | undefined {
    return this.chartTemplates.get(id);
  }

  getChartTemplatesByCategory(category: string): ChartTemplate[] {
    return Array.from(this.chartTemplates.values())
      .filter(template => template.category === category);
  }

  getChartPresets(): ChartPreset[] {
    return Array.from(this.chartPresets.values());
  }

  getChartPreset(id: string): ChartPreset | undefined {
    return this.chartPresets.get(id);
  }

  createCustomPreset(name: string, description: string, config: Partial<AdvancedChartConfig>): ChartPreset {
    const preset: ChartPreset = {
      id: `custom-${Date.now()}`,
      name,
      description,
      category: 'Custom',
      config,
      isDefault: false,
      isCustom: true,
      createdAt: new Date()
    };

    this.customPresets.set(preset.id, preset);
    return preset;
  }

  updateTemplateUsage(templateId: string): void {
    const template = this.chartTemplates.get(templateId);
    if (template) {
      template.usageCount++;
    }
  }

  rateTemplate(templateId: string, rating: number): void {
    const template = this.chartTemplates.get(templateId);
    if (template && rating >= 1 && rating <= 5) {
      template.rating = rating;
    }
  }

  searchTemplates(query: string, category?: string): ChartTemplate[] {
    const templates = Array.from(this.chartTemplates.values());
    return templates.filter(template => {
      const matchesQuery = template.name.toLowerCase().includes(query.toLowerCase()) ||
                          template.description.toLowerCase().includes(query.toLowerCase()) ||
                          template.tags.some(tag => tag.toLowerCase().includes(query.toLowerCase()));
      
      const matchesCategory = !category || template.category === category;
      
      return matchesQuery && matchesCategory;
    });
  }

  getPopularTemplates(limit: number = 10): ChartTemplate[] {
    return Array.from(this.chartTemplates.values())
      .sort((a, b) => b.usageCount - a.usageCount)
      .slice(0, limit);
  }

  getHighlyRatedTemplates(limit: number = 10): ChartTemplate[] {
    return Array.from(this.chartTemplates.values())
      .sort((a, b) => b.rating - a.rating)
      .slice(0, limit);
  }

  validateChartConfig(config: AdvancedChartConfig): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!config.title || config.title.trim() === '') {
      errors.push('Chart title is required');
    }

    if (!config.type) {
      errors.push('Chart type is required');
    }

    if (config.threeD?.enabled) {
      if (config.threeD.rotationX < -180 || config.threeD.rotationX > 180) {
        errors.push('3D rotation X must be between -180 and 180 degrees');
      }
      if (config.threeD.rotationY < -180 || config.threeD.rotationY > 180) {
        errors.push('3D rotation Y must be between -180 and 180 degrees');
      }
      if (config.threeD.rotationZ < -180 || config.threeD.rotationZ > 180) {
        errors.push('3D rotation Z must be between -180 and 180 degrees');
      }
    }

    if (config.heatmap) {
      if (config.heatmap.minValue >= config.heatmap.maxValue) {
        errors.push('Heatmap min value must be less than max value');
      }
    }

    return {
      isValid: errors.length === 0,
      errors
    };
  }

  generateSampleData(chartType: string, dataPoints: number = 50): ChartData {
    switch (chartType) {
      case '3d':
        return this.generate3DData(dataPoints);
      case 'heatmap':
        return this.generateHeatmapData(dataPoints);
      case 'radar':
        return this.generateRadarData(dataPoints);
      case 'bubble':
        return this.generateBubbleData(dataPoints);
      case 'scatter':
        return this.generateScatterData(dataPoints);
      case 'area':
        return this.generateAreaData(dataPoints);
      case 'candlestick':
        return this.generateCandlestickData(dataPoints);
      case 'gantt':
        return this.generateGanttData(dataPoints);
      default:
        return this.generateBasicData(dataPoints);
    }
  }

  private generate3DData(dataPoints: number): ChartData {
    const labels = Array.from({ length: dataPoints }, (_, i) => `Point ${i + 1}`);
    const datasets = [
      {
        label: 'X Axis',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)'
      },
      {
        label: 'Y Axis',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(255, 99, 132, 0.6)',
        borderColor: 'rgba(255, 99, 132, 1)'
      },
      {
        label: 'Z Axis',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)'
      }
    ];

    return { labels, datasets };
  }

  private generateHeatmapData(dataPoints: number): ChartData {
    const size = Math.ceil(Math.sqrt(dataPoints));
    const labels = Array.from({ length: size }, (_, i) => `Row ${i + 1}`);
    const datasets = [
      {
        label: 'Heatmap Values',
        data: Array.from({ length: size * size }, () => Math.random() * 100),
        backgroundColor: 'rgba(255, 99, 132, 0.6)',
        borderColor: 'rgba(255, 99, 132, 1)'
      }
    ];

    return { labels, datasets };
  }

  private generateRadarData(dataPoints: number): ChartData {
    const labels = Array.from({ length: dataPoints }, (_, i) => `Dimension ${i + 1}`);
    const datasets = [
      {
        label: 'Series 1',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        fill: true
      },
      {
        label: 'Series 2',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)',
        fill: true
      }
    ];

    return { labels, datasets };
  }

  private generateBubbleData(dataPoints: number): ChartData {
    const labels = Array.from({ length: dataPoints }, (_, i) => `Bubble ${i + 1}`);
    const datasets = [
      {
        label: 'Bubble Dataset',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)'
      }
    ];

    return { labels, datasets };
  }

  private generateScatterData(dataPoints: number): ChartData {
    const labels = Array.from({ length: dataPoints }, (_, i) => `Point ${i + 1}`);
    const datasets = [
      {
        label: 'Scatter Dataset',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(255, 159, 64, 0.6)',
        borderColor: 'rgba(255, 159, 64, 1)'
      }
    ];

    return { labels, datasets };
  }

  private generateAreaData(dataPoints: number): ChartData {
    const labels = Array.from({ length: dataPoints }, (_, i) => `Point ${i + 1}`);
    const datasets = [
      {
        label: 'Area Dataset',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(153, 102, 255, 0.6)',
        borderColor: 'rgba(153, 102, 255, 1)',
        fill: true
      }
    ];

    return { labels, datasets };
  }

  private generateCandlestickData(dataPoints: number): ChartData {
    const labels = Array.from({ length: dataPoints }, (_, i) => `Day ${i + 1}`);
    const datasets = [
      {
        label: 'Candlestick Dataset',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(255, 205, 86, 0.6)',
        borderColor: 'rgba(255, 205, 86, 1)'
      }
    ];

    return { labels, datasets };
  }

  private generateGanttData(dataPoints: number): ChartData {
    const labels = Array.from({ length: dataPoints }, (_, i) => `Task ${i + 1}`);
    const datasets = [
      {
        label: 'Gantt Dataset',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(201, 203, 207, 0.6)',
        borderColor: 'rgba(201, 203, 207, 1)'
      }
    ];

    return { labels, datasets };
  }

  private generateBasicData(dataPoints: number): ChartData {
    const labels = Array.from({ length: dataPoints }, (_, i) => `Point ${i + 1}`);
    const datasets = [
      {
        label: 'Dataset 1',
        data: Array.from({ length: dataPoints }, () => Math.random() * 100),
        backgroundColor: 'rgba(54, 162, 235, 0.6)',
        borderColor: 'rgba(54, 162, 235, 1)'
      }
    ];

    return { labels, datasets };
  }
}

export const advancedChartService = new AdvancedChartService();
export default advancedChartService;
