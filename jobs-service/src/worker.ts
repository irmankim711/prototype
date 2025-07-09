import { Worker, Job } from 'bullmq';
import { redisConfig, queues } from './config';
import { reportsProcessor } from './workers/reports';
import { emailsProcessor } from './workers/emails';
import { syncProcessor } from './workers/sync';
import { filesProcessor } from './workers/files';
import { maintenanceProcessor } from './workers/maintenance';

function createWorker(name: string, processor: (job: Job) => Promise<any>) {
  return new Worker(name, processor, {
    connection: redisConfig,
    concurrency: 5
  });
}

createWorker(queues.reports, reportsProcessor);
createWorker(queues.emails, emailsProcessor);
createWorker(queues.sync, syncProcessor);
createWorker(queues.files, filesProcessor);
createWorker(queues.maintenance, maintenanceProcessor);

process.on('SIGTERM', () => process.exit(0));
