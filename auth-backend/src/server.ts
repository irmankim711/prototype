import express from 'express';
import helmet from 'helmet';
import cors from 'cors';
import morgan from 'morgan';
import dotenv from 'dotenv';
import rateLimiter from './middleware/rateLimiter';
import authRoutes from './routes/auth';
import { initDb } from './utils/db';

dotenv.config();

const PORT = process.env.PORT || 4000;

async function bootstrap() {
  await initDb();

  const app = express();
  app.use(helmet());
  app.use(cors({ origin: process.env.CORS_ORIGIN || '*', credentials: true }));
  app.use(express.json());
  app.use(rateLimiter);
  app.use(morgan('combined'));

  app.get('/health', (_, res) => res.json({ status: 'OK' }));
  app.use('/api/auth', authRoutes);

  app.use((err: any, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
    console.error(err);
    res.status(err.status || 500).json({ error: err.message || 'Internal Server Error' });
  });

  app.listen(PORT, () => {
    console.log(`Auth server running on port ${PORT}`);
  });
}

bootstrap().catch((err) => {
  console.error('Failed to bootstrap server', err);
  process.exit(1);
});
