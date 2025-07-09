import { Job } from 'bullmq';
import { generateReport } from '../../lib/report';

export async function reportsProcessor(job: Job) {
  const { formId } = job.data;
  job.log(`Generating report for form ${formId}`);
  const pdfBuffer = await generateReport(formId);
  // TODO: save to storage & update DB
  job.updateProgress(100);
  return { url: `/storage/reports/${formId}.pdf` };
}
