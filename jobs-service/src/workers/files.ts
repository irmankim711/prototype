import { Job } from 'bullmq';
import { processFile } from '../../lib/files';

export async function filesProcessor(job: Job) {
  const { fileId } = job.data;
  job.log(`Processing file ${fileId}`);
  await processFile(fileId);
  job.updateProgress(100);
  return { status: 'processed' };
}
