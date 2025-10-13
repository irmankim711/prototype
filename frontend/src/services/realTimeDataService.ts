/**
 * Real-time Data Service
 * Handles WebSocket connections, data streaming, and live updates
 */

import type { RawDataPoint } from '../components/NextGenReportBuilder/types';

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

class RealTimeDataService {
  private ws: WebSocket | null = null;
  private eventSource: EventSource | null = null;
  private pollingInterval: NodeJS.Timeout | null = null;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  
  private config: RealTimeConfig;
  private streamConfig: DataStreamConfig;
  private stats: RealTimeStats;
  private subscribers: Map<string, (update: DataUpdate) => void> = new Map();
  private dataBuffer: RawDataPoint[] = [];
  private reconnectAttempts = 0;
  private connectionStartTime: Date | null = null;

  constructor(
    config: Partial<RealTimeConfig> = {},
    streamConfig: Partial<DataStreamConfig> = {}
  ) {
    this.config = {
      endpoint: 'ws://localhost:8000/ws/data',
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      heartbeatInterval: 30000,
      dataBufferSize: 1000,
      ...config,
    };

    this.streamConfig = {
      source: 'websocket',
      updateFrequency: 1000,
      batchSize: 100,
      enableCompression: false,
      ...streamConfig,
    };

    this.stats = {
      connectionStatus: 'disconnected',
      lastUpdate: new Date(),
      messagesReceived: 0,
      messagesSent: 0,
      connectionUptime: 0,
      reconnectAttempts: 0,
      dataLatency: 0,
      errorCount: 0,
    };
  }

  /**
   * Connect to real-time data source
   */
  async connect(): Promise<void> {
    try {
      this.stats.connectionStatus = 'connecting';
      this.connectionStartTime = new Date();

      switch (this.streamConfig.source) {
        case 'websocket':
          await this.connectWebSocket();
          break;
        case 'server-sent-events':
          await this.connectEventSource();
          break;
        case 'polling':
          await this.startPolling();
          break;
        default:
          throw new Error(`Unsupported data source: ${this.streamConfig.source}`);
      }
    } catch (error) {
      console.error('Failed to connect to real-time data source:', error);
      this.stats.connectionStatus = 'error';
      this.stats.errorCount++;
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from data source
   */
  disconnect(): void {
    this.stats.connectionStatus = 'disconnected';
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    if (this.pollingInterval) {
      clearInterval(this.pollingInterval);
      this.pollingInterval = null;
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    this.connectionStartTime = null;
  }

  /**
   * Subscribe to data updates
   */
  subscribe(id: string, callback: (update: DataUpdate) => void): void {
    this.subscribers.set(id, callback);
  }

  /**
   * Unsubscribe from data updates
   */
  unsubscribe(id: string): void {
    this.subscribers.delete(id);
  }

  /**
   * Get current connection statistics
   */
  getStats(): RealTimeStats {
    if (this.connectionStartTime) {
      this.stats.connectionUptime = Date.now() - this.connectionStartTime.getTime();
    }
    return { ...this.stats };
  }

  /**
   * Send data to the server
   */
  sendData(data: any): void {
    if (this.stats.connectionStatus === 'connected') {
      try {
        if (this.ws) {
          this.ws.send(JSON.stringify(data));
        }
        this.stats.messagesSent++;
      } catch (error) {
        console.error('Failed to send data:', error);
        this.stats.errorCount++;
      }
    }
  }

  /**
   * Request specific data from server
   */
  requestData(config: SubscriptionConfig): void {
    const request = {
      type: 'data_request',
      config,
      timestamp: new Date().toISOString(),
    };

    this.sendData(request);
  }

  /**
   * Get buffered data
   */
  getBufferedData(): RawDataPoint[] {
    return [...this.dataBuffer];
  }

  /**
   * Clear data buffer
   */
  clearBuffer(): void {
    this.dataBuffer = [];
  }

  /**
   * Update configuration
   */
  updateConfig(newConfig: Partial<RealTimeConfig>): void {
    this.config = { ...this.config, ...newConfig };
  }

  /**
   * Update stream configuration
   */
  updateStreamConfig(newConfig: Partial<DataStreamConfig>): void {
    const oldSource = this.streamConfig.source;
    this.streamConfig = { ...this.streamConfig, ...newConfig };

    // Reconnect if data source changed
    if (oldSource !== this.streamConfig.source) {
      this.disconnect();
      this.connect();
    }
  }

  // Private methods
  private async connectWebSocket(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(this.config.endpoint);

        this.ws.onopen = () => {
          this.stats.connectionStatus = 'connected';
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.setupWebSocketHandlers();
          resolve();
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.stats.errorCount++;
          reject(error);
        };

        this.ws.onclose = () => {
          this.stats.connectionStatus = 'disconnected';
          this.stopHeartbeat();
          this.scheduleReconnect();
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private async connectEventSource(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.eventSource = new EventSource(this.config.endpoint.replace('ws://', 'http://'));

        this.eventSource.onopen = () => {
          this.stats.connectionStatus = 'connected';
          this.reconnectAttempts = 0;
          resolve();
        };

        this.eventSource.onerror = (error) => {
          console.error('EventSource error:', error);
          this.stats.errorCount++;
          reject(error);
        };

        this.eventSource.onmessage = (event) => {
          this.handleDataMessage(event.data);
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  private async startPolling(): Promise<void> {
    this.stats.connectionStatus = 'connected';
    
    this.pollingInterval = setInterval(async () => {
      try {
        const response = await fetch(this.config.endpoint.replace('ws://', 'http://'));
        if (response.ok) {
          const data = await response.json();
          this.handleDataMessage(data);
        }
      } catch (error) {
        console.error('Polling error:', error);
        this.stats.errorCount++;
      }
    }, this.streamConfig.updateFrequency);
  }

  private setupWebSocketHandlers(): void {
    if (!this.ws) return;

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        this.handleDataMessage(data);
        this.stats.messagesReceived++;
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
        this.stats.errorCount++;
      }
    };
  }

  private handleDataMessage(data: any): void {
    const startTime = Date.now();

    try {
      let update: DataUpdate;

      if (Array.isArray(data)) {
        // Batch update
        update = {
          type: 'batch',
          timestamp: new Date(),
          data: data,
          source: 'realtime',
        };
      } else if (data.type && data.data) {
        // Structured update
        update = {
          type: data.type,
          timestamp: new Date(data.timestamp || Date.now()),
          data: data.data,
          source: data.source || 'realtime',
          metadata: data.metadata,
        };
      } else {
        // Raw data
        update = {
          type: 'insert',
          timestamp: new Date(),
          data: data,
          source: 'realtime',
        };
      }

      // Add to buffer
      this.addToBuffer(update.data);

      // Notify subscribers
      this.notifySubscribers(update);

      // Update stats
      this.stats.lastUpdate = new Date();
      this.stats.dataLatency = Date.now() - startTime;

    } catch (error) {
      console.error('Failed to handle data message:', error);
      this.stats.errorCount++;
    }
  }

  private addToBuffer(data: RawDataPoint | RawDataPoint[]): void {
    const dataArray = Array.isArray(data) ? data : [data];
    
    this.dataBuffer.push(...dataArray);

    // Maintain buffer size
    if (this.dataBuffer.length > this.config.dataBufferSize) {
      this.dataBuffer = this.dataBuffer.slice(-this.config.dataBufferSize);
    }
  }

  private notifySubscribers(update: DataUpdate): void {
    this.subscribers.forEach((callback) => {
      try {
        callback(update);
      } catch (error) {
        console.error('Subscriber callback error:', error);
        this.stats.errorCount++;
      }
    });
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'heartbeat', timestamp: Date.now() }));
      }
    }, this.config.heartbeatInterval);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts < this.config.maxReconnectAttempts) {
      this.reconnectAttempts++;
      this.stats.reconnectAttempts = this.reconnectAttempts;

      this.reconnectTimer = setTimeout(() => {
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.config.maxReconnectAttempts})`);
        this.connect();
      }, this.config.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached');
      this.stats.connectionStatus = 'error';
    }
  }
}

export const realTimeDataService = new RealTimeDataService();
export default realTimeDataService;
