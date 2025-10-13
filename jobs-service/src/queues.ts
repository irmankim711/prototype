import { Queue, QueueScheduler } from 'bullmq';
import { redisConfig, queues } from './config';

const defaultOpts = { connection: redisConfig, defaultJobOptions: { attempts: 5, backoff: { type: 'exponential', delay: 30000 } } };

export const reportsQueue = new Queue(queues.reports, defaultOpts);
export const emailsQueue = new Queue(queues.emails, defaultOpts);
export const syncQueue = new Queue(queues.sync, defaultOpts);
export const filesQueue = new Queue(queues.files, defaultOpts);
export const maintenanceQueue = new Queue(queues.maintenance, defaultOpts);

// Ensure stalled jobs handled
new QueueScheduler(queues.reports, { connection: redisConfig });
new QueueScheduler(queues.emails, { connection: redisConfig });
new QueueScheduler(queues.sync, { connection: redisConfig });
new QueueScheduler(queues.files, { connection: redisConfig });
new QueueScheduler(queues.maintenance, { connection: redisConfig });
