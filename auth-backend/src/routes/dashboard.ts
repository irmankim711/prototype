import { Router } from 'express';
import controller from '../controllers/dashboardController';
import { authenticateJWT } from '../middleware/auth';

const router = Router();
router.use(authenticateJWT);

// Form management
router.get('/forms', controller.getFormsList);

export default router;
