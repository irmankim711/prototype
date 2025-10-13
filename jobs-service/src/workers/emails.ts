import { Job } from 'bullmq';
import { sendEmail } from '../../lib/email';

export async function emailsProcessor(job: Job) {
  const { to, subject, html } = job.data;
  job.log(`Sending email to ${to}`);
  await sendEmail({ to, subject, html });
  job.updateProgress(100);
  return { status: 'sent' };
}
