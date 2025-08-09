/**
 * Mobile-Optimized Dashboard Component
 * Responsive dashboard with touch interactions and mobile-first design
 */

import React from "react";
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  Plus,
  BarChart3,
  FileText,
  Users,
  TrendingUp,
  Calendar,
  Bell,
  Search,
  Filter,
  MoreVertical,
} from "lucide-react";
import {
  MobileHeader,
  MobileTabBar,
  FloatingActionButton,
} from "./MobileNavigation";
import {
  PullToRefresh,
  MobileCard,
  MobileButton,
  MobileSkeleton,
} from "./MobileComponents";
import { useViewport, useNetworkStatus } from "../../hooks/useTouchGestures";

interface DashboardStats {
  totalForms: number;
  totalSubmissions: number;
  activeForms: number;
  monthlySubmissions: number;
  weeklyGrowth: number;
  conversionRate: number;
}

interface RecentActivity {
  id: string;
  type: "form_created" | "submission" | "form_published" | "form_updated";
  title: string;
  description: string;
  timestamp: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
}

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ size?: number; className?: string }>;
  action: () => void;
  color: string;
}

const MobileDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { isMobile, isTablet } = useViewport();
  const { isOnline, isSlowConnection } = useNetworkStatus();

  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeTab, setActiveTab] = useState("overview");
  const [showSearch, setShowSearch] = useState(false);

  // Fetch dashboard data
  const fetchDashboardData = async () => {
    try {
      // Simulate API call
      await new Promise((resolve: any) =>
        setTimeout(resolve, isSlowConnection ? 3000 : 1000)
      );

      const mockStats: DashboardStats = {
        totalForms: 24,
        totalSubmissions: 1337,
        activeForms: 18,
        monthlySubmissions: 245,
        weeklyGrowth: 12.5,
        conversionRate: 78.3,
      };

      const mockActivity: RecentActivity[] = [
        {
          id: "1",
          type: "submission",
          title: "New Contact Form Submission",
          description: "John Doe submitted contact form",
          timestamp: "2 minutes ago",
          icon: FileText,
        },
        {
          id: "2",
          type: "form_created",
          title: "Survey Form Created",
          description: "Customer satisfaction survey",
          timestamp: "1 hour ago",
          icon: Plus,
        },
        {
          id: "3",
          type: "form_published",
          title: "Registration Form Published",
          description: "Event registration form is now live",
          timestamp: "3 hours ago",
          icon: TrendingUp,
        },
      ];

      setStats(mockStats);
      setRecentActivity(mockActivity);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  // Handle pull-to-refresh
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    setRefreshing(false);
  };

  // Quick actions configuration
  const quickActions: QuickAction[] = [
    {
      id: "create-form",
      title: "Create Form",
      description: "Build a new form",
      icon: Plus,
      action: () => navigate("/forms/new"),
      color: "bg-blue-500",
    },
    {
      id: "view-analytics",
      title: "Analytics",
      description: "View performance",
      icon: BarChart3,
      action: () => navigate("/analytics"),
      color: "bg-green-500",
    },
    {
      id: "manage-forms",
      title: "All Forms",
      description: "Manage forms",
      icon: FileText,
      action: () => navigate("/forms"),
      color: "bg-purple-500",
    },
    {
      id: "view-reports",
      title: "Reports",
      description: "Generate reports",
      icon: Calendar,
      action: () => navigate("/reports"),
      color: "bg-orange-500",
    },
  ];

  // Tab configuration
  const tabs = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "activity", label: "Activity", icon: Bell },
    { id: "forms", label: "Forms", icon: FileText },
    { id: "users", label: "Users", icon: Users },
  ];

  useEffect(() => {
    fetchDashboardData();
  }, []);

  // Render stat card
  const renderStatCard = (
    title: string,
    value: number | string,
    subtitle?: string,
    trend?: number
  ) => (
    <MobileCard className="stat-card" interactive>
      <div className="stat-card-content">
        <h3 className="stat-title">{title}</h3>
        <div className="stat-value">{value}</div>
        {subtitle && <p className="stat-subtitle">{subtitle}</p>}
        {trend !== undefined && (
          <div className={`stat-trend ${trend >= 0 ? "positive" : "negative"}`}>
            <TrendingUp size={16} />
            <span>{Math.abs(trend)}%</span>
          </div>
        )}
      </div>
    </MobileCard>
  );

  // Render overview tab
  const renderOverviewTab = () => (
    <div className="dashboard-overview">
      {/* Stats Grid */}
      <div className="stats-grid">
        {loading ? (
          Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="stat-card-skeleton">
              <MobileSkeleton variant="rectangular" height={80} />
            </div>
          ))
        ) : (
          <>
            {renderStatCard("Total Forms", stats?.totalForms || 0)}
            {renderStatCard(
              "Submissions",
              stats?.totalSubmissions || 0,
              "This month",
              stats?.weeklyGrowth
            )}
            {renderStatCard("Active Forms", stats?.activeForms || 0)}
            {renderStatCard(
              "Conversion",
              `${stats?.conversionRate || 0}%`,
              "Average rate"
            )}
          </>
        )}
      </div>

      {/* Quick Actions */}
      <section className="quick-actions-section">
        <h2 className="section-title">Quick Actions</h2>
        <div className="quick-actions-grid">
          {quickActions.map((action: any) => (
            <MobileCard
              key={action.id}
              className="quick-action-card"
              onTap={action.action}
              interactive
            >
              <div className={`quick-action-icon ${action.color}`}>
                <action.icon size={24} />
              </div>
              <div className="quick-action-content">
                <h3 className="quick-action-title">{action.title}</h3>
                <p className="quick-action-description">{action.description}</p>
              </div>
            </MobileCard>
          ))}
        </div>
      </section>

      {/* Recent Activity Preview */}
      <section className="recent-activity-preview">
        <div className="section-header">
          <h2 className="section-title">Recent Activity</h2>
          <MobileButton
            variant="ghost"
            size="small"
            onClick={() => setActiveTab("activity")}
          >
            View All
          </MobileButton>
        </div>

        {loading ? (
          <div className="activity-skeleton">
            {Array.from({ length: 3 }).map((_, index) => (
              <div key={index} className="activity-item-skeleton">
                <MobileSkeleton variant="circular" width={40} height={40} />
                <div className="activity-text-skeleton">
                  <MobileSkeleton variant="text" width="70%" />
                  <MobileSkeleton variant="text" width="50%" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="activity-list">
            {recentActivity.slice(0, 3).map((activity: any) => (
              <div key={activity.id} className="activity-item">
                <div className="activity-icon">
                  <activity.icon size={20} />
                </div>
                <div className="activity-content">
                  <h4 className="activity-title">{activity.title}</h4>
                  <p className="activity-description">{activity.description}</p>
                  <span className="activity-timestamp">
                    {activity.timestamp}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );

  // Render activity tab
  const renderActivityTab = () => (
    <div className="dashboard-activity">
      <div className="activity-filters">
        <MobileButton
          variant="ghost"
          size="small"
          startIcon={<Filter size={16} />}
        >
          Filter
        </MobileButton>
      </div>

      {loading ? (
        <div className="activity-skeleton">
          {Array.from({ length: 8 }).map((_, index) => (
            <div key={index} className="activity-item-skeleton">
              <MobileSkeleton variant="circular" width={40} height={40} />
              <div className="activity-text-skeleton">
                <MobileSkeleton variant="text" width="80%" />
                <MobileSkeleton variant="text" width="60%" />
                <MobileSkeleton variant="text" width="40%" />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="activity-list">
          {recentActivity.map((activity: any) => (
            <MobileCard key={activity.id} className="activity-card" interactive>
              <div className="activity-item">
                <div className="activity-icon">
                  <activity.icon size={24} />
                </div>
                <div className="activity-content">
                  <h4 className="activity-title">{activity.title}</h4>
                  <p className="activity-description">{activity.description}</p>
                  <span className="activity-timestamp">
                    {activity.timestamp}
                  </span>
                </div>
                <button className="activity-more">
                  <MoreVertical size={16} />
                </button>
              </div>
            </MobileCard>
          ))}
        </div>
      )}
    </div>
  );

  // Render forms tab
  const renderFormsTab = () => (
    <div className="dashboard-forms">
      <div className="forms-header">
        <MobileButton
          variant="primary"
          onClick={() => navigate("/forms/new")}
          startIcon={<Plus size={16} />}
        >
          New Form
        </MobileButton>
      </div>

      <div className="forms-list">
        {/* Forms list content would go here */}
        <p className="coming-soon">Forms management coming soon...</p>
      </div>
    </div>
  );

  // Render users tab
  const renderUsersTab = () => (
    <div className="dashboard-users">
      <div className="users-stats">
        {renderStatCard("Total Users", "1,234")}
        {renderStatCard("Active Today", "89")}
      </div>

      <div className="users-list">
        {/* Users list content would go here */}
        <p className="coming-soon">User management coming soon...</p>
      </div>
    </div>
  );

  // Render tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case "overview":
        return renderOverviewTab();
      case "activity":
        return renderActivityTab();
      case "forms":
        return renderFormsTab();
      case "users":
        return renderUsersTab();
      default:
        return renderOverviewTab();
    }
  };

  // Show offline indicator
  if (!isOnline) {
    return (
      <div className="offline-dashboard">
        <MobileHeader title="Dashboard" />
        <div className="offline-content">
          <div className="offline-icon">📡</div>
          <h2>You're offline</h2>
          <p>Please check your internet connection and try again.</p>
          <MobileButton onClick={() => window.location.reload()}>
            Retry
          </MobileButton>
        </div>
      </div>
    );
  }

  return (
    <div className="mobile-dashboard">
      <MobileHeader
        title="Dashboard"
        rightActions={
          <button
            onClick={() => setShowSearch(!showSearch)}
            className="header-action-button"
            aria-label="Search"
          >
            <Search size={20} />
          </button>
        }
      />

      {/* Search Bar (conditional) */}
      {showSearch && (
        <div className="dashboard-search">
          <input
            type="text"
            placeholder="Search dashboard..."
            className="search-input"
            autoFocus
          />
        </div>
      )}

      {/* Connection Status */}
      {isSlowConnection && (
        <div className="connection-warning">
          <span>⚠️ Slow connection detected</span>
        </div>
      )}

      {/* Tab Navigation */}
      <MobileTabBar
        tabs={tabs}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Main Content */}
      <PullToRefresh onRefresh={handleRefresh} disabled={loading}>
        <div className="dashboard-content">{renderTabContent()}</div>
      </PullToRefresh>

      {/* Floating Action Button (mobile only) */}
      {isMobile && (
        <FloatingActionButton
          onClick={() => navigate("/forms/new")}
          label="Create Form"
        />
      )}
    </div>
  );
};

export default MobileDashboard;
