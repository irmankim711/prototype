/**
 * Mobile-Optimized Components
 * Touch-friendly UI components designed for mobile devices
 */

import { useState, useEffect, useRef } from "react";
import type { ReactNode } from "react";
import {
  useTouchGestures,
  usePullToRefresh,
} from "../../hooks/useTouchGestures";
// import { useViewport } from '../../hooks/useTouchGestures'; // TODO: Re-enable when needed
// import { MobileHeader, MobileTabBar } from './MobileNavigation'; // TODO: Re-enable when needed

// Pull-to-Refresh Component
interface PullToRefreshProps {
  onRefresh: () => Promise<void>;
  children: ReactNode;
  threshold?: number;
  className?: string;
  disabled?: boolean;
}

export const PullToRefresh: React.FC<PullToRefreshProps> = ({
  onRefresh,
  children,
  threshold = 80,
  className = "",
  disabled = false,
}) => {
  const {
    containerRef,
    isPulling,
    isRefreshing,
    pullDistance,
    shouldShowIndicator,
  } = usePullToRefresh({
    onRefresh,
    threshold,
    enabled: !disabled,
  });

  const getIndicatorText = () => {
    if (isRefreshing) return "Refreshing...";
    if (pullDistance >= threshold) return "Release to refresh";
    return "Pull to refresh";
  };

  const getIndicatorIcon = () => {
    if (isRefreshing) {
      return (
        <div className="pull-to-refresh-spinner">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 2V6M12 18V22M4.93 4.93L7.76 7.76M16.24 16.24L19.07 19.07M2 12H6M18 12H22M4.93 19.07L7.76 16.24M16.24 7.76L19.07 4.93"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      );
    }

    const rotation = Math.min((pullDistance / threshold) * 180, 180);
    return (
      <div
        className="pull-to-refresh-arrow"
        style={{ transform: `rotate(${rotation}deg)` }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 19V5M5 12L12 5L19 12"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    );
  };

  return (
    <div className={`pull-to-refresh ${className}`}>
      {shouldShowIndicator && (
        <div
          className={`pull-to-refresh-indicator ${
            isRefreshing ? "refreshing" : ""
          }`}
          style={{
            transform: `translateY(${Math.min(pullDistance, threshold)}px)`,
            opacity: Math.min(pullDistance / (threshold * 0.5), 1),
          }}
        >
          {getIndicatorIcon()}
          <span className="pull-to-refresh-text">{getIndicatorText()}</span>
        </div>
      )}

      <div
        ref={containerRef}
        className="pull-to-refresh-content"
        style={{
          transform:
            isPulling || isRefreshing
              ? `translateY(${Math.min(pullDistance, threshold)}px)`
              : "none",
          transition: isPulling ? "none" : "transform 0.3s ease",
        }}
      >
        {children}
      </div>
    </div>
  );
};

// Mobile Modal Component
interface MobileModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: ReactNode;
  className?: string;
  showHandle?: boolean;
  closeOnBackdrop?: boolean;
  maxHeight?: string;
}

export const MobileModal: React.FC<MobileModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  className = "",
  showHandle = true,
  closeOnBackdrop = true,
  maxHeight = "90vh",
}) => {
  const modalRef = useRef<HTMLDivElement>(null);
  // TODO: Implement animation state usage or remove if not needed
  // const [isAnimating, setIsAnimating] = useState(false);

  // Handle backdrop click
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (closeOnBackdrop && e.target === e.currentTarget) {
      onClose();
    }
  };

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "unset";
    };
  }, [isOpen, onClose]);

  // TODO: Implement animation handling or remove if not needed
  // useEffect(() => {
  //   if (isOpen) {
  //     setIsAnimating(true);
  //     const timer = setTimeout(() => setIsAnimating(false), 300);
  //     return () => clearTimeout(timer);
  //   }
  // }, [isOpen]);

  if (!isOpen) return null;

  return (
    <div className="mobile-modal-overlay-container">
      <div
        className={`mobile-modal-overlay ${isOpen ? "open" : ""}`}
        onClick={handleBackdropClick}
      />

      <div
        ref={modalRef}
        className={`mobile-modal ${isOpen ? "open" : ""} ${className}`}
        style={{ maxHeight }}
        role="dialog"
        aria-modal="true"
        aria-labelledby={title ? "modal-title" : undefined}
      >
        {showHandle && (
          <div className="mobile-modal-handle">
            <div className="mobile-modal-handle-bar" />
          </div>
        )}

        {title && (
          <div className="mobile-modal-header">
            <h2 id="modal-title" className="mobile-modal-title">
              {title}
            </h2>
            <button
              onClick={onClose}
              className="mobile-modal-close"
              aria-label="Close modal"
              type="button"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M18 6L6 18M6 6L18 18"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        )}

        <div className="mobile-modal-content">{children}</div>
      </div>
    </div>
  );
};

// Mobile Card Component
interface MobileCardProps {
  children: ReactNode;
  className?: string;
  onTap?: () => void;
  onLongPress?: () => void;
  interactive?: boolean;
  elevation?: "low" | "medium" | "high";
}

export const MobileCard: React.FC<MobileCardProps> = ({
  children,
  className = "",
  onTap,
  onLongPress,
  interactive = false,
  elevation = "medium",
}) => {
  const cardRef = useTouchGestures({
    onTap,
    onLongPress,
  }) as React.RefObject<HTMLDivElement>;

  const elevationClass = {
    low: "elevation-low",
    medium: "elevation-medium",
    high: "elevation-high",
  }[elevation];

  return (
    <div
      ref={cardRef}
      className={`mobile-card ${elevationClass} ${
        interactive ? "interactive" : ""
      } ${className}`}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
    >
      {children}
    </div>
  );
};

// Mobile List Component
interface MobileListItem {
  id: string;
  content: ReactNode;
  onTap?: () => void;
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  disabled?: boolean;
}

interface MobileListProps {
  items: MobileListItem[];
  className?: string;
  dividers?: boolean;
  virtualized?: boolean;
  itemHeight?: number;
}

export const MobileList: React.FC<MobileListProps> = ({
  items,
  className = "",
  dividers = true,
  virtualized = false,
  itemHeight: _itemHeight = 60, // TODO: Use this parameter when virtual list is implemented
}) => {
  // TODO: Implement isMobile usage or remove if not needed
  // const { isMobile } = useViewport();

  if (virtualized && items.length > 50) {
    // Use virtualization for large lists
    return (
      <div className={`mobile-list virtualized ${className}`}>
        {/* Virtual list implementation would go here */}
        {items.slice(0, 20).map((item, index) => (
          <MobileListItem
            key={item.id}
            item={item}
            showDivider={dividers && index < items.length - 1}
          />
        ))}
      </div>
    );
  }

  return (
    <div className={`mobile-list ${className}`}>
      {items.map((item, index) => (
        <MobileListItem
          key={item.id}
          item={item}
          showDivider={dividers && index < items.length - 1}
        />
      ))}
    </div>
  );
};

// Mobile List Item Component
interface MobileListItemProps {
  item: MobileListItem;
  showDivider?: boolean;
}

const MobileListItem: React.FC<MobileListItemProps> = ({
  item,
  showDivider,
}) => {
  const [swipeDistance, setSwipeDistance] = useState(0);
  const [isSwipingLeft, setIsSwipingLeft] = useState(false);
  const [isSwipingRight, setIsSwipingRight] = useState(false);

  const itemRef = useTouchGestures({
    onTap: item.disabled ? undefined : item.onTap,
    onSwipeLeft: () => {
      if (!item.disabled && item.onSwipeLeft) {
        setIsSwipingLeft(true);
        setTimeout(() => {
          item.onSwipeLeft?.();
          setIsSwipingLeft(false);
          setSwipeDistance(0);
        }, 150);
      }
    },
    onSwipeRight: () => {
      if (!item.disabled && item.onSwipeRight) {
        setIsSwipingRight(true);
        setTimeout(() => {
          item.onSwipeRight?.();
          setIsSwipingRight(false);
          setSwipeDistance(0);
        }, 150);
      }
    },
  }) as React.RefObject<HTMLDivElement>;

  return (
    <div className="mobile-list-item-container">
      <div
        ref={itemRef}
        className={`mobile-list-item ${item.disabled ? "disabled" : ""} ${
          isSwipingLeft ? "swiping-left" : ""
        } ${isSwipingRight ? "swiping-right" : ""}`}
        style={{ transform: `translateX(${swipeDistance}px)` }}
      >
        {item.content}
      </div>
      {showDivider && <div className="mobile-list-divider" />}
    </div>
  );
};

// Mobile Button Component
interface MobileButtonProps {
  children: ReactNode;
  onClick?: () => void;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "small" | "medium" | "large";
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
  className?: string;
  type?: "button" | "submit" | "reset";
  startIcon?: ReactNode;
  endIcon?: ReactNode;
}

export const MobileButton: React.FC<MobileButtonProps> = ({
  children,
  onClick,
  variant = "primary",
  size = "medium",
  disabled = false,
  loading = false,
  fullWidth = false,
  className = "",
  type = "button",
  startIcon,
  endIcon,
}) => {
  const [isPressed, setIsPressed] = useState(false);

  const handleTouchStart = () => {
    if (!disabled && !loading) {
      setIsPressed(true);
      // Haptic feedback
      if ("vibrate" in navigator) {
        navigator.vibrate(30);
      }
    }
  };

  const handleTouchEnd = () => {
    setIsPressed(false);
  };

  const handleClick = () => {
    if (!disabled && !loading && onClick) {
      onClick();
    }
  };

  const buttonClasses = [
    "mobile-button",
    `mobile-button-${variant}`,
    `mobile-button-${size}`,
    fullWidth ? "mobile-button-full-width" : "",
    disabled ? "disabled" : "",
    loading ? "loading" : "",
    isPressed ? "pressed" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      type={type}
      className={buttonClasses}
      onClick={handleClick}
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      disabled={disabled || loading}
      aria-disabled={disabled || loading}
    >
      {loading && (
        <div className="mobile-button-spinner">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path
              d="M12 2V6M12 18V22M4.93 4.93L7.76 7.76M16.24 16.24L19.07 19.07M2 12H6M18 12H22M4.93 19.07L7.76 16.24M16.24 7.76L19.07 4.93"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      )}

      {!loading && (
        <>
          {startIcon && (
            <span className="mobile-button-start-icon">{startIcon}</span>
          )}
          <span className="mobile-button-content">{children}</span>
          {endIcon && <span className="mobile-button-end-icon">{endIcon}</span>}
        </>
      )}
    </button>
  );
};

// Mobile Input Component
interface MobileInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: "text" | "email" | "password" | "number" | "tel" | "url";
  label?: string;
  error?: string;
  disabled?: boolean;
  required?: boolean;
  autoFocus?: boolean;
  className?: string;
  startIcon?: ReactNode;
  endIcon?: ReactNode;
  onFocus?: () => void;
  onBlur?: () => void;
}

export const MobileInput: React.FC<MobileInputProps> = ({
  value,
  onChange,
  placeholder,
  type = "text",
  label,
  error,
  disabled = false,
  required = false,
  autoFocus = false,
  className = "",
  startIcon,
  endIcon,
  onFocus,
  onBlur,
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFocus = () => {
    setIsFocused(true);
    onFocus?.();
  };

  const handleBlur = () => {
    setIsFocused(false);
    onBlur?.();
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  const inputClasses = [
    "mobile-input",
    isFocused ? "focused" : "",
    error ? "error" : "",
    disabled ? "disabled" : "",
    startIcon ? "has-start-icon" : "",
    endIcon ? "has-end-icon" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className="mobile-input-container">
      {label && (
        <label className="mobile-input-label">
          {label}
          {required && <span className="mobile-input-required">*</span>}
        </label>
      )}

      <div className="mobile-input-wrapper">
        {startIcon && (
          <div className="mobile-input-start-icon">{startIcon}</div>
        )}

        <input
          ref={inputRef}
          type={type}
          value={value}
          onChange={handleChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          autoFocus={autoFocus}
          className={inputClasses}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="off"
          spellCheck={false}
        />

        {endIcon && <div className="mobile-input-end-icon">{endIcon}</div>}
      </div>

      {error && (
        <div className="mobile-input-error" role="alert">
          {error}
        </div>
      )}
    </div>
  );
};

// Mobile Loading Skeleton
interface MobileSkeletonProps {
  variant?: "text" | "rectangular" | "circular";
  width?: string | number;
  height?: string | number;
  className?: string;
  animation?: "pulse" | "wave" | "none";
}

export const MobileSkeleton: React.FC<MobileSkeletonProps> = ({
  variant = "text",
  width,
  height,
  className = "",
  animation = "wave",
}) => {
  const skeletonClasses = [
    "mobile-skeleton",
    `mobile-skeleton-${variant}`,
    `mobile-skeleton-${animation}`,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === "number" ? `${width}px` : width;
  if (height)
    style.height = typeof height === "number" ? `${height}px` : height;

  return <div className={skeletonClasses} style={style} />;
};

export default {
  PullToRefresh,
  MobileModal,
  MobileCard,
  MobileList,
  MobileButton,
  MobileInput,
  MobileSkeleton,
};
