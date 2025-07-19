"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.register = register;
exports.login = login;
exports.refreshToken = refreshToken;
exports.verifyEmail = verifyEmail;
exports.forgotPassword = forgotPassword;
exports.resetPassword = resetPassword;
exports.logout = logout;
const bcryptjs_1 = __importDefault(require("bcryptjs"));
const jsonwebtoken_1 = __importDefault(require("jsonwebtoken"));
const uuid_1 = require("uuid");
const db_1 = require("../utils/db");
const email_1 = require("../utils/email");
const ACCESS_TOKEN_EXP = '15m';
const REFRESH_TOKEN_EXP = '30d';
function generateAccessToken(payload) {
    return jsonwebtoken_1.default.sign(payload, process.env.JWT_ACCESS_SECRET, { expiresIn: ACCESS_TOKEN_EXP });
}
function generateRefreshToken(payload) {
    return jsonwebtoken_1.default.sign(payload, process.env.JWT_REFRESH_SECRET, { expiresIn: REFRESH_TOKEN_EXP });
}
async function register(req, res) {
    const { email, password, organizationName } = req.body;
    if (!email || !password)
        return res.status(400).json({ error: 'Missing fields' });
    const client = await db_1.pool.connect();
    try {
        const existing = await client.query('SELECT id FROM users WHERE email=$1', [email]);
        if (existing.rowCount)
            return res.status(409).json({ error: 'Email already exists' });
        let orgId;
        if (organizationName) {
            const orgRes = await client.query('INSERT INTO organizations(name) VALUES($1) RETURNING id', [organizationName]);
            orgId = orgRes.rows[0].id;
        }
        else {
            const defaultOrg = await client.query('SELECT id FROM organizations LIMIT 1');
            orgId = defaultOrg.rows[0]?.id;
        }
        const passwordHash = await bcryptjs_1.default.hash(password, 12);
        const userRes = await client.query(`INSERT INTO users(email, password_hash, organization_id, role)
      VALUES($1,$2,$3,'Admin') RETURNING id, organization_id, role`, [email, passwordHash, orgId]);
        const user = userRes.rows[0];
        const verifyToken = (0, uuid_1.v4)();
        await client.query('INSERT INTO email_verifications(id, user_id) VALUES($1,$2)', [verifyToken, user.id]);
        await (0, email_1.sendVerificationEmail)(email, verifyToken);
        return res.status(201).json({ message: 'Registered. Please verify your email.' });
    }
    catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Registration failed' });
    }
    finally {
        client.release();
    }
}
async function login(req, res) {
    const { email, password } = req.body;
    const client = await db_1.pool.connect();
    try {
        const userRes = await client.query('SELECT * FROM users WHERE email=$1', [email]);
        if (!userRes.rowCount)
            return res.status(401).json({ error: 'Invalid credentials' });
        const user = userRes.rows[0];
        if (user.locked_until && new Date(user.locked_until) > new Date()) {
            return res.status(423).json({ error: 'Account locked. Try later.' });
        }
        const passOk = await bcryptjs_1.default.compare(password, user.password_hash);
        if (!passOk) {
            await client.query('UPDATE users SET failed_attempts = failed_attempts + 1 WHERE id=$1', [user.id]);
            if (user.failed_attempts + 1 >= 5) {
                const lockUntil = new Date(Date.now() + 30 * 60 * 1000); // 30 minutes
                await client.query('UPDATE users SET locked_until=$1 WHERE id=$2', [lockUntil, user.id]);
            }
            return res.status(401).json({ error: 'Invalid credentials' });
        }
        // reset failed attempts
        await client.query('UPDATE users SET failed_attempts=0 WHERE id=$1', [user.id]);
        const payload = { id: user.id, organization_id: user.organization_id, role: user.role };
        const accessToken = generateAccessToken(payload);
        const refreshToken = generateRefreshToken({ ...payload, token_id: (0, uuid_1.v4)() });
        await client.query('INSERT INTO refresh_tokens(token, user_id, expires_at) VALUES($1,$2, NOW() + INTERVAL \'30 days\')', [refreshToken, user.id]);
        res.cookie('refreshToken', refreshToken, { httpOnly: true, secure: process.env.NODE_ENV === 'production', sameSite: 'strict', maxAge: 30 * 24 * 60 * 60 * 1000 });
        return res.json({ accessToken });
    }
    catch (err) {
        console.error(err);
        res.status(500).json({ error: 'Login failed' });
    }
    finally {
        client.release();
    }
}
async function refreshToken(req, res) {
    const token = req.body.refreshToken || req.cookies?.refreshToken;
    if (!token)
        return res.status(401).json({ error: 'Missing refresh token' });
    try {
        const payload = jsonwebtoken_1.default.verify(token, process.env.JWT_REFRESH_SECRET);
        const accessToken = generateAccessToken({ id: payload.id, organization_id: payload.organization_id, role: payload.role });
        return res.json({ accessToken });
    }
    catch (err) {
        return res.status(403).json({ error: 'Invalid refresh token' });
    }
}
async function verifyEmail(req, res) {
    const { token } = req.body;
    const client = await db_1.pool.connect();
    try {
        const verRes = await client.query('SELECT user_id FROM email_verifications WHERE id=$1', [token]);
        if (!verRes.rowCount)
            return res.status(400).json({ error: 'Invalid token' });
        const userId = verRes.rows[0].user_id;
        await client.query('UPDATE users SET is_verified=true WHERE id=$1', [userId]);
        await client.query('DELETE FROM email_verifications WHERE id=$1', [token]);
        return res.json({ message: 'Email verified' });
    }
    catch (err) {
        res.status(500).json({ error: 'Verification failed' });
    }
    finally {
        client.release();
    }
}
async function forgotPassword(req, res) {
    const { email } = req.body;
    const client = await db_1.pool.connect();
    try {
        const userRes = await client.query('SELECT id FROM users WHERE email=$1', [email]);
        if (!userRes.rowCount)
            return res.status(200).json({ message: 'If email exists, reset link sent' });
        const userId = userRes.rows[0].id;
        const resetId = (0, uuid_1.v4)();
        await client.query('INSERT INTO password_resets(id, user_id) VALUES($1,$2)', [resetId, userId]);
        await (0, email_1.sendResetPasswordEmail)(email, resetId);
        return res.json({ message: 'If email exists, reset link sent' });
    }
    catch (err) {
        res.status(500).json({ error: 'Failed to initiate reset' });
    }
    finally {
        client.release();
    }
}
async function resetPassword(req, res) {
    const { token, password } = req.body;
    const client = await db_1.pool.connect();
    try {
        const resetRes = await client.query('SELECT user_id FROM password_resets WHERE id=$1', [token]);
        if (!resetRes.rowCount)
            return res.status(400).json({ error: 'Invalid token' });
        const passHash = await bcryptjs_1.default.hash(password, 12);
        await client.query('UPDATE users SET password_hash=$1 WHERE id=$2', [passHash, resetRes.rows[0].user_id]);
        await client.query('DELETE FROM password_resets WHERE id=$1', [token]);
        res.json({ message: 'Password reset successful' });
    }
    catch (err) {
        res.status(500).json({ error: 'Failed to reset password' });
    }
    finally {
        client.release();
    }
}
async function logout(req, res) {
    // Invalidate refresh token (simple approach: delete from db)
    const token = req.cookies?.refreshToken;
    if (token) {
        try {
            await db_1.pool.query('DELETE FROM refresh_tokens WHERE token=$1', [token]);
        }
        catch (err) {
            console.error(err);
        }
    }
    res.clearCookie('refreshToken');
    res.json({ message: 'Logged out' });
}
