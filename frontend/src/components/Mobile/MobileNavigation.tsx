/**
 * Mobile Navigation Component
 * Touch-optimized bottom navigation with haptic feedback
 */

import React from "react";
import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
// import { Link } from 'react-router-dom'; // TODO: Re-enable when needed
import {
  Home,
  FileText,
  BarChart3,
  Settings,
  Menu,
  Plus,
  Search,
  // Bell // TODO: Re-enable when needed
} from "lucide-react";

interface NavItem {
  icon: React.ComponentType<{ size?: number; className?: string }>;
  label: string;
  path: string;
  badge?: number;
  disabled?: boolean;
}

interface MobileNavigationProps {
  isVisible?: boolean;
  items?: NavItem[];
  onItemSelect?: (path: string) => void;
  className?: string;
}

const defaultNavItems: NavItem[] = [
  { icon: Home, label: "Dashboard", path: "/dashboard" },
  { icon: FileText, label: "Forms", path: "/forms" },
  { icon: BarChart3, label: "Reports", path: "/reports" },
  { icon: Settings, label: "Settings", path: "/settings" },
];

const MobileNavigation: React.FC<MobileNavigationProps> = ({
  isVisible = true,
  items = defaultNavItems,
  onItemSelect,
  className = "",
}) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [activeIndex, setActiveIndex] = useState(0);

  // Update active index based on current path
  useEffect(() => {
    const currentIndex = items.findIndex((item: any) =>
      location.pathname.startsWith(item.path)
    );
    if (currentIndex >= 0) {
      setActiveIndex(currentIndex);
    }
  }, [location.pathname, items]);

  // Haptic feedback for touch devices
  const triggerHapticFeedback = () => {
    if ("vibrate" in navigator) {
      navigator.vibrate(50);
    }
  };

  const handleItemPress = (item: NavItem, index: number) => {
    if (item.disabled) return;

    triggerHapticFeedback();
    setActiveIndex(index);

    if (onItemSelect) {
      onItemSelect(item.path);
    } else {
      navigate(item.path);
    }
  };

  if (!isVisible) return null;

  return (
    <nav
      className={`mobile-nav ${className}`}
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="mobile-nav-container">
        {items.map((item, index) => {
          const Icon = item.icon;
          const isActive = index === activeIndex;

          return (
            <button
              key={item.path}
              onClick={() => handleItemPress(item, index)}
              className={`mobile-nav-item ${isActive ? "active" : ""} ${
                item.disabled ? "disabled" : ""
              }`}
              aria-label={item.label}
              aria-current={isActive ? "page" : undefined}
              disabled={item.disabled}
              type="button"
            >
              <div className="mobile-nav-icon-container">
                <Icon size={20} className="mobile-nav-icon" />
                {item.badge && item.badge > 0 && (
                  <span
                    className="mobile-nav-badge"
                    aria-label={`${item.badge} notifications`}
                  >
                    {item.badge > 99 ? "99+" : item.badge}
                  </span>
                )}
              </div>
              <span className="mobile-nav-label">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
};

// Floating Action Button Component for mobile
interface FloatingActionButtonProps {
  onClick: () => void;
  icon?: React.ComponentType<{ size?: number; className?: string }>;
  label?: string;
  className?: string;
  disabled?: boolean;
}

export const FloatingActionButton: React.FC<FloatingActionButtonProps> = ({
  onClick,
  icon: Icon = Plus,
  label = "Add",
  className = "",
  disabled = false,
}) => {
  const handleClick = () => {
    if (disabled) return;

    // Haptic feedback
    if ("vibrate" in navigator) {
      navigator.vibrate(50);
    }

    onClick();
  };

  return (
    <button
      onClick={handleClick}
      className={`floating-action-button ${className} ${
        disabled ? "disabled" : ""
      }`}
      aria-label={label}
      disabled={disabled}
      type="button"
    >
      <Icon size={24} className="floating-action-button-icon" />
    </button>
  );
};

// Mobile Header Component
interface MobileHeaderProps {
  title: string;
  onMenuToggle?: () => void;
  onBack?: () => void;
  showBack?: boolean;
  showMenu?: boolean;
  rightActions?: React.ReactNode;
  className?: string;
  subtitle?: string;
}

export const MobileHeader: React.FC<MobileHeaderProps> = ({
  title,
  onMenuToggle,
  onBack,
  showBack = false,
  showMenu = false,
  rightActions,
  className = "",
  subtitle,
}) => {
  const navigate = useNavigate();

  const handleBack = () => {
    // Haptic feedback
    if ("vibrate" in navigator) {
      navigator.vibrate(50);
    }

    if (onBack) {
      onBack();
    } else {
      navigate(-1);
    }
  };

  const handleMenuToggle = () => {
    // Haptic feedback
    if ("vibrate" in navigator) {
      navigator.vibrate(50);
    }

    if (onMenuToggle) {
      onMenuToggle();
    }
  };

  return (
    <header className={`mobile-header ${className}`}>
      <div className="mobile-header-content">
        <div className="mobile-header-left">
          {showBack && (
            <button
              onClick={handleBack}
              className="mobile-header-back"
              aria-label="Go back"
              type="button"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M19 12H5M12 19L5 12L12 5"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          )}

          {showMenu && (
            <button
              onClick={handleMenuToggle}
              className="mobile-header-menu"
              aria-label="Open menu"
              type="button"
            >
              <Menu size={20} />
            </button>
          )}

          <div className="mobile-header-title-container">
            <h1 className="mobile-header-title">{title}</h1>
            {subtitle && <p className="mobile-header-subtitle">{subtitle}</p>}
          </div>
        </div>

        {rightActions && (
          <div className="mobile-header-actions">{rightActions}</div>
        )}
      </div>
    </header>
  );
};

// Tab Bar Component for mobile sections
interface TabItem {
  id: string;
  label: string;
  icon?: React.ComponentType<{ size?: number; className?: string }>;
  disabled?: boolean;
  badge?: number;
}

interface MobileTabBarProps {
  tabs: TabItem[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  className?: string;
}

export const MobileTabBar: React.FC<MobileTabBarProps> = ({
  tabs,
  activeTab,
  onTabChange,
  className = "",
}) => {
  const handleTabPress = (tabId: string, disabled?: boolean) => {
    if (disabled) return;

    // Haptic feedback
    if ("vibrate" in navigator) {
      navigator.vibrate(30);
    }

    onTabChange(tabId);
  };

  return (
    <div className={`mobile-tab-bar ${className}`} role="tablist">
      {tabs.map((tab: any) => {
        const Icon = tab.icon;
        const isActive = tab.id === activeTab;

        return (
          <button
            key={tab.id}
            onClick={() => handleTabPress(tab.id, tab.disabled)}
            className={`mobile-tab-item ${isActive ? "active" : ""} ${
              tab.disabled ? "disabled" : ""
            }`}
            role="tab"
            aria-selected={isActive}
            aria-disabled={tab.disabled}
            disabled={tab.disabled}
            type="button"
          >
            <div className="mobile-tab-content">
              {Icon && (
                <div className="mobile-tab-icon-container">
                  <Icon size={18} className="mobile-tab-icon" />
                  {tab.badge && tab.badge > 0 && (
                    <span
                      className="mobile-tab-badge"
                      aria-label={`${tab.badge} items`}
                    >
                      {tab.badge > 99 ? "99+" : tab.badge}
                    </span>
                  )}
                </div>
              )}
              <span className="mobile-tab-label">{tab.label}</span>
            </div>
          </button>
        );
      })}
    </div>
  );
};

// Search Bar Component for mobile
interface MobileSearchBarProps {
  value: string;
  onChange: (value: string) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  placeholder?: string;
  className?: string;
  autoFocus?: boolean;
}

export const MobileSearchBar: React.FC<MobileSearchBarProps> = ({
  value,
  onChange,
  onFocus,
  onBlur,
  placeholder = "Search...",
  className = "",
  autoFocus = false,
}) => {
  const [isFocused, setIsFocused] = useState(false);

  const handleFocus = () => {
    setIsFocused(true);
    onFocus?.();
  };

  const handleBlur = () => {
    setIsFocused(false);
    onBlur?.();
  };

  const handleClear = () => {
    onChange("");
    // Haptic feedback
    if ("vibrate" in navigator) {
      navigator.vibrate(30);
    }
  };

  return (
    <div
      className={`mobile-search-bar ${isFocused ? "focused" : ""} ${className}`}
    >
      <div className="mobile-search-input-container">
        <Search size={20} className="mobile-search-icon" />
        <input
          type="text"
          value={value}
          onChange={(e: any) => onChange(e.target.value)}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          className="mobile-search-input"
          autoFocus={autoFocus}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
          spellCheck={false}
        />
        {value && (
          <button
            onClick={handleClear}
            className="mobile-search-clear"
            aria-label="Clear search"
            type="button"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path
                d="M18 6L6 18M6 6L18 18"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default MobileNavigation;
