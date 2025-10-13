/**
 * Formatting utilities for display
 */

export const formatDateTime = (
  dateString: string | null | undefined
): string => {
  if (!dateString) return "Never";

  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    }).format(date);
  } catch {
    return "Invalid date";
  }
};

export const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return "Never";

  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    }).format(date);
  } catch {
    return "Invalid date";
  }
};

export const formatTime = (dateString: string | null | undefined): string => {
  if (!dateString) return "Never";

  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    }).format(date);
  } catch {
    return "Invalid time";
  }
};

export const formatFileSize = (bytes: number | null | undefined): string => {
  if (!bytes) return "0 B";

  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));

  return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
};

export const formatDuration = (seconds: number | null | undefined): string => {
  if (!seconds) return "0 seconds";

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = seconds % 60;

  if (hours > 0) {
    return `${hours}h ${minutes}m ${remainingSeconds}s`;
  } else if (minutes > 0) {
    return `${minutes}m ${remainingSeconds}s`;
  } else {
    return `${remainingSeconds}s`;
  }
};

export const formatNumber = (num: number | null | undefined): string => {
  if (num === null || num === undefined) return "0";

  return new Intl.NumberFormat("en-US").format(num);
};

export const formatPercentage = (
  value: number | null | undefined,
  decimals: number = 1
): string => {
  if (value === null || value === undefined) return "0%";

  return `${value.toFixed(decimals)}%`;
};

export const formatRelativeTime = (
  dateString: string | null | undefined
): string => {
  if (!dateString) return "Never";

  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) {
      return "Just now";
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes !== 1 ? "s" : ""} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours !== 1 ? "s" : ""} ago`;
    } else if (diffInSeconds < 2592000) {
      const days = Math.floor(diffInSeconds / 86400);
      return `${days} day${days !== 1 ? "s" : ""} ago`;
    } else {
      return formatDate(dateString);
    }
  } catch {
    return "Invalid date";
  }
};

export const truncateText = (
  text: string | null | undefined,
  maxLength: number = 50
): string => {
  if (!text) return "";

  if (text.length <= maxLength) {
    return text;
  }

  return `${text.substring(0, maxLength)}...`;
};

export const capitalizeFirst = (text: string | null | undefined): string => {
  if (!text) return "";

  return text.charAt(0).toUpperCase() + text.slice(1);
};

export const formatSourceType = (
  sourceType: string | null | undefined
): string => {
  if (!sourceType) return "Unknown";

  return sourceType
    .split("_")
    .map((word) => capitalizeFirst(word))
    .join(" ");
};
