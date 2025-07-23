import { Response } from 'express';
import { pool } from '../utils/db';
import { AuthRequest } from '../middleware/auth';

export async function getDashboardStats(req: AuthRequest, res: Response) {
  if (!req.user) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  const client = await pool.connect();
  try {
    // Get total submissions count
    const submissionsResult = await client.query(`
      SELECT COUNT(*) as total_submissions 
      FROM submissions s
      JOIN forms f ON s.form_id = f.id 
      WHERE f.user_id = $1
    `, [req.user.id]);

    // Get active users count (users who submitted in last 30 days)
    const activeUsersResult = await client.query(`
      SELECT COUNT(DISTINCT s.user_id) as active_users
      FROM submissions s
      JOIN forms f ON s.form_id = f.id
      WHERE f.user_id = $1 AND s.submitted_at >= NOW() - INTERVAL '30 days'
    `, [req.user.id]);

    // Get average score (assuming submissions have a score field in JSON data)
    const avgScoreResult = await client.query(`
      SELECT AVG(CAST(s.data->>'score' AS NUMERIC)) as average_score
      FROM submissions s
      JOIN forms f ON s.form_id = f.id
      WHERE f.user_id = $1 AND s.data->>'score' IS NOT NULL
    `, [req.user.id]);

    // Get top score
    const topScoreResult = await client.query(`
      SELECT MAX(CAST(s.data->>'score' AS NUMERIC)) as top_score
      FROM submissions s
      JOIN forms f ON s.form_id = f.id
      WHERE f.user_id = $1 AND s.data->>'score' IS NOT NULL
    `, [req.user.id]);

    // Get median score
    const medianScoreResult = await client.query(`
      SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY CAST(s.data->>'score' AS NUMERIC)) as median_score
      FROM submissions s
      JOIN forms f ON s.form_id = f.id
      WHERE f.user_id = $1 AND s.data->>'score' IS NOT NULL
    `, [req.user.id]);

    const stats = {
      totalSubmissions: parseInt(submissionsResult.rows[0]?.total_submissions || '0'),
      activeUsers: parseInt(activeUsersResult.rows[0]?.active_users || '0'),
      averageScore: parseFloat(avgScoreResult.rows[0]?.average_score || '0'),
      topScore: parseFloat(topScoreResult.rows[0]?.top_score || '0'),
      medianScore: parseFloat(medianScoreResult.rows[0]?.median_score || '0')
    };

    res.json(stats);
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    res.status(500).json({ error: 'Failed to fetch dashboard statistics' });
  } finally {
    client.release();
  }
}

export async function getChartData(req: AuthRequest, res: Response) {
  if (!req.user) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  const { chartType, field, groupBy } = req.query;
  const client = await pool.connect();
  
  try {
    let query = '';
    let params = [req.user.id];

    if (groupBy === 'Name') {
      // Group by user name/email
      query = `
        SELECT 
          u.email as name,
          AVG(CAST(s.data->>'score' AS NUMERIC)) as score,
          COUNT(s.id) as submission_count
        FROM submissions s
        JOIN forms f ON s.form_id = f.id
        JOIN users u ON s.user_id = u.id
        WHERE f.user_id = $1 AND s.data->>'score' IS NOT NULL
        GROUP BY u.email, u.id
        ORDER BY score DESC
        LIMIT 10
      `;
    } else if (groupBy === 'Date') {
      // Group by date
      query = `
        SELECT 
          DATE(s.submitted_at) as name,
          AVG(CAST(s.data->>'score' AS NUMERIC)) as score,
          COUNT(s.id) as submission_count
        FROM submissions s
        JOIN forms f ON s.form_id = f.id
        WHERE f.user_id = $1 AND s.data->>'score' IS NOT NULL
        GROUP BY DATE(s.submitted_at)
        ORDER BY name DESC
        LIMIT 10
      `;
    } else {
      // Default to form grouping
      query = `
        SELECT 
          f.title as name,
          AVG(CAST(s.data->>'score' AS NUMERIC)) as score,
          COUNT(s.id) as submission_count
        FROM submissions s
        JOIN forms f ON s.form_id = f.id
        WHERE f.user_id = $1 AND s.data->>'score' IS NOT NULL
        GROUP BY f.id, f.title
        ORDER BY score DESC
        LIMIT 10
      `;
    }

    const result = await client.query(query, params);
    
    const chartData = result.rows.map(row => ({
      name: row.name || 'Unknown',
      score: parseFloat(row.score || '0'),
      submissionCount: parseInt(row.submission_count || '0')
    }));

    res.json(chartData);
  } catch (error) {
    console.error('Error fetching chart data:', error);
    res.status(500).json({ error: 'Failed to fetch chart data' });
  } finally {
    client.release();
  }
}

export async function getRecentActivity(req: AuthRequest, res: Response) {
  if (!req.user) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  
  const client = await pool.connect();
  
  try {
    const query = `
      SELECT 
        s.id,
        s.submitted_at,
        s.data,
        f.title as form_title,
        u.email as user_email
      FROM submissions s
      JOIN forms f ON s.form_id = f.id
      JOIN users u ON s.user_id = u.id
      WHERE f.user_id = $1
      ORDER BY s.submitted_at DESC
      LIMIT 20
    `;

    const result = await client.query(query, [req.user.id]);
    
    const activities = result.rows.map(row => ({
      id: row.id,
      submittedAt: row.submitted_at,
      formTitle: row.form_title,
      userEmail: row.user_email,
      data: row.data
    }));

    res.json(activities);
  } catch (error) {
    console.error('Error fetching recent activity:', error);
    res.status(500).json({ error: 'Failed to fetch recent activity' });
  } finally {
    client.release();
  }
}

import { AuthRequest } from '../middleware/auth';
import { Response } from 'express';
import { pool } from '../utils/db';

export const getFormsList = async (req: AuthRequest, res: Response) => {
  try {
    const result = await pool.query(
      `SELECT id, title, description, is_active, 
       created_at FROM forms WHERE user_id = $1`,
      [req.user?.id]
    );
    res.json(result.rows);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch forms' });
  }
};

export default {
  getFormsList
};
