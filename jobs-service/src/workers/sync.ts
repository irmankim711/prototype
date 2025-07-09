import { Job } from 'bullmq';
import { runSync } from '../../lib/sync';

export async function syncProcessor(job: Job) {
  const { source } = job.data;
  job.log(`Running data sync for ${source}`);
  await runSync(source);
  job.updateProgress(100);
  return { status: 'synced' };
}
