/**
 * Security Monitoring Service
 * Tracks and logs security-related events for analysis and debugging
 */

export interface SecurityEvent {
  type: 'rate_limit_triggered' | 'rate_limit_warning' | 'login_failure' | 'suspicious_activity';
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  metadata?: Record<string, any>;
  timestamp: string;
  userAgent?: string;
}

class SecurityMonitoringService {
  private events: SecurityEvent[] = [];
  private readonly MAX_STORED_EVENTS = 100;
  private readonly STORAGE_KEY = 'security_events';

  constructor() {
    this.loadEventsFromStorage();
  }

  /**
   * Log a security event
   */
  logEvent(
    type: SecurityEvent['type'],
    message: string,
    severity: SecurityEvent['severity'] = 'medium',
    metadata?: Record<string, any>
  ): void {
    const event: SecurityEvent = {
      type,
      severity,
      message,
      metadata: {
        ...metadata,
        url: window.location.href,
        userAgent: navigator.userAgent,
      },
      timestamp: new Date().toISOString(),
    };

    // Add to in-memory store
    this.events.unshift(event);

    // Keep only the most recent events
    if (this.events.length > this.MAX_STORED_EVENTS) {
      this.events = this.events.slice(0, this.MAX_STORED_EVENTS);
    }

    // Persist to localStorage
    this.saveEventsToStorage();

    // Console logging based on severity
    this.logToConsole(event);

    // In production, you would send this to your monitoring service
    // Example: Sentry, LogRocket, Datadog, etc.
    if (import.meta.env.PROD) {
      this.sendToMonitoringService(event);
    }
  }

  /**
   * Log rate limit triggered event
   */
  logRateLimitTriggered(attempts: number, lockoutDuration: number): void {
    this.logEvent(
      'rate_limit_triggered',
      `Client-side rate limit triggered after ${attempts} failed attempts`,
      'high',
      {
        attempts,
        lockoutDurationMinutes: lockoutDuration / 60 / 1000,
      }
    );
  }

  /**
   * Log rate limit warning event
   */
  logRateLimitWarning(attemptsRemaining: number): void {
    this.logEvent(
      'rate_limit_warning',
      `User approaching rate limit: ${attemptsRemaining} attempts remaining`,
      'medium',
      {
        attemptsRemaining,
      }
    );
  }

  /**
   * Log login failure event
   */
  logLoginFailure(errorCode: string, errorMessage: string, email?: string): void {
    // Determine severity based on error code
    const severity = this.getLoginFailureSeverity(errorCode);

    this.logEvent(
      'login_failure',
      `Login failed: ${errorMessage}`,
      severity,
      {
        errorCode,
        email: this.sanitizeEmail(email), // Sanitize PII
      }
    );
  }

  /**
   * Log Firebase auth/too-many-requests error
   */
  logFirebaseRateLimit(email?: string): void {
    this.logEvent(
      'rate_limit_triggered',
      'Firebase rate limit triggered (auth/too-many-requests)',
      'critical',
      {
        source: 'firebase',
        email: this.sanitizeEmail(email),
        recommendation: 'User should wait 15-30 minutes or reset password',
      }
    );
  }

  /**
   * Get recent security events
   */
  getRecentEvents(limit: number = 50): SecurityEvent[] {
    return this.events.slice(0, limit);
  }

  /**
   * Get events by type
   */
  getEventsByType(type: SecurityEvent['type']): SecurityEvent[] {
    return this.events.filter((event) => event.type === type);
  }

  /**
   * Clear all stored events
   */
  clearEvents(): void {
    this.events = [];
    localStorage.removeItem(this.STORAGE_KEY);
  }

  /**
   * Export events for analysis
   */
  exportEvents(): string {
    return JSON.stringify(this.events, null, 2);
  }

  /**
   * Get security statistics
   */
  getStatistics() {
    const now = new Date();
    const last24Hours = new Date(now.getTime() - 24 * 60 * 60 * 1000);
    const last7Days = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);

    const recentEvents = this.events.filter(
      (e) => new Date(e.timestamp) > last24Hours
    );
    const weeklyEvents = this.events.filter(
      (e) => new Date(e.timestamp) > last7Days
    );

    return {
      total: this.events.length,
      last24Hours: recentEvents.length,
      last7Days: weeklyEvents.length,
      byType: {
        rateLimitTriggered: this.getEventsByType('rate_limit_triggered').length,
        rateLimitWarning: this.getEventsByType('rate_limit_warning').length,
        loginFailure: this.getEventsByType('login_failure').length,
        suspiciousActivity: this.getEventsByType('suspicious_activity').length,
      },
      bySeverity: {
        low: this.events.filter((e) => e.severity === 'low').length,
        medium: this.events.filter((e) => e.severity === 'medium').length,
        high: this.events.filter((e) => e.severity === 'high').length,
        critical: this.events.filter((e) => e.severity === 'critical').length,
      },
    };
  }

  /**
   * Private: Load events from localStorage
   */
  private loadEventsFromStorage(): void {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        this.events = JSON.parse(stored);
      }
    } catch (error) {
      console.error('[SecurityMonitoring] Failed to load events from storage:', error);
    }
  }

  /**
   * Private: Save events to localStorage
   */
  private saveEventsToStorage(): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.events));
    } catch (error) {
      console.error('[SecurityMonitoring] Failed to save events to storage:', error);
    }
  }

  /**
   * Private: Log to console with appropriate level
   */
  private logToConsole(event: SecurityEvent): void {
    const prefix = `[SECURITY:${event.severity.toUpperCase()}]`;
    const message = `${prefix} ${event.type}: ${event.message}`;

    switch (event.severity) {
      case 'critical':
        console.error(message, event.metadata);
        break;
      case 'high':
        console.warn(message, event.metadata);
        break;
      case 'medium':
        console.log(message, event.metadata);
        break;
      case 'low':
        console.debug(message, event.metadata);
        break;
    }
  }

  /**
   * Private: Send to external monitoring service
   */
  private sendToMonitoringService(event: SecurityEvent): void {
    // This is where you would integrate with your monitoring service
    // Examples:

    // Sentry
    // if (window.Sentry) {
    //   window.Sentry.captureMessage(event.message, {
    //     level: event.severity,
    //     extra: event.metadata,
    //     tags: { type: event.type },
    //   });
    // }

    // LogRocket
    // if (window.LogRocket) {
    //   window.LogRocket.track(event.type, event.metadata);
    // }

    // Custom analytics endpoint
    // fetch('/api/security/events', {
    //   method: 'POST',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify(event),
    // }).catch(console.error);

    // For now, just log that we would send it
    console.debug('[SecurityMonitoring] Would send to monitoring service:', event);
  }

  /**
   * Private: Get severity level for login failure
   */
  private getLoginFailureSeverity(errorCode: string): SecurityEvent['severity'] {
    switch (errorCode) {
      case 'auth/too-many-requests':
      case 'auth/user-disabled':
        return 'critical';
      case 'auth/wrong-password':
      case 'auth/invalid-credential':
        return 'high';
      case 'auth/user-not-found':
      case 'auth/invalid-email':
        return 'medium';
      default:
        return 'low';
    }
  }

  /**
   * Private: Sanitize email for logging (PII protection)
   */
  private sanitizeEmail(email?: string): string | undefined {
    if (!email) return undefined;

    // In production, you might want to hash the email or just store the domain
    const parts = email.split('@');
    if (parts.length === 2) {
      return `${parts[0].substring(0, 2)}***@${parts[1]}`;
    }
    return '***';
  }
}

// Export singleton instance
export const securityMonitoring = new SecurityMonitoringService();

// Export for testing
export default securityMonitoring;
