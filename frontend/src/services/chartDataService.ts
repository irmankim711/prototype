/**
 * Chart Data Service
 * Processes raw data and transforms it into chart-ready data structures
 */

import type { ChartData, ChartConfig, DataField, RawDataPoint } from '../components/NextGenReportBuilder/types';

export interface ProcessedData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
  }[];
  metadata: {
    totalRecords: number;
    uniqueValues: number;
    dataRange: {
      min: number;
      max: number;
      average: number;
    };
  };
}

class ChartDataService {
  /**
   * Process raw data into chart-ready format
   */
  processDataForChart(
    rawData: RawDataPoint[],
    config: ChartConfig,
    fields: DataField[]
  ): ChartData {
    if (!rawData || rawData.length === 0) {
      throw new Error('No data provided for chart processing');
    }

    if (!config.xAxis?.field || !config.yAxis?.field) {
      throw new Error('Chart configuration missing axis mappings');
    }

    const xField = fields.find(f => f.id === config.xAxis?.field);
    const yField = fields.find(f => f.id === config.yAxis?.field);

    if (!xField || !yField) {
      throw new Error('Required fields not found in data schema');
    }

    // Extract unique X-axis values and sort them
    const xValues = this.extractUniqueValues(rawData, config.xAxis.field, xField.dataType);
    
    // Process data based on chart type
    switch (config.type) {
      case 'bar':
      case 'line':
      case 'area':
        return this.processBarLineData(rawData, config, xValues, yField);
      case 'pie':
      case 'doughnut':
        return this.processPieData(rawData, config, xField, yField);
      case 'scatter':
        return this.processScatterData(rawData, config, xField, yField);
      default:
        return this.processBarLineData(rawData, config, xValues, yField);
    }
  }

  /**
   * Process data for bar, line, and area charts
   */
  private processBarLineData(
    rawData: RawDataPoint[],
    config: ChartConfig,
    xValues: string[],
    yField: DataField
  ): ChartData {
    const dataset = {
      label: yField.name,
      data: xValues.map(xValue => {
        const matchingData = rawData.filter(item => 
          String(item[config.xAxis!.field]) === xValue
        );
        
        if (yField.dataType === 'numerical') {
          return matchingData.reduce((sum, item) => {
            const value = parseFloat(item[config.yAxis!.field]);
            return sum + (isNaN(value) ? 0 : value);
          }, 0);
        } else {
          return matchingData.length;
        }
      }),
    };

    return {
      labels: xValues,
      datasets: [dataset],
    };
  }

  /**
   * Process data for pie and doughnut charts
   */
  private processPieData(
    rawData: RawDataPoint[],
    config: ChartConfig,
    xField: DataField,
    yField: DataField
  ): ChartData {
    const aggregatedData = this.aggregateDataByCategory(
      rawData,
      config.xAxis!.field,
      config.yAxis!.field,
      yField.dataType
    );

    return {
      labels: Object.keys(aggregatedData),
      datasets: [{
        label: yField.name,
        data: Object.values(aggregatedData),
      }],
    };
  }

  /**
   * Process data for scatter plots
   */
  private processScatterData(
    rawData: RawDataPoint[],
    config: ChartConfig,
    xField: DataField,
    yField: DataField
  ): ChartData {
    const validData = rawData.filter(item => {
      const xValue = parseFloat(item[config.xAxis!.field]);
      const yValue = parseFloat(item[config.yAxis!.field]);
      return !isNaN(xValue) && !isNaN(yValue);
    });

    return {
      labels: validData.map(item => String(item[config.xAxis!.field])),
      datasets: [{
        label: `${yField.name} vs ${xField.name}`,
        data: validData.map(item => parseFloat(item[config.yAxis!.field])),
      }],
    };
  }

  /**
   * Extract unique values for X-axis with proper sorting
   */
  private extractUniqueValues(
    rawData: RawDataPoint[],
    fieldId: string,
    dataType: string
  ): string[] {
    const values = [...new Set(rawData.map(item => String(item[fieldId])))];
    
    if (dataType === 'temporal') {
      // Sort temporal data chronologically
      return values.sort((a, b) => new Date(a).getTime() - new Date(b).getTime());
    } else if (dataType === 'numerical') {
      // Sort numerical data numerically
      return values.sort((a, b) => parseFloat(a) - parseFloat(b));
    } else {
      // Sort categorical data alphabetically
      return values.sort();
    }
  }

  /**
   * Aggregate data by category for pie charts
   */
  private aggregateDataByCategory(
    rawData: RawDataPoint[],
    categoryField: string,
    valueField: string,
    valueType: string
  ): Record<string, number> {
    const aggregated: Record<string, number> = {};

    rawData.forEach(item => {
      const category = String(item[categoryField]);
      const value = valueType === 'numerical' 
        ? parseFloat(item[valueField]) || 0
        : 1; // Count for non-numerical values

      aggregated[category] = (aggregated[category] || 0) + value;
    });

    return aggregated;
  }

  /**
   * Generate sample data for testing and development
   */
  generateSampleData(config: ChartConfig): ChartData {
    const sampleLabels = ['Q1', 'Q2', 'Q3', 'Q4'];
    const sampleData = [85000, 92000, 78000, 96000];

    return {
      labels: sampleLabels,
      datasets: [{
        label: config.yAxis?.label || 'Sample Data',
        data: sampleData,
        backgroundColor: this.getDefaultColors(1),
        borderColor: this.getDefaultColors(1),
      }],
    };
  }

  /**
   * Get default color palette
   */
  private getDefaultColors(count: number): string[] {
    const colors = [
      '#2563eb', '#10b981', '#f59e0b', '#ef4444',
      '#8b5cf6', '#06b6d4', '#84cc16', '#f97316'
    ];
    
    return Array.from({ length: count }, (_, i) => colors[i % colors.length]);
  }

  /**
   * Validate chart configuration
   */
  validateChartConfig(config: ChartConfig, fields: DataField[]): string[] {
    const errors: string[] = [];

    if (!config.title) {
      errors.push('Chart title is required');
    }

    if (!config.xAxis?.field) {
      errors.push('X-axis field is required');
    }

    if (!config.yAxis?.field) {
      errors.push('Y-axis field is required');
    }

    if (config.xAxis?.field && config.yAxis?.field) {
      const xField = fields.find(f => f.id === config.xAxis?.field);
      const yField = fields.find(f => f.id === config.yAxis?.field);

      if (!xField) {
        errors.push('X-axis field not found in data schema');
      }

      if (!yField) {
        errors.push('Y-axis field not found in data schema');
      }

      if (xField && yField) {
        if (config.type === 'pie' || config.type === 'doughnut') {
          if (xField.type !== 'dimension') {
            errors.push('Pie/doughnut charts require dimension field for X-axis');
          }
          if (yField.type !== 'measure') {
            errors.push('Pie/doughnut charts require measure field for Y-axis');
          }
        }

        if (config.type === 'scatter') {
          if (xField.type !== 'measure' || yField.type !== 'measure') {
            errors.push('Scatter plots require measure fields for both axes');
          }
        }
      }
    }

    return errors;
  }

  /**
   * Get data statistics for insights
   */
  getDataInsights(
    rawData: RawDataPoint[],
    config: ChartConfig,
    fields: DataField[]
  ): any {
    if (!rawData || rawData.length === 0) {
      return null;
    }

    const xField = fields.find(f => f.id === config.xAxis?.field);
    const yField = fields.find(f => f.id === config.yAxis?.field);

    if (!xField || !yField) {
      return null;
    }

    const yValues = rawData
      .map(item => parseFloat(item[config.yAxis!.field]))
      .filter(value => !isNaN(value));

    if (yValues.length === 0) {
      return null;
    }

    const sortedValues = yValues.sort((a, b) => a - b);
    const sum = yValues.reduce((acc, val) => acc + val, 0);
    const average = sum / yValues.length;
    const median = sortedValues[Math.floor(sortedValues.length / 2)];

    return {
      totalRecords: rawData.length,
      validRecords: yValues.length,
      dataRange: {
        min: Math.min(...yValues),
        max: Math.max(...yValues),
        average: Math.round(average * 100) / 100,
        median: Math.round(median * 100) / 100,
      },
      distribution: {
        quartiles: {
          q1: sortedValues[Math.floor(sortedValues.length * 0.25)],
          q2: median,
          q3: sortedValues[Math.floor(sortedValues.length * 0.75)],
        },
        standardDeviation: this.calculateStandardDeviation(yValues, average),
      },
      suggestions: this.generateDataSuggestions(config, yValues, average),
    };
  }

  /**
   * Calculate standard deviation
   */
  private calculateStandardDeviation(values: number[], mean: number): number {
    const variance = values.reduce((acc, val) => acc + Math.pow(val - mean, 2), 0) / values.length;
    return Math.sqrt(variance);
  }

  /**
   * Generate data insights and suggestions
   */
  private generateDataSuggestions(config: ChartConfig, values: number[], average: number): string[] {
    const suggestions: string[] = [];
    const variance = values.reduce((acc, val) => acc + Math.pow(val - average, 2), 0) / values.length;
    const stdDev = Math.sqrt(variance);
    const coefficientOfVariation = (stdDev / average) * 100;

    if (coefficientOfVariation > 50) {
      suggestions.push('High data variability detected. Consider using log scale or filtering outliers.');
    }

    if (config.type === 'line' && values.length > 10) {
      const trend = this.calculateTrend(values);
      if (Math.abs(trend) > 0.1) {
        suggestions.push(`Strong ${trend > 0 ? 'upward' : 'downward'} trend detected in the data.`);
      }
    }

    if (values.length < 5) {
      suggestions.push('Limited data points. Consider collecting more data for better insights.');
    }

    return suggestions;
  }

  /**
   * Calculate trend in time series data
   */
  private calculateTrend(values: number[]): number {
    const n = values.length;
    const xMean = (n - 1) / 2;
    const yMean = values.reduce((sum, val) => sum + val, 0) / n;

    let numerator = 0;
    let denominator = 0;

    for (let i = 0; i < n; i++) {
      numerator += (i - xMean) * (values[i] - yMean);
      denominator += Math.pow(i - xMean, 2);
    }

    return denominator === 0 ? 0 : numerator / denominator;
  }
}

export const chartDataService = new ChartDataService();
export default chartDataService;
