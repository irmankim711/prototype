declare module 'pg' {
  import { EventEmitter } from 'events';
  export interface PoolConfig {
    connectionString?: string;
    ssl?: any;
  }
  export class Pool extends EventEmitter {
    constructor(config?: PoolConfig);
    connect(): Promise<void>;
    query<T = any>(text: string, params?: any[]): Promise<{ rows: T[] }>;
    end(): Promise<void>;
  }
}
