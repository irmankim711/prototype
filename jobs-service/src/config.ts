import dotenv from 'dotenv';
import { RedisOptions } from 'ioredis';

dotenv.config();

export const redisConfig: RedisOptions = {
  host: process.env.REDIS_HOST || '127.0.0.1',
  port: Number(process.env.REDIS_PORT) || 6379,
  password: process.env.REDIS_PASSWORD || undefined,
  tls: process.env.REDIS_TLS === 'true' ? {} : undefined
};

export const queues = {
  reports: 'reports',
  emails: 'emails',
  sync: 'sync',
  files: 'files',
  maintenance: 'maintenance'
};

export const isProd = process.env.NODE_ENV === 'production';
