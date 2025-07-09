import { Pool } from 'pg';
import fs from 'fs';
import path from 'path';

export const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : undefined
});

export async function initDb() {
  const client = await pool.connect();
  try {
    // run schema migrations if not applied
    const schemaSql = fs.readFileSync(path.join(__dirname, '../../schema.sql'), 'utf-8');
    await client.query(schemaSql);
    console.log('Database initialized');
  } finally {
    client.release();
  }
}
