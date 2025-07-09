import { Job } from 'bullmq';

export async function maintenanceProcessor(job: Job) {
  job.log('Running maintenance task');
  // perform cleanup etc.
  job.updateProgress(100);
  return { status: 'done' };
}
