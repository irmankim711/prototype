/**
 * Next-Gen Report Builder Service
 * Production-ready integration layer with backend APIs for data sources, templates, and report generation
 */

import React from 'react';
import axiosInstance from './axiosInstance';
import * as XLSX from 'xlsx';
import {
  fallbackDataSources,
  fallbackTemplates,
  fallbackAISuggestions,
  fallbackExcelData
} from './fallbackData';

export interface DataSource {
  id: string;
  name: string;
  type: 'excel' | 'database' | 'api' | 'csv';
  fields: DataField[];
  connectionStatus: 'connected' | 'disconnected' | 'error';
  lastUpdated: Date;
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

export interface ReportConfig {
  id?: string;
  title: string;
  description?: string;
  dataSourceId: string;
  elements: ReportElement[];
  layout: {
    theme: string;
    colorScheme: string;
    responsive: boolean;
  };
  metadata: {
    created: Date;
    modified: Date;
    createdBy: string;
    version: number;
  };
}

export interface ReportElement {
  id: string;
  type: 'chart' | 'table' | 'text' | 'image' | 'heading' | 'divider';
  title: string;
  config: any;
  position: { x: number; y: number };
  size: { width: number; height: number };
  dataMapping?: Record<string, any>;
  styling?: Record<string, any>;
  metadata: {
    created: Date;
    modified: Date;
    version: number;
  };
}

export interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string | string[];
  }[];
}

// Production logging service
class Logger {
  private static instance: Logger;
  
  private constructor() {}
  
  static getInstance(): Logger {
    if (!Logger.instance) {
      Logger.instance = new Logger();
    }
    return Logger.instance;
  }
  
  info(message: string, data?: any): void {
    if (process.env.NODE_ENV === 'development') {
      console.info(`[INFO] ${message}`, data);
    }
    // In production, this would send to a logging service
  }
  
  warn(message: string, data?: any): void {
    if (process.env.NODE_ENV === 'development') {
      console.warn(`[WARN] ${message}`, data);
    }
    // In production, this would send to a logging service
  }
  
  error(message: string, error?: any): void {
    if (process.env.NODE_ENV === 'development') {
      console.error(`[ERROR] ${message}`, error);
    }
    // In production, this would send to error tracking service
  }
}

// Request deduplication to prevent multiple simultaneous calls
class RequestDeduplicator {
  private static instance: RequestDeduplicator;
  private pendingRequests: Map<string, Promise<any>> = new Map();
  
  private constructor() {}
  
  static getInstance(): RequestDeduplicator {
    if (!RequestDeduplicator.instance) {
      RequestDeduplicator.instance = new RequestDeduplicator();
    }
    return RequestDeduplicator.instance;
  }
  
  async deduplicate<T>(key: string, requestFn: () => Promise<T>): Promise<T> {
    const dedupId = Math.random().toString(36).substr(2, 6);
    console.log(`🔄 [Dedup-${dedupId}] Checking deduplication for key: ${key}`);
    
    if (this.pendingRequests.has(key)) {
      console.log(`🔄 [Dedup-${dedupId}] Reusing pending request for ${key}`);
      const pendingPromise = this.pendingRequests.get(key)!;
      console.log(`🔄 [Dedup-${dedupId}] Pending promise type:`, typeof pendingPromise);
      
      try {
        const result = await pendingPromise;
        console.log(`✅ [Dedup-${dedupId}] Deduplicated request succeeded:`, {
          resultType: typeof result,
          isArray: Array.isArray(result),
          length: Array.isArray(result) ? result.length : 'N/A'
        });
        return result;
      } catch (error: any) {
        console.error(`❌ [Dedup-${dedupId}] Deduplicated request failed:`, {
          error: error.message,
          errorType: typeof error
        });
        throw error;
      }
    }
    
    console.log(`🚀 [Dedup-${dedupId}] Creating new request for key: ${key}`);
    const promise = requestFn();
    this.pendingRequests.set(key, promise);
    
    try {
      const result = await promise;
      console.log(`✅ [Dedup-${dedupId}] New request succeeded:`, {
        resultType: typeof result,
        isArray: Array.isArray(result),
        length: Array.isArray(result) ? result.length : 'N/A'
      });
      return result;
    } finally {
      console.log(`🧹 [Dedup-${dedupId}] Cleaning up pending request for key: ${key}`);
      this.pendingRequests.delete(key);
    }
  }
}

// Request throttling to respect rate limits
class RequestThrottler {
  private static instance: RequestThrottler;
  private requestTimestamps: Map<string, number[]> = new Map();
  private requestCounts: Map<string, number> = new Map();
  private lastResetTime: number = Date.now();
  
  private constructor() {}
  
  static getInstance(): RequestThrottler {
    if (!RequestThrottler.instance) {
      RequestThrottler.instance = new RequestThrottler();
    }
    return RequestThrottler.instance;
  }
  
  async throttle<T>(endpoint: string, requestFn: () => Promise<T>): Promise<T> {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    
    // Reset counters every minute
    if (now - this.lastResetTime >= 60000) {
      this.requestCounts.clear();
      this.lastResetTime = now;
    }
    
    // Get endpoint-specific rate limit config
    const config = this.getEndpointConfig(endpoint);
    const currentCount = this.requestCounts.get(endpoint) || 0;
    
    if (currentCount >= config.maxRequestsPerMinute) {
      const waitTime = 60000 - (now - this.lastResetTime) + 1000;
      console.warn(`Rate limit reached for ${endpoint}, waiting ${waitTime}ms`);
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }
    
    // Increment request count
    this.requestCounts.set(endpoint, currentCount + 1);
    
    // Add timestamp for tracking
    if (!this.requestTimestamps.has(endpoint)) {
      this.requestTimestamps.set(endpoint, []);
    }
    const timestamps = this.requestTimestamps.get(endpoint)!;
    timestamps.push(now);
    
    // Clean up old timestamps
    const recentTimestamps = timestamps.filter(timestamp => timestamp > oneMinuteAgo);
    this.requestTimestamps.set(endpoint, recentTimestamps);
    
    return requestFn();
  }
  
  private getEndpointConfig(endpoint: string) {
    // Default conservative limits
    const defaultConfig = {
      maxRequestsPerMinute: 20,
      maxRequestsPerSecond: 1,
      burstLimit: 3,
    };
    
    // Endpoint-specific overrides
    const endpointConfigs: Record<string, any> = {
      '/api/v1/nextgen/data-sources': { maxRequestsPerMinute: 15, maxRequestsPerSecond: 1 },
      '/api/v1/nextgen/templates': { maxRequestsPerMinute: 10, maxRequestsPerSecond: 1 },
      '/api/v1/nextgen/charts/generate': { maxRequestsPerMinute: 5, maxRequestsPerSecond: 1 },
      '/api/v1/nextgen/ai/suggestions': { maxRequestsPerMinute: 10, maxRequestsPerSecond: 1 },
    };
    
    return { ...defaultConfig, ...endpointConfigs[endpoint] };
  }
}

class NextGenReportService {
  private logger = Logger.getInstance();
  private cache = new Map<string, { data: any; timestamp: number; ttl: number }>();
  private deduplicator = RequestDeduplicator.getInstance();
  private throttler = RequestThrottler.getInstance();
  
  // Helper method to check authentication
  // Authentication is now handled by axiosInstance interceptors

  // Cache management
  private getCachedData<T>(key: string): T | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data as T;
    }
    this.cache.delete(key);
    return null;
  }

  private setCachedData<T>(key: string, data: T, ttl: number = 5 * 60 * 1000): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  // Enhanced retry logic with exponential backoff and rate limit handling
  private async retryWithBackoff<T>(
    fn: () => Promise<T>, 
    retries: number = 3,
    baseDelay: number = 2000
  ): Promise<T> {
    try {
      this.logger.info('Executing function with retry logic');
      const result = await fn();
      this.logger.info('Function executed successfully');
      return result;
    } catch (error: any) {
      const status = error?.response?.status;
      
      // Check if this is a client error (4xx) that shouldn't be retried
      if (status >= 400 && status < 500 && status !== 429) {
        this.logger.error(`Client error (${status}), not retrying:`, error?.response?.data);
        throw error; // Don't retry client errors except rate limiting
      }
      
      // Handle rate limiting specifically
      if (status === 429) {
        const retryAfter = error.response.headers['retry-after'];
        const waitTime = retryAfter ? parseInt(retryAfter) * 1000 : baseDelay * Math.pow(3, 4 - retries);
        
        this.logger.warn(`Rate limited (429), waiting ${waitTime}ms before retry ${4 - retries} of 3`);
        
        if (retries > 1) {
          await new Promise(resolve => setTimeout(resolve, waitTime));
          return this.retryWithBackoff(fn, retries - 1, baseDelay);
        }
      } else {
        this.logger.warn(`Function failed, attempt ${4 - retries} of 3`, error);
        
        if (retries > 1) {
          const delay = baseDelay * Math.pow(3, 4 - retries); // More aggressive exponential backoff
          this.logger.info(`Waiting ${delay}ms before retry`);
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.retryWithBackoff(fn, retries - 1, baseDelay);
        }
      }
      
      throw error;
    }
  }

  // Data Sources
  async getDataSources(): Promise<DataSource[]> {
    try {
      // Check cache first
      const cached = this.getCachedData<DataSource[]>('dataSources');
      if (cached) {
        this.logger.info('Returning cached data sources');
        return cached;
      }

      console.log('🔍 [NextGenReportService] Fetching data sources...');
      console.log('🔗 Endpoint: /api/v1/nextgen/data-sources');
      
      // Use deduplication and throttling to prevent multiple simultaneous calls and respect rate limits
      const response = await this.deduplicator.deduplicate('getDataSources', async () => {
        return await this.throttler.throttle('/api/v1/nextgen/data-sources', async () => {
          return await this.retryWithBackoff(async () => {
            console.log('📡 Making API request to /api/v1/nextgen/data-sources...');
            const apiResponse = await axiosInstance.get('/api/v1/nextgen/data-sources');
            
            // IMMEDIATE DEBUGGING: Log raw response details
            console.log('📥 Raw API response received:');
            console.log('  Status:', apiResponse.status);
            console.log('  Status Text:', apiResponse.statusText);
            console.log('  Headers:', apiResponse.headers);
            console.log('  Data Type:', typeof apiResponse.data);
            console.log('  Data Structure:', apiResponse.data);
            
            // Check if response is valid
            if (!apiResponse.data) {
              console.error('❌ No data in response');
              throw new Error('Empty response from data sources endpoint');
            }
            
            // Check content type if available
            const contentType = apiResponse.headers['content-type'];
            if (contentType && !contentType.includes('application/json')) {
              console.error('❌ Non-JSON response detected:', contentType);
              console.error('❌ Response content:', apiResponse.data);
              throw new Error(`Expected JSON response, got ${contentType}`);
            }
            
            // Validate response structure
            if (Array.isArray(apiResponse.data)) {
              console.log('✅ Response is direct array format');
              return apiResponse;
            } else if (apiResponse.data && Array.isArray(apiResponse.data.dataSources)) {
              console.log('✅ Response has dataSources property with array');
              return apiResponse;
            } else if (apiResponse.data && apiResponse.data.data && Array.isArray(apiResponse.data.data)) {
              console.log('✅ Response has data property with array');
              return apiResponse;
            } else {
              console.error('❌ Invalid response structure:', apiResponse.data);
              console.error('❌ Expected: array or {dataSources: array} or {data: array}');
              throw new Error('Invalid response format from data sources endpoint');
            }
          });
        });
      }) as any;

      // Process the validated response
      let dataSources: DataSource[] = [];
      
      if (Array.isArray(response.data)) {
        // Direct array format
        dataSources = response.data;
        console.log('✅ Using direct array format, found', dataSources.length, 'data sources');
      } else if (response.data?.dataSources && Array.isArray(response.data.dataSources)) {
        // {dataSources: [...]} format
        dataSources = response.data.dataSources;
        console.log('✅ Using dataSources property, found', dataSources.length, 'data sources');
      } else if (response.data?.data && Array.isArray(response.data.data)) {
        // {data: [...]} format
        dataSources = response.data.data;
        console.log('✅ Using data property, found', dataSources.length, 'data sources');
      }
      
      // Validate each data source has required properties
      const validDataSources = dataSources.filter((source, index) => {
        if (!source.id || !source.name || !source.type) {
          console.warn(`⚠️ Data source at index ${index} missing required properties:`, source);
          return false;
        }
        return true;
      });
      
      if (validDataSources.length !== dataSources.length) {
        console.warn(`⚠️ Filtered out ${dataSources.length - validDataSources.length} invalid data sources`);
      }
      
      console.log('✅ Successfully processed', validDataSources.length, 'valid data sources');
      
      // Cache the valid data sources
      this.setCachedData('dataSources', validDataSources, 2 * 60 * 1000); // 2 minutes cache
      
      return validDataSources;
      
    } catch (error: any) {
      console.error('🚨 [NextGenReportService] getDataSources failed:', {
        error: error.message,
        stack: error.stack,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText
      });
      
      // Provide specific error messages based on error type
      if (error.response?.status === 404) {
        throw new Error('Data sources endpoint not found. Please check if the backend service is running and the endpoint exists.');
      }
      
      if (error.response?.status === 500) {
        throw new Error('Server error occurred while fetching data sources. Please try again later.');
      }
      
      if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
        throw new Error('Unable to connect to the backend service. Please ensure the server is running on the correct port.');
      }
      
      if (error.code === 'ECONNABORTED') {
        throw new Error('Request timeout. The server took too long to respond.');
      }
      
      throw new Error(`Failed to load data sources: ${error.message || 'Unknown error occurred'}`);
    }
  }

  // Data Fields
  async getDataFields(dataSourceId: string): Promise<DataField[]> {
    const requestId = Math.random().toString(36).substr(2, 9);
    console.log(`🆔 [${requestId}] getDataFields called for dataSourceId: ${dataSourceId}`);
    
    try {
      const cacheKey = `dataFields_${dataSourceId}`;
      const cached = this.getCachedData<DataField[]>(cacheKey);
      if (cached) {
        console.log(`🆔 [${requestId}] Returning cached data fields (${cached.length} items)`);
        return cached;
      }

      console.log(`🔍 [${requestId}] Fetching data fields for dataSourceId: ${dataSourceId}`);
      console.log(`🔗 [${requestId}] Endpoint: /api/v1/nextgen/data-sources/${dataSourceId}/fields`);
      
      console.log(`🚀 [${requestId}] Making fresh request`);
      
      const response = await this.retryWithBackoff(async () => {
        console.log(`📡 [${requestId}] Making API request to /api/v1/nextgen/data-sources/${dataSourceId}/fields...`);
        const apiResponse = await axiosInstance.get(`/api/v1/nextgen/data-sources/${dataSourceId}/fields`);
        
        // IMMEDIATE DEBUGGING: Log raw response details
        console.log(`📥 [${requestId}] Raw API response received:`, {
          status: apiResponse.status,
          statusText: apiResponse.statusText,
          headers: apiResponse.headers,
          dataType: typeof apiResponse.data,
          dataStructure: apiResponse.data,
          isAxiosResponse: apiResponse.status !== undefined,
          responseKeys: Object.keys(apiResponse || {}),
          dataKeys: apiResponse.data ? Object.keys(apiResponse.data) : []
        });
        
        // Check if response is valid
        if (!apiResponse.data) {
          console.error(`❌ [${requestId}] No data in response`);
          throw new Error('Empty response from data fields endpoint');
        }
        
        // Check content type if available
        const contentType = apiResponse.headers['content-type'];
        if (contentType && !contentType.includes('application/json')) {
          console.error(`❌ [${requestId}] Non-JSON response detected:`, contentType);
          console.error(`❌ [${requestId}] Response content:`, apiResponse.data);
          throw new Error(`Expected JSON response, got ${contentType}`);
        }
        
        return apiResponse;
      }) as any;

      console.log(`🔍 [${requestId}] Processing response:`, {
        responseType: typeof response,
        hasData: 'data' in response,
        dataType: response.data ? typeof response.data : 'undefined',
        responseKeys: Object.keys(response || {}),
        dataKeys: response.data ? Object.keys(response.data) : []
      });

      // Process the response - handle multiple possible formats
      let dataFields: DataField[] = [];
      
      if (Array.isArray(response.data)) {
        // Direct array format
        dataFields = response.data;
        console.log(`✅ [${requestId}] Using direct array format, found ${dataFields.length} data fields`);
      } else if (response.data?.fields && Array.isArray(response.data.fields)) {
        // {fields: [...]} format
        dataFields = response.data.fields;
        console.log(`✅ [${requestId}] Using fields property, found ${dataFields.length} data fields`);
      } else if (response.data?.data && Array.isArray(response.data.data)) {
        // {data: [...]} format
        dataFields = response.data.data;
        console.log(`✅ [${requestId}] Using data property, found ${dataFields.length} data fields`);
      } else if (response.data?.dataFields && Array.isArray(response.data.dataFields)) {
        // {dataFields: [...]} format
        dataFields = response.data.dataFields;
        console.log(`✅ [${requestId}] Using dataFields property, found ${dataFields.length} data fields`);
      } else {
        console.error(`❌ [${requestId}] Invalid response structure:`, response.data);
        console.error(`❌ [${requestId}] Expected: array or {fields: array} or {data: array} or {dataFields: array}`);
        throw new Error('Invalid response format from data fields endpoint');
      }
      
      // Validate each data field has required properties
      const validDataFields = dataFields.filter((field, index) => {
        if (!field.id || !field.name || !field.type) {
          console.warn(`⚠️ [${requestId}] Data field at index ${index} missing required properties:`, field);
          return false;
        }
        return true;
      });
      
      if (validDataFields.length !== dataFields.length) {
        console.warn(`⚠️ [${requestId}] Filtered out ${dataFields.length - validDataFields.length} invalid data fields`);
      }
      
      console.log(`✅ [${requestId}] Successfully processed ${validDataFields.length} valid data fields`);
      
      // Cache the valid data fields
      this.setCachedData(cacheKey, validDataFields, 5 * 60 * 1000); // 5 minutes cache
      
      return validDataFields;
      
    } catch (error: any) {
      console.error(`🚨 [${requestId}] getDataFields failed for dataSourceId ${dataSourceId}:`, {
        error: error.message,
        stack: error.stack,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText,
        errorKeys: Object.keys(error || {})
      });
      
      // Provide fallback data when API fails
      if (error.message.includes('timeout') || error.code === 'ECONNABORTED') {
        console.log(`⚠️ [${requestId}] API timeout detected, providing fallback data`);
        
        // Return fallback data structure for excel-upload
        if (dataSourceId === 'excel-upload') {
          const fallbackFields: DataField[] = [
            {
              id: 'name',
              name: 'Name',
              type: 'dimension',
              dataType: 'categorical',
              sampleValues: ['John Doe', 'Jane Smith', 'Bob Johnson'],
              usageCount: 0,
              description: 'Full name of the person',
              icon: null
            },
            {
              id: 'email',
              name: 'Email',
              type: 'dimension',
              dataType: 'text',
              sampleValues: ['john@example.com', 'jane@example.com'],
              usageCount: 0,
              description: 'Email address',
              icon: null
            },
            {
              id: 'age',
              name: 'Age',
              type: 'measure',
              dataType: 'numerical',
              sampleValues: [25, 30, 35, 40],
              usageCount: 0,
              description: 'Age in years',
              icon: null
            },
            {
              id: 'satisfaction',
              name: 'Satisfaction Score',
              type: 'measure',
              dataType: 'numerical',
              sampleValues: [1, 2, 3, 4, 5],
              usageCount: 0,
              description: 'Overall satisfaction rating',
              icon: null
            }
          ];
          
          console.log(`✅ [${requestId}] Returning ${fallbackFields.length} fallback data fields`);
          return fallbackFields;
        }
      }
      
      // Provide specific error messages based on error type
      if (error.response?.status === 404) {
        throw new Error(`Data fields endpoint not found for data source ${dataSourceId}. Please check if the data source exists.`);
      }
      
      if (error.response?.status === 500) {
        throw new Error(`Server error occurred while fetching data fields for ${dataSourceId}. Please try again later.`);
      }
      
      if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
        throw new Error('Unable to connect to the backend service. Please ensure the server is running on the correct port.');
      }
      
      if (error.code === 'ECONNABORTED') {
        throw new Error('Request timeout. The server took too long to respond.');
      }
      
      throw new Error(`Failed to load data fields for ${dataSourceId}: ${error.message || 'Unknown error occurred'}`);
    }
  }

  // Chart Generation
  async generateChartData(
    dataSourceId: string,
    chartConfig: any
  ): Promise<ChartData> {
    try {

      const response = await this.retryWithBackoff(async () => {
        return await axiosInstance.post('/api/v1/nextgen/charts/generate', {
          dataSourceId,
          config: chartConfig,
        });
      }) as any;
      
      if (response?.data?.chartData) {
        return response.data.chartData;
      }
      
      throw new Error('Invalid response format from chart generation endpoint');
    } catch (error: any) {
      this.logger.error('Failed to generate chart data', error);
      throw new Error('Failed to generate chart data. Please try again.');
    }
  }

  // AI Suggestions
  async getSmartSuggestions(
    dataSourceId: string,
    context?: any
  ): Promise<any[]> {
    try {

      const response = await this.retryWithBackoff(async () => {
        return await axiosInstance.post('/api/v1/nextgen/ai/suggestions', {
          dataSourceId,
          context,
        });
      }) as any;
      
      if (response?.data?.suggestions) {
        return response.data.suggestions;
      }
      
      return [];
    } catch (error: any) {
      this.logger.error('Failed to get AI suggestions', error);
      return [];
    }
  }

  // Export Functions
  async exportReport(reportId: string, format: string): Promise<any> {
    try {

      const response = await this.retryWithBackoff(async () => {
        return await axiosInstance.get(`/api/v1/nextgen/reports/${reportId}/export?format=${format}`);
      }) as any;

      if (response?.data) {
        return response.data;
      }
      
      throw new Error('Invalid response format from export endpoint');
    } catch (error: any) {
      this.logger.error('Failed to export report', error);
      throw error;
    }
  }

  // Templates - Production implementation
  async getReportTemplates(): Promise<any[]> {
    const requestId = Math.random().toString(36).substr(2, 9);
    console.log(`🆔 [${requestId}] getReportTemplates called`);
    
    try {
      const cacheKey = 'reportTemplates';
      const cached = this.getCachedData<any[]>(cacheKey);
      if (cached) {
        console.log(`🆔 [${requestId}] Returning cached report templates (${cached.length} items)`);
        return cached;
      }

      console.log(`🔍 [${requestId}] Fetching report templates...`);
      console.log(`🔗 [${requestId}] Endpoint: /api/v1/nextgen/templates`);
      
      console.log(`🚀 [${requestId}] Making fresh request`);
      
      const response = await this.retryWithBackoff(async () => {
        console.log(`📡 [${requestId}] Making API request to /api/v1/nextgen/templates...`);
        const apiResponse = await axiosInstance.get('/api/v1/nextgen/templates');
        
        // IMMEDIATE DEBUGGING: Log raw response details
        console.log(`📥 [${requestId}] Raw API response received:`, {
          status: apiResponse.status,
          statusText: apiResponse.statusText,
          headers: apiResponse.headers,
          dataType: typeof apiResponse.data,
          dataStructure: apiResponse.data,
          isAxiosResponse: apiResponse.status !== undefined,
          responseKeys: Object.keys(apiResponse || {}),
          dataKeys: apiResponse.data ? Object.keys(apiResponse.data) : []
        });
        
        // Check if response is valid
        if (!apiResponse.data) {
          console.error(`❌ [${requestId}] No data in response`);
          throw new Error('Empty response from templates endpoint');
        }
        
        // Check content type if available
        const contentType = apiResponse.headers['content-type'];
        if (contentType && !contentType.includes('application/json')) {
          console.error(`❌ [${requestId}] Non-JSON response detected:`, contentType);
          console.error(`❌ [${requestId}] Response content:`, apiResponse.data);
          throw new Error(`Expected JSON response, got ${contentType}`);
        }
        
        return apiResponse;
      }) as any;

      console.log(`🔍 [${requestId}] Processing response:`, {
        responseType: typeof response,
        hasData: 'data' in response,
        dataType: response.data ? typeof response.data : 'undefined',
        responseKeys: Object.keys(response || {}),
        dataKeys: response.data ? Object.keys(response.data) : []
      });

      // Process the response - handle multiple possible formats
      let templates: any[] = [];
      
      if (Array.isArray(response.data)) {
        // Direct array format
        templates = response.data;
        console.log(`✅ [${requestId}] Using direct array format, found ${templates.length} templates`);
      } else if (response.data?.templates && Array.isArray(response.data.templates)) {
        // {templates: [...]} format
        templates = response.data.templates;
        console.log(`✅ [${requestId}] Using templates property, found ${templates.length} templates`);
      } else if (response.data?.recommendedTemplates && Array.isArray(response.data.recommendedTemplates)) {
        // {recommendedTemplates: [...]} format
        templates = response.data.recommendedTemplates;
        console.log(`✅ [${requestId}] Using recommendedTemplates property, found ${templates.length} templates`);
      } else if (response.data?.data && Array.isArray(response.data.data)) {
        // {data: [...]} format
        templates = response.data.data;
        console.log(`✅ [${requestId}] Using data property, found ${templates.length} templates`);
      } else {
        console.error(`❌ [${requestId}] Invalid response structure:`, response.data);
        console.error(`❌ [${requestId}] Expected: array or {templates: array} or {recommendedTemplates: array} or {data: array}`);
        throw new Error('No templates available from backend');
      }
      
      console.log(`✅ [${requestId}] Successfully processed ${templates.length} templates`);
      
      // Cache the templates
      this.setCachedData(cacheKey, templates, 10 * 60 * 1000); // 10 minutes cache
      
      return templates;
      
    } catch (error: any) {
      console.error(`🚨 [${requestId}] getReportTemplates failed:`, {
        error: error.message,
        stack: error.stack,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText,
        errorType: typeof error,
        errorKeys: Object.keys(error || {})
      });
      
      // Provide specific error messages based on error type
      if (error.response?.status === 405) {
        throw new Error('Method not allowed. The templates endpoint does not support GET requests. Please check the backend configuration.');
      }
      
      if (error.response?.status === 404) {
        throw new Error('Templates endpoint not found. Please check if the backend service is running and the endpoint exists.');
      }
      
      if (error.response?.status === 500) {
        throw new Error('Server error occurred while fetching templates. Please try again later.');
      }
      
      if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
        throw new Error('Unable to connect to the backend service. Please ensure the server is running on the correct port.');
      }
      
      if (error.code === 'ECONNABORTED') {
        throw new Error('Request timeout. The server took too long to respond.');
      }
      
      throw new Error(`Failed to load report templates: ${error.message || 'Unknown error occurred'}`);
    }
  }

  // Save template to backend
  async saveTemplate(template: any): Promise<any> {
    const requestId = Math.random().toString(36).substr(2, 9);
    console.log(`🆔 [${requestId}] saveTemplate called`);
    
    try {
      console.log(`🔍 [${requestId}] Saving template to backend...`);
      console.log(`🔗 [${requestId}] Endpoint: /api/v1/nextgen/templates`);
      console.log(`📦 [${requestId}] Template data:`, {
        templateType: typeof template,
        templateKeys: Object.keys(template || {}),
        templateId: template?.id,
        templateName: template?.name
      });
      
      console.log(`🚀 [${requestId}] Making POST request`);
      
      const response = await this.retryWithBackoff(async () => {
        console.log(`📡 [${requestId}] Making API request to /api/v1/nextgen/templates...`);
        const apiResponse = await axiosInstance.post('/api/v1/nextgen/templates', template);
        
        // IMMEDIATE DEBUGGING: Log raw response details
        console.log(`📥 [${requestId}] Raw API response received:`, {
          status: apiResponse.status,
          statusText: apiResponse.statusText,
          headers: apiResponse.headers,
          dataType: typeof apiResponse.data,
          dataStructure: apiResponse.data,
          isAxiosResponse: apiResponse.status !== undefined,
          responseKeys: Object.keys(apiResponse || {}),
          dataKeys: apiResponse.data ? Object.keys(apiResponse.data) : []
        });
        
        return apiResponse;
      }) as any;

      console.log(`🔍 [${requestId}] Processing response:`, {
        responseType: typeof response,
        hasData: 'data' in response,
        dataType: response.data ? typeof response.data : 'undefined',
        responseKeys: Object.keys(response || {}),
        dataKeys: response.data ? Object.keys(response.data) : []
      });

      if (response?.data?.success) {
        console.log(`✅ [${requestId}] Template saved successfully`);
        // Clear template cache to ensure fresh data
        this.cache.delete('reportTemplates');
        return response.data;
      }
      
      console.error(`❌ [${requestId}] Template save response missing success flag:`, response?.data);
      throw new Error('Failed to save template to backend');
      
    } catch (error: any) {
      console.error(`🚨 [${requestId}] saveTemplate failed:`, {
        error: error.message,
        stack: error.stack,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText,
        errorType: typeof error,
        errorKeys: Object.keys(error || {})
      });
      
      // Provide specific error messages based on error type
      if (error.response?.status === 405) {
        throw new Error('Method not allowed. The templates endpoint does not support POST requests. Please check the backend configuration.');
      }
      
      if (error.response?.status === 404) {
        throw new Error('Templates endpoint not found. Please check if the backend service is running and the endpoint exists.');
      }
      
      if (error.response?.status === 500) {
        throw new Error('Server error occurred while saving template. Please try again later.');
      }
      
      if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
        throw new Error('Unable to connect to the backend service. Please ensure the server is running on the correct port.');
      }
      
      if (error.code === 'ECONNABORTED') {
        throw new Error('Request timeout. The server took too long to respond.');
      }
      
      throw new Error(`Failed to save template: ${error.message || 'Unknown error occurred'}`);
    }
  }

  // Excel Automation
  async uploadExcelFile(file: File): Promise<any> {
    try {
      this.logger.info('Starting Excel file upload to backend', { fileName: file.name, fileSize: file.size });
      
      // Validate file type
      if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.xls')) {
        throw new Error('Invalid file type. Please upload Excel files (.xlsx or .xls)');
      }
      
      // Validate file size (50MB limit)
      if (file.size > 50 * 1024 * 1024) {
        throw new Error('File size exceeds 50MB limit');
      }
      
      // Create FormData to upload file to backend
      const formData = new FormData();
      formData.append('file', file);
      
      // Upload file to backend Excel upload endpoint
      const response = await this.retryWithBackoff(async () => {
        this.logger.info('Uploading Excel file to backend endpoint');
        const apiResponse = await axiosInstance.post('/api/v1/nextgen/excel/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        
        this.logger.info('Backend upload response received', {
          status: apiResponse.status,
          data: apiResponse.data
        });
        
        return apiResponse;
      }) as any;
      
      if (response?.data?.success) {
        this.logger.info('Excel file uploaded successfully to backend', { 
          dataSourceId: response.data.dataSource.id,
          recordCount: response.data.dataSource.recordCount,
          fieldCount: response.data.dataSource.fields?.length || 0
        });
        
        return response.data;
      } else {
        throw new Error('Backend upload failed or returned invalid response');
      }
    } catch (error) {
      this.logger.error('Failed to upload Excel file to backend', error);
      
      // Provide more specific error messages
      let errorMessage = 'Failed to upload Excel file to backend';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      // Handle specific upload errors
      if (errorMessage.includes('Invalid file')) {
        errorMessage = 'The file appears to be corrupted or not a valid Excel file';
      } else if (errorMessage.includes('network') || errorMessage.includes('connection')) {
        errorMessage = 'Network error. Please check your connection and try again.';
      } else if (errorMessage.includes('timeout')) {
        errorMessage = 'Upload timeout. Please try uploading again.';
      }
      
      // Create a more informative error
      const enhancedError = new Error(errorMessage);
      (enhancedError as any).originalError = error;
      (enhancedError as any).fileName = file.name;
      (enhancedError as any).fileSize = file.size;
      
      throw enhancedError;
    }
  }



  async generateReportFromExcel(excelFilePath: string, templateId: string, reportTitle?: string): Promise<any> {
    const requestId = Math.random().toString(36).substr(2, 9);
    console.log(`🆔 [${requestId}] generateReportFromExcel called`);
    
    try {
      console.log(`🔍 [${requestId}] Generating report from Excel...`);
      console.log(`🔗 [${requestId}] Endpoint: /api/v1/nextgen/excel/generate-report`);
      console.log(`📦 [${requestId}] Request payload:`, {
        excelFilePath,
        templateId,
        reportTitle,
        payloadType: 'POST'
      });
      
      // ADDITIONAL DEBUGGING: Validate payload before sending
      if (!excelFilePath) {
        console.error(`❌ [${requestId}] Missing excelFilePath in payload`);
        throw new Error('Excel file path is required');
      }
      if (!templateId) {
        console.error(`❌ [${requestId}] Missing templateId in payload`);
        throw new Error('Template ID is required');
      }
      
      console.log(`✅ [${requestId}] Payload validation passed`);
      
      console.log(`🚀 [${requestId}] Making POST request`);
      
      const response = await this.retryWithBackoff(async () => {
        console.log(`📡 [${requestId}] Making API request to /api/v1/nextgen/excel/generate-report...`);
        const apiResponse = await axiosInstance.post('/api/v1/nextgen/excel/generate-report', {
          excelFilePath,
          templateId,
          reportTitle
        });
        
        // IMMEDIATE DEBUGGING: Log raw response details
        console.log(`📥 [${requestId}] Raw API response received:`, {
          status: apiResponse.status,
          statusText: apiResponse.statusText,
          headers: apiResponse.headers,
          dataType: typeof apiResponse.data,
          dataStructure: apiResponse.data,
          isAxiosResponse: apiResponse.status !== undefined,
          responseKeys: Object.keys(apiResponse || {}),
          dataKeys: apiResponse.data ? Object.keys(apiResponse.data) : []
        });
        
        // Check if response is valid
        if (!apiResponse.data) {
          console.error(`❌ [${requestId}] No data in response`);
          throw new Error('Empty response from Excel report generation endpoint');
        }
        
        // Check content type if available
        const contentType = apiResponse.headers['content-type'];
        if (contentType && !contentType.includes('application/json')) {
          console.error(`❌ [${requestId}] Non-JSON response detected:`, contentType);
          console.error(`❌ [${requestId}] Response content:`, apiResponse.data);
          throw new Error(`Expected JSON response, got ${contentType}`);
        }
        
        return apiResponse;
      }) as any;

      console.log(`🔍 [${requestId}] Processing response:`, {
        responseType: typeof response,
        hasData: 'data' in response,
        dataType: response.data ? typeof response.data : 'undefined',
        responseKeys: Object.keys(response || {}),
        dataKeys: response.data ? Object.keys(response.data) : []
      });

      if (response?.data) {
        // Check for the fields we expect from the backend
        const reportData = response.data;
        const reportId = reportData.reportId || reportData.id || reportData.report_id;
        const reportTitle = reportData.reportTitle || reportData.title;
        const reportType = reportData.reportType || reportData.type || reportData.report_type;
        
        if (!reportId) {
          console.error(`❌ [${requestId}] Backend response missing reportId:`, reportData);
          throw new Error('Report generation failed: No report ID returned from backend');
        }
        
        console.log(`✅ [${requestId}] Report generated successfully:`, {
          reportId,
          reportTitle,
          reportType,
          success: reportData.success
        });
        
        return response.data;
      }
      
      console.error(`❌ [${requestId}] Response missing data property:`, response);
      throw new Error('Invalid response format from Excel report generation endpoint');
      
    } catch (error: any) {
      console.error(`🚨 [${requestId}] generateReportFromExcel failed:`, {
        error: error.message,
        stack: error.stack,
        response: error.response?.data,
        status: error.response?.status,
        statusText: error.response?.statusText,
        errorType: typeof error,
        errorKeys: Object.keys(error || {}),
        requestPayload: { excelFilePath, templateId, reportTitle }
      });
      
      // Provide specific error messages based on error type
      if (error.response?.status === 500) {
        console.error(`🔥 [${requestId}] SERVER ERROR (500) - Backend encountered internal error`);
        console.error(`🔥 [${requestId}] This usually indicates a backend processing issue`);
        console.error(`🔥 [${requestId}] Check backend logs for detailed error information`);
        throw new Error('Server error occurred while generating Excel report. The backend encountered an internal error. Please check backend logs and try again later.');
      }
      
      if (error.response?.status === 404) {
        throw new Error('Excel report generation endpoint not found. Please check if the backend service is running and the endpoint exists.');
      }
      
      if (error.response?.status === 400) {
        throw new Error('Bad request. Please check that the Excel file path, template ID, and report title are valid.');
      }
      
      if (error.response?.status === 413) {
        throw new Error('File too large. The Excel file exceeds the maximum allowed size.');
      }
      
      if (error.code === 'ERR_NETWORK' || error.code === 'ECONNREFUSED') {
        throw new Error('Unable to connect to the backend service. Please ensure the server is running on the correct port.');
      }
      
      if (error.code === 'ECONNABORTED') {
        throw new Error('Request timeout. The server took too long to respond while processing the Excel file.');
      }
      
      throw new Error(`Failed to generate Excel report: ${error.message || 'Unknown error occurred'}`);
    }
  }

  // Clear cache for specific keys or all
  clearCache(key?: string): void {
    if (key) {
      this.cache.delete(key);
    } else {
      this.cache.clear();
    }
  }
}

// Export singleton instance
export const nextGenReportService = new NextGenReportService();
export default nextGenReportService;
