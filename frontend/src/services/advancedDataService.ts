/**
 * Advanced Data Processing Service
 * Provides sophisticated data processing, aggregation, and analytics capabilities
 */

import type { RawDataPoint, DataField } from '../components/NextGenReportBuilder/types';

export interface DataAggregation {
  sum: number;
  average: number;
  median: number;
  min: number;
  max: number;
  count: number;
  standardDeviation: number;
  variance: number;
  quartiles: {
    q1: number;
    q2: number;
    q3: number;
  };
  percentiles: {
    p10: number;
    p25: number;
    p50: number;
    p75: number;
    p90: number;
  };
}

export interface TimeSeriesAnalysis {
  trend: 'increasing' | 'decreasing' | 'stable' | 'fluctuating';
  trendStrength: number; // 0-1 scale
  seasonality: boolean;
  seasonalityStrength: number; // 0-1 scale
  forecast: {
    nextValue: number;
    confidence: number;
    trend: number;
  };
}

export interface CorrelationAnalysis {
  correlation: number; // -1 to 1
  strength: 'strong' | 'moderate' | 'weak' | 'none';
  significance: number; // p-value
  relationship: 'positive' | 'negative' | 'none';
}

export interface DataQualityMetrics {
  completeness: number; // 0-1 scale
  accuracy: number; // 0-1 scale
  consistency: number; // 0-1 scale
  validity: number; // 0-1 scale
  uniqueness: number; // 0-1 scale
  overallScore: number; // 0-1 scale
  issues: string[];
  recommendations: string[];
}

export interface AdvancedInsights {
  patterns: string[];
  anomalies: Array<{
    value: number;
    expectedRange: [number, number];
    severity: 'low' | 'medium' | 'high';
    description: string;
  }>;
  trends: Array<{
    field: string;
    direction: 'up' | 'down' | 'stable';
    strength: number;
    confidence: number;
    description: string;
  }>;
  correlations: Array<{
    field1: string;
    field2: string;
    correlation: number;
    strength: string;
    description: string;
  }>;
  recommendations: string[];
}

class AdvancedDataService {
  /**
   * Perform advanced data aggregation with statistical measures
   */
  aggregateData(
    data: RawDataPoint[],
    field: string,
    groupBy?: string
  ): DataAggregation | Record<string, DataAggregation> {
    if (groupBy) {
      return this.aggregateByGroup(data, field, groupBy);
    }

    const values = this.extractNumericValues(data, field);
    return this.calculateAggregation(values);
  }

  /**
   * Analyze time series data for trends and patterns
   */
  analyzeTimeSeries(
    data: RawDataPoint[],
    timeField: string,
    valueField: string
  ): TimeSeriesAnalysis {
    const sortedData = data
      .filter(item => item[timeField] && item[valueField])
      .sort((a, b) => new Date(a[timeField]).getTime() - new Date(b[timeField]).getTime());

    if (sortedData.length < 2) {
      throw new Error('Insufficient data for time series analysis');
    }

    const values = sortedData.map(item => parseFloat(item[valueField]));
    const timestamps = sortedData.map(item => new Date(item[timeField]).getTime());

    const trend = this.calculateTrend(values, timestamps);
    const seasonality = this.detectSeasonality(values);
    const forecast = this.generateForecast(values, trend);

    return {
      trend: this.classifyTrend(trend),
      trendStrength: Math.abs(trend),
      seasonality: seasonality.detected,
      seasonalityStrength: seasonality.strength,
      forecast,
    };
  }

  /**
   * Analyze correlations between multiple fields
   */
  analyzeCorrelations(
    data: RawDataPoint[],
    fields: string[]
  ): CorrelationAnalysis[] {
    const correlations: CorrelationAnalysis[] = [];

    for (let i = 0; i < fields.length; i++) {
      for (let j = i + 1; j < fields.length; j++) {
        const field1 = fields[i];
        const field2 = fields[j];

        const correlation = this.calculateCorrelation(data, field1, field2);
        const significance = this.calculateSignificance(data.length, correlation);

        correlations.push({
          correlation,
          strength: this.classifyCorrelationStrength(Math.abs(correlation)),
          significance,
          relationship: correlation > 0 ? 'positive' : correlation < 0 ? 'negative' : 'none',
        });
      }
    }

    return correlations;
  }

  /**
   * Assess data quality across multiple dimensions
   */
  assessDataQuality(
    data: RawDataPoint[],
    fields: DataField[]
  ): DataQualityMetrics {
    const metrics = {
      completeness: this.calculateCompleteness(data, fields),
      accuracy: this.calculateAccuracy(data, fields),
      consistency: this.calculateConsistency(data, fields),
      validity: this.calculateValidity(data, fields),
      uniqueness: this.calculateUniqueness(data, fields),
    };

    const overallScore = Object.values(metrics).reduce((sum, score) => sum + score, 0) / 5;
    const issues = this.identifyDataQualityIssues(metrics);
    const recommendations = this.generateDataQualityRecommendations(metrics, issues);

    return {
      ...metrics,
      overallScore,
      issues,
      recommendations,
    };
  }

  /**
   * Generate advanced insights from data
   */
  generateAdvancedInsights(
    data: RawDataPoint[],
    fields: DataField[]
  ): AdvancedInsights {
    const patterns = this.detectPatterns(data, fields);
    const anomalies = this.detectAnomalies(data, fields);
    const trends = this.analyzeTrends(data, fields);
    const correlations = this.analyzeCorrelations(data, fields.map(f => f.id));
    const recommendations = this.generateRecommendations(data, fields, patterns, anomalies, trends);

    return {
      patterns,
      anomalies,
      trends,
      correlations: correlations.map(corr => ({
        field1: corr.field1 || '',
        field2: corr.field2 || '',
        correlation: corr.correlation,
        strength: corr.strength,
        description: this.describeCorrelation(corr),
      })),
      recommendations,
    };
  }

  /**
   * Perform advanced filtering with multiple criteria
   */
  advancedFilter(
    data: RawDataPoint[],
    filters: Array<{
      field: string;
      operator: 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'contains' | 'not_contains' | 'between' | 'in';
      value: any;
      value2?: any; // For 'between' operator
    }>
  ): RawDataPoint[] {
    return data.filter(item => {
      return filters.every(filter => {
        const itemValue = item[filter.field];
        
        switch (filter.operator) {
          case 'equals':
            return itemValue === filter.value;
          case 'not_equals':
            return itemValue !== filter.value;
          case 'greater_than':
            return parseFloat(itemValue) > parseFloat(filter.value);
          case 'less_than':
            return parseFloat(itemValue) < parseFloat(filter.value);
          case 'contains':
            return String(itemValue).includes(String(filter.value));
          case 'not_contains':
            return !String(itemValue).includes(String(filter.value));
          case 'between':
            const numValue = parseFloat(itemValue);
            return numValue >= parseFloat(filter.value) && numValue <= parseFloat(filter.value2 || filter.value);
          case 'in':
            return Array.isArray(filter.value) ? filter.value.includes(itemValue) : false;
          default:
            return true;
        }
      });
    });
  }

  /**
   * Perform data transformation operations
   */
  transformData(
    data: RawDataPoint[],
    transformations: Array<{
      field: string;
      operation: 'normalize' | 'standardize' | 'log' | 'sqrt' | 'square' | 'round' | 'floor' | 'ceil';
      newField?: string;
    }>
  ): RawDataPoint[] {
    return data.map(item => {
      const transformed = { ...item };
      
      transformations.forEach(transform => {
        const value = parseFloat(item[transform.field]);
        if (isNaN(value)) return;

        let result: number;
        switch (transform.operation) {
          case 'normalize':
            result = this.normalizeValue(value, data, transform.field);
            break;
          case 'standardize':
            result = this.standardizeValue(value, data, transform.field);
            break;
          case 'log':
            result = Math.log(Math.max(value, 0.0001));
            break;
          case 'sqrt':
            result = Math.sqrt(Math.max(value, 0));
            break;
          case 'square':
            result = value * value;
            break;
          case 'round':
            result = Math.round(value);
            break;
          case 'floor':
            result = Math.floor(value);
            break;
          case 'ceil':
            result = Math.ceil(value);
            break;
          default:
            result = value;
        }

        const targetField = transform.newField || transform.field;
        transformed[targetField] = result;
      });

      return transformed;
    });
  }

  // Private helper methods
  private extractNumericValues(data: RawDataPoint[], field: string): number[] {
    return data
      .map(item => parseFloat(item[field]))
      .filter(value => !isNaN(value));
  }

  private calculateAggregation(values: number[]): DataAggregation {
    if (values.length === 0) {
      throw new Error('No valid numeric values found');
    }

    const sorted = values.sort((a, b) => a - b);
    const sum = values.reduce((acc, val) => acc + val, 0);
    const average = sum / values.length;
    const median = sorted[Math.floor(sorted.length / 2)];
    const min = Math.min(...values);
    const max = Math.max(...values);
    const variance = values.reduce((acc, val) => acc + Math.pow(val - average, 2), 0) / values.length;
    const standardDeviation = Math.sqrt(variance);

    return {
      sum,
      average,
      median,
      min,
      max,
      count: values.length,
      standardDeviation,
      variance,
      quartiles: {
        q1: sorted[Math.floor(sorted.length * 0.25)],
        q2: median,
        q3: sorted[Math.floor(sorted.length * 0.75)],
      },
      percentiles: {
        p10: sorted[Math.floor(sorted.length * 0.1)],
        p25: sorted[Math.floor(sorted.length * 0.25)],
        p50: median,
        p75: sorted[Math.floor(sorted.length * 0.75)],
        p90: sorted[Math.floor(sorted.length * 0.9)],
      },
    };
  }

  private aggregateByGroup(
    data: RawDataPoint[],
    field: string,
    groupBy: string
  ): Record<string, DataAggregation> {
    const groups: Record<string, RawDataPoint[]> = {};
    
    data.forEach(item => {
      const groupKey = String(item[groupBy]);
      if (!groups[groupKey]) {
        groups[groupKey] = [];
      }
      groups[groupKey].push(item);
    });

    const result: Record<string, DataAggregation> = {};
    Object.entries(groups).forEach(([groupKey, groupData]) => {
      const values = this.extractNumericValues(groupData, field);
      if (values.length > 0) {
        result[groupKey] = this.calculateAggregation(values);
      }
    });

    return result;
  }

  private calculateTrend(values: number[], timestamps: number[]): number {
    const n = values.length;
    const xMean = timestamps.reduce((sum, t) => sum + t, 0) / n;
    const yMean = values.reduce((sum, v) => sum + v, 0) / n;

    let numerator = 0;
    let denominator = 0;

    for (let i = 0; i < n; i++) {
      numerator += (timestamps[i] - xMean) * (values[i] - yMean);
      denominator += Math.pow(timestamps[i] - xMean, 2);
    }

    return denominator === 0 ? 0 : numerator / denominator;
  }

  private detectSeasonality(values: number[]): { detected: boolean; strength: number } {
    // Simple seasonality detection using autocorrelation
    if (values.length < 12) {
      return { detected: false, strength: 0 };
    }

    const autocorr = this.calculateAutocorrelation(values, 1);
    return {
      detected: autocorr > 0.3,
      strength: Math.min(autocorr, 1),
    };
  }

  private calculateAutocorrelation(values: number[], lag: number): number {
    const n = values.length;
    if (lag >= n) return 0;

    const mean = values.reduce((sum, val) => sum + val, 0) / n;
    const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / n;

    if (variance === 0) return 0;

    let numerator = 0;
    for (let i = 0; i < n - lag; i++) {
      numerator += (values[i] - mean) * (values[i + lag] - mean);
    }

    return numerator / ((n - lag) * variance);
  }

  private generateForecast(values: number[], trend: number): { nextValue: number; confidence: number; trend: number } {
    const lastValue = values[values.length - 1];
    const nextValue = lastValue + trend;
    const confidence = Math.max(0.1, 1 - Math.abs(trend) / Math.max(...values));
    
    return {
      nextValue,
      confidence: Math.min(confidence, 0.95),
      trend,
    };
  }

  private classifyTrend(trend: number): 'increasing' | 'decreasing' | 'stable' | 'fluctuating' {
    if (Math.abs(trend) < 0.01) return 'stable';
    if (trend > 0.1) return 'increasing';
    if (trend < -0.1) return 'decreasing';
    return 'fluctuating';
  }

  private calculateCorrelation(data: RawDataPoint[], field1: string, field2: string): number {
    const pairs = data
      .filter(item => item[field1] && item[field2])
      .map(item => ({
        x: parseFloat(item[field1]),
        y: parseFloat(item[field2]),
      }))
      .filter(pair => !isNaN(pair.x) && !isNaN(pair.y));

    if (pairs.length < 2) return 0;

    const n = pairs.length;
    const sumX = pairs.reduce((sum, pair) => sum + pair.x, 0);
    const sumY = pairs.reduce((sum, pair) => sum + pair.y, 0);
    const sumXY = pairs.reduce((sum, pair) => sum + pair.x * pair.y, 0);
    const sumX2 = pairs.reduce((sum, pair) => sum + pair.x * pair.x, 0);
    const sumY2 = pairs.reduce((sum, pair) => sum + pair.y * pair.y, 0);

    const numerator = n * sumXY - sumX * sumY;
    const denominator = Math.sqrt((n * sumX2 - sumX * sumX) * (n * sumY2 - sumY * sumY));

    return denominator === 0 ? 0 : numerator / denominator;
  }

  private calculateSignificance(n: number, correlation: number): number {
    // Simplified significance calculation
    const t = correlation * Math.sqrt((n - 2) / (1 - correlation * correlation));
    return Math.exp(-Math.abs(t) / 10); // Approximate p-value
  }

  private classifyCorrelationStrength(correlation: number): 'strong' | 'moderate' | 'weak' | 'none' {
    if (correlation >= 0.7) return 'strong';
    if (correlation >= 0.3) return 'moderate';
    if (correlation >= 0.1) return 'weak';
    return 'none';
  }

  private calculateCompleteness(data: RawDataPoint[], fields: DataField[]): number {
    let totalFields = 0;
    let filledFields = 0;

    data.forEach(item => {
      fields.forEach(field => {
        totalFields++;
        if (item[field.id] !== undefined && item[field.id] !== null && item[field.id] !== '') {
          filledFields++;
        }
      });
    });

    return totalFields === 0 ? 0 : filledFields / totalFields;
  }

  private calculateAccuracy(data: RawDataPoint[], fields: DataField[]): number {
    // Simplified accuracy calculation - in production this would use validation rules
    return 0.95; // Placeholder
  }

  private calculateConsistency(data: RawDataPoint[], fields: DataField[]): number {
    // Simplified consistency calculation
    return 0.9; // Placeholder
  }

  private calculateValidity(data: RawDataPoint[], fields: DataField[]): number {
    // Simplified validity calculation
    return 0.92; // Placeholder
  }

  private calculateUniqueness(data: RawDataPoint[], fields: DataField[]): number {
    const totalRecords = data.length;
    const uniqueRecords = new Set(data.map(item => JSON.stringify(item))).size;
    return totalRecords === 0 ? 0 : uniqueRecords / totalRecords;
  }

  private identifyDataQualityIssues(metrics: Partial<DataQualityMetrics>): string[] {
    const issues: string[] = [];
    
    if (metrics.completeness && metrics.completeness < 0.8) {
      issues.push('Low data completeness detected');
    }
    if (metrics.accuracy && metrics.accuracy < 0.9) {
      issues.push('Data accuracy concerns identified');
    }
    if (metrics.consistency && metrics.consistency < 0.85) {
      issues.push('Data consistency issues found');
    }
    
    return issues;
  }

  private generateDataQualityRecommendations(
    metrics: Partial<DataQualityMetrics>,
    issues: string[]
  ): string[] {
    const recommendations: string[] = [];
    
    if (metrics.completeness && metrics.completeness < 0.8) {
      recommendations.push('Implement data validation rules to ensure required fields are populated');
    }
    if (metrics.accuracy && metrics.accuracy < 0.9) {
      recommendations.push('Add data quality checks and validation workflows');
    }
    if (metrics.consistency && metrics.consistency < 0.85) {
      recommendations.push('Standardize data formats and implement data governance policies');
    }
    
    return recommendations;
  }

  private detectPatterns(data: RawDataPoint[], fields: DataField[]): string[] {
    const patterns: string[] = [];
    
    // Detect common patterns
    if (data.length > 10) {
      patterns.push('Sufficient data volume for pattern analysis');
    }
    
    // Add more pattern detection logic here
    return patterns;
  }

  private detectAnomalies(data: RawDataPoint[], fields: DataField[]): Array<{
    value: number;
    expectedRange: [number, number];
    severity: 'low' | 'medium' | 'high';
    description: string;
  }> {
    const anomalies: Array<{
      value: number;
      expectedRange: [number, number];
      severity: 'low' | 'medium' | 'high';
      description: string;
    }> = [];
    
    // Simplified anomaly detection
    fields.forEach(field => {
      if (field.dataType === 'numerical') {
        const values = this.extractNumericValues(data, field.id);
        if (values.length > 0) {
          const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
          const stdDev = Math.sqrt(
            values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
          );
          
          values.forEach(value => {
            const zScore = Math.abs((value - mean) / stdDev);
            if (zScore > 3) {
              anomalies.push({
                value,
                expectedRange: [mean - 2 * stdDev, mean + 2 * stdDev],
                severity: zScore > 4 ? 'high' : zScore > 3.5 ? 'medium' : 'low',
                description: `Outlier detected in ${field.name} field`,
              });
            }
          });
        }
      }
    });
    
    return anomalies;
  }

  private analyzeTrends(data: RawDataPoint[], fields: DataField[]): Array<{
    field: string;
    direction: 'up' | 'down' | 'stable';
    strength: number;
    confidence: number;
    description: string;
  }> {
    const trends: Array<{
      field: string;
      direction: 'up' | 'down' | 'stable';
      strength: number;
      confidence: number;
      description: string;
    }> = [];
    
    fields.forEach(field => {
      if (field.dataType === 'numerical') {
        const values = this.extractNumericValues(data, field.id);
        if (values.length > 5) {
          const trend = this.calculateTrend(values, Array.from({ length: values.length }, (_, i) => i));
          const direction = trend > 0.01 ? 'up' : trend < -0.01 ? 'down' : 'stable';
          const strength = Math.min(Math.abs(trend), 1);
          const confidence = Math.max(0.1, 1 - Math.abs(trend) / Math.max(...values));
          
          trends.push({
            field: field.name,
            direction,
            strength,
            confidence: Math.min(confidence, 0.95),
            description: `${field.name} shows ${direction} trend with ${(strength * 100).toFixed(1)}% strength`,
          });
        }
      }
    });
    
    return trends;
  }

  private generateRecommendations(
    data: RawDataPoint[],
    fields: DataField[],
    patterns: string[],
    anomalies: Array<any>,
    trends: Array<any>
  ): string[] {
    const recommendations: string[] = [];
    
    if (anomalies.length > 0) {
      recommendations.push('Review and investigate detected anomalies for data quality improvement');
    }
    
    if (trends.some(t => t.direction === 'up' && t.strength > 0.5)) {
      recommendations.push('Strong upward trends detected - consider trend analysis for forecasting');
    }
    
    if (data.length < 100) {
      recommendations.push('Consider collecting more data for more robust statistical analysis');
    }
    
    return recommendations;
  }

  private describeCorrelation(corr: any): string {
    const strength = corr.strength;
    const relationship = corr.relationship;
    
    if (strength === 'strong') {
      return `Strong ${relationship} correlation detected`;
    } else if (strength === 'moderate') {
      return `Moderate ${relationship} correlation observed`;
    } else if (strength === 'weak') {
      return `Weak ${relationship} correlation found`;
    } else {
      return 'No significant correlation detected';
    }
  }

  private normalizeValue(value: number, data: RawDataPoint[], field: string): number {
    const values = this.extractNumericValues(data, field);
    const min = Math.min(...values);
    const max = Math.max(...values);
    return max === min ? 0 : (value - min) / (max - min);
  }

  private standardizeValue(value: number, data: RawDataPoint[], field: string): number {
    const values = this.extractNumericValues(data, field);
    const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
    const stdDev = Math.sqrt(
      values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / values.length
    );
    return stdDev === 0 ? 0 : (value - mean) / stdDev;
  }
}

export const advancedDataService = new AdvancedDataService();
export default advancedDataService;
