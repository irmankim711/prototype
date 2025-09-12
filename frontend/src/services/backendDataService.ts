/**
 * Backend Data Service
 * Handles connections to various data sources and backend services
 */

import type { RawDataPoint, DataField } from '../components/NextGenReportBuilder/types';

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

class BackendDataService {
  private dataSources: Map<string, DataSourceConfig> = new Map();
  private connections: Map<string, any> = new Map();
  private status: Map<string, DataSourceStatus> = new Map();
  private queryCache: Map<string, { data: any; timestamp: number; ttl: number }> = new Map();

  constructor() {
    this.initializeDefaultDataSources();
  }

  /**
   * Safe environment variable accessor for browser environment
   */
  private getEnvVar(key: string, defaultValue: string = ''): string {
    // Check if we're in a browser environment with Vite
    if (typeof import.meta !== 'undefined' && import.meta.env) {
      return import.meta.env[key] || defaultValue;
    }
    // Fallback for other environments
    return defaultValue;
  }

  /**
   * Initialize default data sources
   */
  private initializeDefaultDataSources(): void {
    const defaultSources: DataSourceConfig[] = [
      {
        id: 'local-postgres',
        name: 'Local PostgreSQL',
        type: 'database',
        connectionString: 'postgresql://localhost:5432/reports',
        options: {
          timeout: 30000,
          maxConnections: 10,
          ssl: false,
          cache: true,
          cacheTTL: 300000,
        },
      },
      {
        id: 'api-external',
        name: 'External API',
        type: 'api',
        connectionString: 'https://api.example.com/data',
        credentials: {
          apiKey: this.getEnvVar('VITE_API_KEY', ''),
        },
        options: {
          timeout: 15000,
          cache: true,
          cacheTTL: 60000,
        },
      },
      {
        id: 'mongodb-atlas',
        name: 'MongoDB Atlas',
        type: 'database',
        connectionString: 'mongodb+srv://cluster.mongodb.net/reports',
        options: {
          timeout: 30000,
          maxConnections: 5,
          ssl: true,
          cache: true,
          cacheTTL: 300000,
        },
      },
    ];

    defaultSources.forEach(source => {
      this.addDataSource(source);
    });
  }

  /**
   * Add a new data source
   */
  addDataSource(config: DataSourceConfig): void {
    this.dataSources.set(config.id, config);
    this.status.set(config.id, {
      id: config.id,
      status: 'disconnected',
      lastConnection: new Date(),
      connectionTime: 0,
      errorCount: 0,
      performance: {
        avgQueryTime: 0,
        totalQueries: 0,
        failedQueries: 0,
      },
    });
  }

  /**
   * Remove a data source
   */
  removeDataSource(id: string): void {
    this.disconnectDataSource(id);
    this.dataSources.delete(id);
    this.status.delete(id);
    this.connections.delete(id);
  }

  /**
   * Get all data sources
   */
  getDataSources(): DataSourceConfig[] {
    return Array.from(this.dataSources.values());
  }

  /**
   * Get data source by ID
   */
  getDataSource(id: string): DataSourceConfig | undefined {
    return this.dataSources.get(id);
  }

  /**
   * Connect to a data source
   */
  async connectDataSource(id: string): Promise<boolean> {
    const config = this.dataSources.get(id);
    if (!config) {
      throw new Error(`Data source not found: ${id}`);
    }

    const status = this.status.get(id)!;
    status.status = 'connecting';
    const startTime = Date.now();

    try {
      let connection: any;

      switch (config.type) {
        case 'database':
          connection = await this.connectDatabase(config);
          break;
        case 'api':
          connection = await this.connectAPI(config);
          break;
        case 'file':
          connection = await this.connectFile(config);
          break;
        case 'stream':
          connection = await this.connectStream(config);
          break;
        case 'cloud':
          connection = await this.connectCloud(config);
          break;
        default:
          throw new Error(`Unsupported data source type: ${config.type}`);
      }

      this.connections.set(id, connection);
      status.status = 'connected';
      status.lastConnection = new Date();
      status.connectionTime = Date.now() - startTime;
      status.errorCount = 0;

      return true;
    } catch (error) {
      status.status = 'error';
      status.errorCount++;
      status.lastError = error instanceof Error ? error.message : 'Unknown error';
      throw error;
    }
  }

  /**
   * Disconnect from a data source
   */
  async disconnectDataSource(id: string): Promise<void> {
    const connection = this.connections.get(id);
    if (connection) {
      try {
        if (typeof connection.close === 'function') {
          await connection.close();
        } else if (typeof connection.disconnect === 'function') {
          await connection.disconnect();
        }
      } catch (error) {
        console.error(`Error disconnecting from data source ${id}:`, error);
      }
    }

    this.connections.delete(id);
    const status = this.status.get(id);
    if (status) {
      status.status = 'disconnected';
    }
  }

  /**
   * Execute a query on a data source
   */
  async executeQuery(config: QueryConfig): Promise<QueryResult> {
    const dataSource = this.dataSources.get(config.dataSourceId);
    if (!dataSource) {
      throw new Error(`Data source not found: ${config.dataSourceId}`);
    }

    const status = this.status.get(config.dataSourceId)!;
    const startTime = Date.now();

    // Check cache first
    const cacheKey = this.generateCacheKey(config);
    const cached = this.queryCache.get(cacheKey);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return { data: cached.data };
    }

    try {
      // Ensure connection
      if (!this.connections.has(config.dataSourceId)) {
        await this.connectDataSource(config.dataSourceId);
      }

      const connection = this.connections.get(config.dataSourceId);
      let result: QueryResult;

      switch (dataSource.type) {
        case 'database':
          result = await this.executeDatabaseQuery(connection, config);
          break;
        case 'api':
          result = await this.executeAPIQuery(connection, config);
          break;
        case 'file':
          result = await this.executeFileQuery(connection, config);
          break;
        case 'stream':
          result = await this.executeStreamQuery(connection, config);
          break;
        case 'cloud':
          result = await this.executeCloudQuery(connection, config);
          break;
        default:
          throw new Error(`Unsupported data source type: ${dataSource.type}`);
      }

      // Update performance metrics
      const queryTime = Date.now() - startTime;
      status.performance.totalQueries++;
      status.performance.avgQueryTime = 
        (status.performance.avgQueryTime * (status.performance.totalQueries - 1) + queryTime) / 
        status.performance.totalQueries;

      // Cache result if enabled
      if (dataSource.options?.cache && result.data) {
        this.queryCache.set(cacheKey, {
          data: result.data,
          timestamp: Date.now(),
          ttl: dataSource.options.cacheTTL || 300000,
        });
      }

      return result;
    } catch (error) {
      status.performance.failedQueries++;
      status.errorCount++;
      status.lastError = error instanceof Error ? error.message : 'Unknown error';
      throw error;
    }
  }

  /**
   * Get data source status
   */
  getDataSourceStatus(id: string): DataSourceStatus | undefined {
    return this.status.get(id);
  }

  /**
   * Get all data source statuses
   */
  getAllDataSourceStatuses(): DataSourceStatus[] {
    return Array.from(this.status.values());
  }

  /**
   * Check data source health
   */
  async checkDataSourceHealth(id: string): Promise<DataSourceHealth> {
    const status = this.status.get(id);
    if (!status) {
      throw new Error(`Data source not found: ${id}`);
    }

    const health: DataSourceHealth = {
      status: 'healthy',
      metrics: {
        responseTime: status.performance.avgQueryTime,
        availability: status.status === 'connected' ? 100 : 0,
        errorRate: status.performance.totalQueries > 0 
          ? (status.performance.failedQueries / status.performance.totalQueries) * 100 
          : 0,
        throughput: status.performance.totalQueries,
      },
      recommendations: [],
    };

    // Determine health status
    if (health.metrics.errorRate > 10 || status.errorCount > 5) {
      health.status = 'critical';
      health.recommendations.push('High error rate detected. Check connection and credentials.');
    } else if (health.metrics.errorRate > 5 || status.errorCount > 2) {
      health.status = 'warning';
      health.recommendations.push('Moderate error rate. Monitor connection stability.');
    }

    if (health.metrics.responseTime > 5000) {
      health.status = health.status === 'critical' ? 'critical' : 'warning';
      health.recommendations.push('Slow response time. Consider optimizing queries or upgrading infrastructure.');
    }

    if (status.status !== 'connected') {
      health.status = 'critical';
      health.recommendations.push('Data source is not connected. Attempt to reconnect.');
    }

    return health;
  }

  /**
   * Test data source connection
   */
  async testConnection(id: string): Promise<boolean> {
    try {
      await this.connectDataSource(id);
      await this.disconnectDataSource(id);
      return true;
    } catch (error) {
      return false;
    }
  }

  /**
   * Get available schemas/tables for a data source
   */
  async getSchemaInfo(id: string): Promise<any> {
    const dataSource = this.dataSources.get(id);
    if (!dataSource) {
      throw new Error(`Data source not found: ${id}`);
    }

    if (!this.connections.has(id)) {
      await this.connectDataSource(id);
    }

    const connection = this.connections.get(id);
    
    switch (dataSource.type) {
      case 'database':
        return await this.getDatabaseSchema(connection, dataSource);
      case 'api':
        return await this.getAPISchema(connection, dataSource);
      default:
        throw new Error(`Schema info not available for data source type: ${dataSource.type}`);
    }
  }

  // Private helper methods
  private generateCacheKey(config: QueryConfig): string {
    return `${config.dataSourceId}:${config.query}:${JSON.stringify(config.parameters || {})}`;
  }

  private async connectDatabase(config: DataSourceConfig): Promise<any> {
    // Simulate database connection
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          type: 'database',
          config,
          close: async () => Promise.resolve(),
        });
      }, 1000);
    });
  }

  private async connectAPI(config: DataSourceConfig): Promise<any> {
    // Simulate API connection
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          type: 'api',
          config,
          disconnect: async () => Promise.resolve(),
        });
      }, 500);
    });
  }

  private async connectFile(config: DataSourceConfig): Promise<any> {
    // Simulate file connection
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          type: 'file',
          config,
          close: async () => Promise.resolve(),
        });
      }, 200);
    });
  }

  private async connectStream(config: DataSourceConfig): Promise<any> {
    // Simulate stream connection
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          type: 'stream',
          config,
          disconnect: async () => Promise.resolve(),
        });
      }, 300);
    });
  }

  private async connectCloud(config: DataSourceConfig): Promise<any> {
    // Simulate cloud connection
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          type: 'cloud',
          config,
          close: async () => Promise.resolve(),
        });
      }, 800);
    });
  }

  private async executeDatabaseQuery(connection: any, config: QueryConfig): Promise<QueryResult> {
    // Simulate database query execution
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: this.generateMockData(100),
          metadata: {
            totalRows: 100,
            queryTime: Math.random() * 1000,
            timestamp: new Date(),
            source: 'database',
            fields: this.generateMockFields(),
          },
        });
      }, Math.random() * 2000);
    });
  }

  private async executeAPIQuery(connection: any, config: QueryConfig): Promise<QueryResult> {
    // Simulate API query execution
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: this.generateMockData(50),
          metadata: {
            totalRows: 50,
            queryTime: Math.random() * 500,
            timestamp: new Date(),
            source: 'api',
            fields: this.generateMockFields(),
          },
        });
      }, Math.random() * 1000);
    });
  }

  private async executeFileQuery(connection: any, config: QueryConfig): Promise<QueryResult> {
    // Simulate file query execution
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: this.generateMockData(200),
          metadata: {
            totalRows: 200,
            queryTime: Math.random() * 300,
            timestamp: new Date(),
            source: 'file',
            fields: this.generateMockFields(),
          },
        });
      }, Math.random() * 800);
    });
  }

  private async executeStreamQuery(connection: any, config: QueryConfig): Promise<QueryResult> {
    // Simulate stream query execution
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: this.generateMockData(75),
          metadata: {
            totalRows: 75,
            queryTime: Math.random() * 400,
            timestamp: new Date(),
            source: 'stream',
            fields: this.generateMockFields(),
          },
        });
      }, Math.random() * 600);
    });
  }

  private async executeCloudQuery(connection: any, config: QueryConfig): Promise<QueryResult> {
    // Simulate cloud query execution
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          data: this.generateMockData(150),
          metadata: {
            totalRows: 150,
            queryTime: Math.random() * 1500,
            timestamp: new Date(),
            source: 'cloud',
            fields: this.generateMockFields(),
          },
        });
      }, Math.random() * 1200);
    });
  }

  private async getDatabaseSchema(connection: any, config: DataSourceConfig): Promise<any> {
    // Simulate database schema retrieval
    return {
      tables: ['users', 'orders', 'products', 'categories', 'analytics'],
      columns: {
        users: ['id', 'name', 'email', 'created_at', 'status'],
        orders: ['id', 'user_id', 'product_id', 'quantity', 'total', 'order_date'],
        products: ['id', 'name', 'price', 'category_id', 'stock', 'created_at'],
      },
    };
  }

  private async getAPISchema(connection: any, config: DataSourceConfig): Promise<any> {
    // Simulate API schema retrieval
    return {
      endpoints: ['/users', '/orders', '/products', '/analytics'],
      methods: ['GET', 'POST', 'PUT', 'DELETE'],
      parameters: {
        '/users': ['page', 'limit', 'sort', 'filter'],
        '/orders': ['user_id', 'date_from', 'date_to', 'status'],
      },
    };
  }

  private generateMockData(count: number): RawDataPoint[] {
    const data: RawDataPoint[] = [];
    for (let i = 0; i < count; i++) {
      data.push({
        id: i + 1,
        name: `Item ${i + 1}`,
        value: Math.floor(Math.random() * 1000),
        category: ['A', 'B', 'C'][Math.floor(Math.random() * 3)],
        date: new Date(Date.now() - Math.random() * 30 * 24 * 60 * 60 * 1000),
        status: Math.random() > 0.5 ? 'active' : 'inactive',
      });
    }
    return data;
  }

  private generateMockFields(): DataField[] {
    return [
      { id: 'id', name: 'id', type: 'dimension', dataType: 'numerical', sampleValues: [1, 2, 3], usageCount: 0 },
      { id: 'name', name: 'name', type: 'dimension', dataType: 'categorical', sampleValues: ['Item 1', 'Item 2'], usageCount: 0 },
      { id: 'value', name: 'value', type: 'measure', dataType: 'numerical', sampleValues: [100, 200, 300], usageCount: 0 },
      { id: 'category', name: 'category', type: 'dimension', dataType: 'categorical', sampleValues: ['A', 'B', 'C'], usageCount: 0 },
      { id: 'date', name: 'date', type: 'dimension', dataType: 'temporal', sampleValues: [new Date()], usageCount: 0 },
      { id: 'status', name: 'status', type: 'dimension', dataType: 'categorical', sampleValues: ['active', 'inactive'], usageCount: 0 },
    ];
  }
}

export const backendDataService = new BackendDataService();
export default backendDataService;
