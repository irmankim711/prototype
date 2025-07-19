"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.sendVerificationEmail = sendVerificationEmail;
exports.sendResetPasswordEmail = sendResetPasswordEmail;
const nodemailer_1 = __importDefault(require("nodemailer"));
const transporter = nodemailer_1.default.createTransport({
    host: process.env.SMTP_HOST,
    port: Number(process.env.SMTP_PORT) || 587,
    secure: false,
    auth: {
        user: process.env.SMTP_USER,
        pass: process.env.SMTP_PASS
    }
});
async function sendEmail(to, subject, html) {
    await transporter.sendMail({ from: process.env.EMAIL_FROM, to, subject, html });
}
async function sendVerificationEmail(email, token) {
    const link = `${process.env.FRONTEND_URL}/verify-email?token=${token}`;
    const html = `<p>Please verify your email by clicking <a href="${link}">here</a>.</p>`;
    await sendEmail(email, 'Verify your email', html);
}
async function sendResetPasswordEmail(email, token) {
    const link = `${process.env.FRONTEND_URL}/reset-password?token=${token}`;
    const html = `<p>Reset your password by clicking <a href="${link}">here</a>.</p>`;
    await sendEmail(email, 'Reset your password', html);
}
