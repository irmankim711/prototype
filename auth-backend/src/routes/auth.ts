import { Router } from 'express';
import * as controller from '../controllers/authController';
import { authenticateJWT } from '../middleware/auth';

const router = Router();

// Public endpoints
router.post('/register', controller.register);
router.post('/login', controller.login);
router.post('/refresh', controller.refreshToken);
router.post('/verify-email', controller.verifyEmail);
router.post('/forgot-password', controller.forgotPassword);
router.post('/reset-password', controller.resetPassword);

// Protected endpoints
router.post('/logout', authenticateJWT, controller.logout);

export default router;
