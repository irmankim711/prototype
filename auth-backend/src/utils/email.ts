import nodemailer from 'nodemailer';

type Template = 'verify' | 'reset';

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: Number(process.env.SMTP_PORT) || 587,
  secure: false,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS
  }
});

async function sendEmail(to: string, subject: string, html: string) {
  await transporter.sendMail({ from: process.env.EMAIL_FROM, to, subject, html });
}

export async function sendVerificationEmail(email: string, token: string) {
  const link = `${process.env.FRONTEND_URL}/verify-email?token=${token}`;
  const html = `<p>Please verify your email by clicking <a href="${link}">here</a>.</p>`;
  await sendEmail(email, 'Verify your email', html);
}

export async function sendResetPasswordEmail(email: string, token: string) {
  const link = `${process.env.FRONTEND_URL}/reset-password?token=${token}`;
  const html = `<p>Reset your password by clicking <a href="${link}">here</a>.</p>`;
  await sendEmail(email, 'Reset your password', html);
}
