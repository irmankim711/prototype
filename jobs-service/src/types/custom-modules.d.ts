declare module 'dotenv' {
  const content: any;
  export = content;
}

declare module 'ioredis' {
  import { EventEmitter } from 'events';
  type RedisOptions = Record<string, any>; // Simplified
  class Redis extends EventEmitter {
    constructor(port?: number, host?: string, options?: RedisOptions);
    constructor(path?: string, options?: RedisOptions);
    get(key: string): Promise<string | null>;
    set(key: string, value: string, ...args: any[]): Promise<'OK' | null>;
    quit(): Promise<'OK'>;
    // Add other methods as needed
  }
  export = Redis;
}

declare module 'pg' {
  import { EventEmitter } from 'events';
  export interface ClientConfig {
    connectionString?: string;
  }
  export class Client extends EventEmitter {
    constructor(config?: ClientConfig);
    connect(): Promise<void>;
    query<T = any>(text: string, params?: any[]): Promise<{ rows: T[] }>;
    end(): Promise<void>;
  }
}
