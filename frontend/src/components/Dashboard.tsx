import React, { useState, useEffect } from "react";
import "./Dashboard.css";
import {
  fetchDashboardStats,
  fetchRecentActivity,
  fetchChartData,
  fetchFileStats,
  getCurrentUser,
} from "../services/api";
import type {
  DashboardStats,
  Report,
  ChartData,
  FileStats,
  User,
} from "../services/api";

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<Report[]>([]);
  const [chartData, setChartData] = useState<ChartData | null>(null);
  const [fileStats, setFileStats] = useState<FileStats | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Load all dashboard data in parallel
      const [statsData, activityData, chartResponse, fileStatsData, userData] =
        await Promise.all([
          fetchDashboardStats(),
          fetchRecentActivity(5),
          fetchChartData("reports_by_status"),
          fetchFileStats(),
          getCurrentUser(),
        ]);

      setStats(statsData);
      setRecentActivity(activityData.recent_activity);
      setChartData(chartResponse);
      setFileStats(fileStatsData);
      setUser(userData);
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
      setError("Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Welcome to StratoSys Dashboard</h1>
        {user && <p>Hello, {user.email}!</p>}
      </div>

      <div className="dashboard-grid">
        {/* Stats Cards */}
        <div className="stats-section">
          <h2>Statistics</h2>
          {stats && (
            <div className="stats-cards">
              <div className="stat-card">
                <h3>Total Reports</h3>
                <p className="stat-number">{stats.totalReports}</p>
              </div>
              <div className="stat-card">
                <h3>Completed Reports</h3>
                <p className="stat-number">{stats.completedReports}</p>
              </div>
              <div className="stat-card">
                <h3>Success Rate</h3>
                <p className="stat-number">{stats.successRate}%</p>
              </div>
              <div className="stat-card">
                <h3>Avg Processing Time</h3>
                <p className="stat-number">{stats.avgProcessingTime}min</p>
              </div>
            </div>
          )}
        </div>

        {/* File Stats */}
        <div className="file-stats-section">
          <h2>File Statistics</h2>
          {fileStats && (
            <div className="file-stats">
              <p>Total Files: {fileStats.total_files}</p>
              <p>Total Size: {fileStats.total_size_mb.toFixed(2)} MB</p>
              <p>Public Files: {fileStats.public_files}</p>
              <p>Private Files: {fileStats.private_files}</p>
              <p>Weekly Uploads: {fileStats.weekly_uploads}</p>
            </div>
          )}
        </div>

        {/* Chart Data */}
        <div className="chart-section">
          <h2>Report Status Distribution</h2>
          {chartData && (
            <div className="chart-data">
              <h3>Chart Type: {chartData.type}</h3>
              <div className="chart-labels">
                {chartData.data.labels.map((label, index) => (
                  <div key={label} className="chart-item">
                    <span className="label">{label}</span>
                    <span className="value">{chartData.data.data[index]}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="activity-section">
          <h2>Recent Activity</h2>
          {recentActivity.length > 0 ? (
            <div className="activity-list">
              {recentActivity.map((report) => (
                <div key={report.id} className="activity-item">
                  <h4>{report.title}</h4>
                  <p>
                    Status:{" "}
                    <span className={`status-${report.status}`}>
                      {report.status}
                    </span>
                  </p>
                  <p>
                    Created: {new Date(report.createdAt).toLocaleDateString()}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p>No recent activity</p>
          )}
        </div>
      </div>

      <div className="dashboard-actions">
        <button onClick={loadDashboardData} className="refresh-btn">
          Refresh Dashboard
        </button>
      </div>
    </div>
  );
};
