/**
 * Chart Types and Interfaces
 * Centralized type definitions for chart components
 */

import React from 'react';

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
    fill?: boolean;
    tension?: number;
    pointRadius?: number;
    pointHoverRadius?: number;
  }[];
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'doughnut' | 'scatter' | 'bubble' | 'area';
  title: string;
  xAxis?: {
    field: string;
    label: string;
    type: 'dimension' | 'temporal';
  };
  yAxis?: {
    field: string;
    label: string;
    type: 'measure';
  };
  colorScheme?: 'default' | 'colorful' | 'monochrome' | 'professional';
  showLegend?: boolean;
  showGrid?: boolean;
  animation?: boolean;
  responsive?: boolean;
}

export interface DataField {
  id: string;
  name: string;
  type: 'dimension' | 'measure';
  dataType: 'categorical' | 'numerical' | 'temporal' | 'text';
  sampleValues: any[];
  usageCount: number;
  description?: string;
  icon?: React.ReactNode;
}

export interface RawDataPoint {
  [key: string]: any;
}

// Advanced Analytics Interfaces
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

// Real-time Data Interfaces
export interface RealTimeConfig {
  endpoint: string;
  reconnectInterval: number;
  maxReconnectAttempts: number;
  heartbeatInterval: number;
  dataBufferSize: number;
}

export interface DataStreamConfig {
  source: 'websocket' | 'server-sent-events' | 'polling';
  updateFrequency: number; // milliseconds
  batchSize: number;
  enableCompression: boolean;
}

export interface RealTimeStats {
  connectionStatus: 'connected' | 'connecting' | 'disconnected' | 'error';
  lastUpdate: Date;
  messagesReceived: number;
  messagesSent: number;
  connectionUptime: number;
  reconnectAttempts: number;
  dataLatency: number;
  errorCount: number;
}

export interface DataUpdate {
  type: 'insert' | 'update' | 'delete' | 'batch';
  timestamp: Date;
  data: RawDataPoint[] | RawDataPoint;
  source: string;
  metadata?: {
    userId?: string;
    sessionId?: string;
    version?: number;
    checksum?: string;
  };
}

export interface SubscriptionConfig {
  dataSource: string;
  fields: string[];
  filters?: Array<{
    field: string;
    operator: string;
    value: any;
  }>;
  aggregation?: {
    type: 'count' | 'sum' | 'average' | 'min' | 'max';
    field: string;
    interval: number; // milliseconds
  };
}

// Backend Data Source Interfaces
export interface DataSourceConfig {
  id: string;
  name: string;
  type: 'database' | 'api' | 'file' | 'stream' | 'cloud';
  connectionString?: string;
  credentials?: {
    username?: string;
    password?: string;
    apiKey?: string;
    token?: string;
    certificate?: string;
  };
  options?: {
    timeout?: number;
    maxConnections?: number;
    ssl?: boolean;
    compression?: boolean;
    cache?: boolean;
    cacheTTL?: number;
  };
  schema?: {
    tables?: string[];
    collections?: string[];
    endpoints?: string[];
  };
}

// Phase 5: Advanced Chart Types & Export Interfaces
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
  config: Partial<AdvancedChartConfig>;
  category: string;
  isCustom: boolean;
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
  type: 'fade' | 'slide' | 'zoom' | 'bounce' | 'elastic' | 'none';
  duration: number;
  delay: number;
  easing: 'linear' | 'easeIn' | 'easeOut' | 'easeInOut';
  loop: boolean;
  direction: 'normal' | 'reverse' | 'alternate';
}

export interface QueryConfig {
  dataSourceId: string;
  query: string;
  parameters?: Record<string, any>;
  timeout?: number;
  maxRows?: number;
  includeMetadata?: boolean;
}

export interface DataSourceStatus {
  id: string;
  status: 'connected' | 'connecting' | 'disconnected' | 'error';
  lastConnection: Date;
  connectionTime: number;
  errorCount: number;
  lastError?: string;
  performance: {
    avgQueryTime: number;
    totalQueries: number;
    failedQueries: number;
  };
}

export interface QueryResult {
  data: RawDataPoint[];
  metadata?: {
    totalRows: number;
    queryTime: number;
    timestamp: Date;
    source: string;
    fields: DataField[];
  };
  error?: string;
}

export interface DataSourceHealth {
  status: 'healthy' | 'warning' | 'critical';
  metrics: {
    responseTime: number;
    availability: number;
    errorRate: number;
    throughput: number;
  };
  recommendations: string[];
}
