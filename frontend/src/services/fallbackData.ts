/**
 * Fallback Data for NextGen Report Builder
 * DEPRECATED: Should only be used as last resort when backend is unavailable
 * Production systems should use real API data
 */

import type { DataSource } from './nextGenReportService';

export const fallbackDataSources: DataSource[] = [
  {
    id: 'excel-upload',
    name: 'Excel File Upload',
    type: 'excel' as const,
    fields: [
      {
        id: 'region',
        name: 'Region',
        type: 'dimension' as const,
        dataType: 'categorical' as const,
        sampleValues: ['North', 'South', 'East', 'West'],
        usageCount: 0,
        description: 'Geographic region'
      },
      {
        id: 'revenue',
        name: 'Revenue',
        type: 'measure' as const,
        dataType: 'numerical' as const,
        sampleValues: [120000, 135000, 98000, 110000],
        usageCount: 0,
        description: 'Revenue in USD'
      },
      {
        id: 'quarter',
        name: 'Quarter',
        type: 'dimension' as const,
        dataType: 'temporal' as const,
        sampleValues: ['Q1', 'Q2', 'Q3', 'Q4'],
        usageCount: 0,
        description: 'Financial quarter'
      }
    ],
    connectionStatus: 'connected' as const,
    lastUpdated: new Date()
  },
  {
    id: 'csv-upload',
    name: 'CSV File Upload',
    type: 'csv' as const,
    fields: [],
    connectionStatus: 'connected' as const,
    lastUpdated: new Date()
  }
];

export const fallbackTemplates = [
  {
    id: 'default',
    name: 'Default Business Report',
    description: 'Clean, professional layout with charts and tables',
    category: 'business',
    thumbnail: null,
    config: {
      layout: 'standard',
      colorScheme: 'blue',
      includeCharts: true,
      includeTables: true
    }
  },
  {
    id: 'financial',
    name: 'Financial Report',
    description: 'Optimized for financial data with emphasis on numbers',
    category: 'financial',
    thumbnail: null,
    config: {
      layout: 'financial',
      colorScheme: 'green',
      includeCharts: true,
      includeTables: true
    }
  },
  {
    id: 'executive',
    name: 'Executive Summary',
    description: 'High-level overview format for executive presentations',
    category: 'executive',
    thumbnail: null,
    config: {
      layout: 'executive',
      colorScheme: 'dark',
      includeCharts: true,
      includeTables: false
    }
  },
  {
    id: 'detailed',
    name: 'Detailed Analysis',
    description: 'Comprehensive format with extensive data tables',
    category: 'analysis',
    thumbnail: null,
    config: {
      layout: 'detailed',
      colorScheme: 'multi',
      includeCharts: true,
      includeTables: true
    }
  }
];

export const fallbackAISuggestions = [
  {
    id: '1',
    title: 'Revenue Trend Analysis',
    confidence: 0.9,
    preview: 'Create a line chart showing revenue trends over time',
    reasoning: 'Detected temporal and numerical data suitable for trend analysis',
    icon: null,
    quickApply: () => console.log('Applied revenue trend chart')
  },
  {
    id: '2',
    title: 'Regional Performance Comparison',
    confidence: 0.85,
    preview: 'Generate bar chart comparing performance across regions',
    reasoning: 'Found categorical region data with numerical measures',
    icon: null,
    quickApply: () => console.log('Applied regional comparison chart')
  },
  {
    id: '3',
    title: 'Quarterly Summary Table',
    confidence: 0.8,
    preview: 'Create summary table with quarterly breakdowns',
    reasoning: 'Temporal quarterly data detected with multiple metrics',
    icon: null,
    quickApply: () => console.log('Applied quarterly summary table')
  }
];

export const fallbackExcelData = {
  sheets: {
    'Sheet1': {
      headers: ['Region', 'Quarter', 'Revenue', 'Profit Margin', 'Customers'],
      data: [
        ['North', 'Q1', 120000, 15, 450],
        ['North', 'Q2', 135000, 18, 520],
        ['South', 'Q1', 98000, 12, 380],
        ['South', 'Q2', 110000, 14, 420],
        ['East', 'Q1', 86000, 16, 320],
        ['East', 'Q2', 92000, 19, 350],
        ['West', 'Q1', 102000, 13, 400],
        ['West', 'Q2', 115000, 17, 460]
      ],
      tables: [
        {
          title: 'Regional Performance Data',
          headers: ['Region', 'Quarter', 'Revenue', 'Profit Margin', 'Customers'],
          data: [
            ['North', 'Q1', 120000, 15, 450],
            ['North', 'Q2', 135000, 18, 520],
            ['South', 'Q1', 98000, 12, 380],
            ['South', 'Q2', 110000, 14, 420]
          ],
          statistics: {
            totalRows: 8,
            totalRevenue: 858000,
            avgProfitMargin: 15.5,
            totalCustomers: 3300
          },
          chart_suggestions: [
            {
              type: 'bar',
              title: 'Revenue by Region',
              x_field: 'Region',
              y_field: 'Revenue'
            },
            {
              type: 'line',
              title: 'Revenue Trend',
              x_field: 'Quarter',
              y_field: 'Revenue'
            }
          ]
        }
      ]
    }
  },
  summary: {
    total_sheets: 1,
    total_rows: 8,
    total_columns: 5,
    data_types_detected: ['categorical', 'temporal', 'numerical'],
    suggested_charts: ['bar', 'line', 'pie']
  }
};