/**
 * CSRF Token Service
 * 
 * This service provides comprehensive CSRF token management including:
 * - Token generation and refresh
 * - Automatic token inclusion in API calls
 * - Form integration
 * - Token validation
 */

import { api } from './api-new';

export interface CSRFResponse {
  success: boolean;
  csrf_token: string;
  message: string;
}

export interface CSRFValidationResponse {
  success: boolean;
  is_valid: boolean;
  message: string;
}

class CSRFService {
  private currentToken: string | null = null;
  private tokenExpiry: number | null = null;
  private readonly TOKEN_REFRESH_THRESHOLD = 5 * 60 * 1000; // 5 minutes before expiry
  private readonly TOKEN_LIFETIME = 60 * 60 * 1000; // 1 hour

  /**
   * Get the current CSRF token, generating a new one if needed
   */
  async getToken(): Promise<string> {
    // Check if we have a valid token
    if (this.isTokenValid()) {
      return this.currentToken!;
    }

    // Generate a new token
    return this.generateNewToken();
  }

  /**
   * Generate a new CSRF token from the backend
   */
  async generateNewToken(): Promise<string> {
    try {
      const response = await api.get<CSRFResponse>('/csrf/token');
      
      if (response.data.success) {
        this.currentToken = response.data.csrf_token;
        this.tokenExpiry = Date.now() + this.TOKEN_LIFETIME;
        
        // Store token in localStorage for persistence
        localStorage.setItem('csrf_token', this.currentToken);
        localStorage.setItem('csrf_token_expiry', this.tokenExpiry.toString());
        
        console.log('✅ CSRF token generated successfully');
        return this.currentToken;
      } else {
        throw new Error('Failed to generate CSRF token');
      }
    } catch (error) {
      console.error('❌ Failed to generate CSRF token:', error);
      throw new Error('CSRF token generation failed');
    }
  }

  /**
   * Refresh the current CSRF token
   */
  async refreshToken(): Promise<string> {
    try {
      const response = await api.post<CSRFResponse>('/csrf/refresh');
      
      if (response.data.success) {
        this.currentToken = response.data.csrf_token;
        this.tokenExpiry = Date.now() + this.TOKEN_LIFETIME;
        
        // Update localStorage
        localStorage.setItem('csrf_token', this.currentToken);
        localStorage.setItem('csrf_token_expiry', this.tokenExpiry.toString());
        
        console.log('✅ CSRF token refreshed successfully');
        return this.currentToken;
      } else {
        throw new Error('Failed to refresh CSRF token');
      }
    } catch (error) {
      console.error('❌ Failed to refresh CSRF token:', error);
      // Fallback to generating a new token
      return this.generateNewToken();
    }
  }

  /**
   * Validate a CSRF token
   */
  async validateToken(token: string): Promise<boolean> {
    try {
      const response = await api.post<CSRFValidationResponse>('/csrf/validate', {
        csrf_token: token
      });
      
      return response.data.success && response.data.is_valid;
    } catch (error) {
      console.error('❌ Failed to validate CSRF token:', error);
      return false;
    }
  }

  /**
   * Check if the current token is valid
   */
  private isTokenValid(): boolean {
    if (!this.currentToken || !this.tokenExpiry) {
      return false;
    }

    const now = Date.now();
    const timeUntilExpiry = this.tokenExpiry - now;

    // Token is valid if it hasn't expired and isn't close to expiring
    return timeUntilExpiry > this.TOKEN_REFRESH_THRESHOLD;
  }

  /**
   * Initialize the CSRF service by loading stored token
   */
  initialize(): void {
    try {
      const storedToken = localStorage.getItem('csrf_token');
      const storedExpiry = localStorage.getItem('csrf_token_expiry');

      if (storedToken && storedExpiry) {
        this.currentToken = storedToken;
        this.tokenExpiry = parseInt(storedExpiry);

        // Check if stored token is still valid
        if (!this.isTokenValid()) {
          // Clear invalid token
          this.clearToken();
        }
      }
    } catch (error) {
      console.error('❌ Failed to initialize CSRF service:', error);
      this.clearToken();
    }
  }

  /**
   * Clear the current CSRF token
   */
  clearToken(): void {
    this.currentToken = null;
    this.tokenExpiry = null;
    localStorage.removeItem('csrf_token');
    localStorage.removeItem('csrf_token_expiry');
  }

  /**
   * Get CSRF token for use in headers
   */
  getTokenHeader(): { [key: string]: string } {
    if (this.currentToken) {
      return { 'X-CSRF-Token': this.currentToken };
    }
    return {};
  }

  /**
   * Get CSRF token for use in form data
   */
  getTokenFormData(): { [key: string]: string } {
    if (this.currentToken) {
      return { csrf_token: this.currentToken };
    }
    return {};
  }

  /**
   * Check if token needs refresh and refresh if necessary
   */
  async ensureValidToken(): Promise<string> {
    if (this.shouldRefreshToken()) {
      return this.refreshToken();
    }
    return this.getToken();
  }

  /**
   * Check if token should be refreshed
   */
  private shouldRefreshToken(): boolean {
    if (!this.currentToken || !this.tokenExpiry) {
      return true;
    }

    const now = Date.now();
    const timeUntilExpiry = this.tokenExpiry - now;

    return timeUntilExpiry <= this.TOKEN_REFRESH_THRESHOLD;
  }

  /**
   * Set up automatic token refresh
   */
  setupAutoRefresh(): void {
    // Check token every minute
    setInterval(async () => {
      if (this.shouldRefreshToken()) {
        try {
          await this.refreshToken();
        } catch (error) {
          console.error('❌ Auto-refresh of CSRF token failed:', error);
        }
      }
    }, 60 * 1000); // Check every minute
  }
}

// Create singleton instance
export const csrfService = new CSRFService();

// Initialize the service
csrfService.initialize();

// Set up auto-refresh
csrfService.setupAutoRefresh();

export default csrfService;
