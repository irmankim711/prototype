/**
 * Advanced Rate Limiting and Debouncing Utilities
 * Prevents AI suggestions endpoint rate limiting (HTTP 429)
 */

export interface RateLimitConfig {
  maxRequestsPerMinute: number;
  maxRequestsPerSecond: number;
  debounceDelay: number;
  retryConfig: {
    maxRetries: number;
    baseDelay: number;
    maxDelay: number;
    backoffMultiplier: number;
  };
  cache: {
    ttl: number;
    maxSize: number;
  };
}

const DEFAULT_CONFIG: RateLimitConfig = {
  maxRequestsPerMinute: 8, // Conservative limit for AI suggestions
  maxRequestsPerSecond: 0.2, // 1 request every 5 seconds
  debounceDelay: 2000, // 2 second debounce
  retryConfig: {
    maxRetries: 3,
    baseDelay: 3000,
    maxDelay: 30000,
    backoffMultiplier: 3
  },
  cache: {
    ttl: 5 * 60 * 1000, // 5 minutes
    maxSize: 50
  }
};

class AdvancedRateLimiter {
  private requestQueue: Map<string, number[]> = new Map();
  private debounceTimers: Map<string, NodeJS.Timeout> = new Map();
  private requestCache: Map<string, {
    data: any;
    timestamp: number;
    ttl: number;
  }> = new Map();
  private pendingRequests: Map<string, Promise<any>> = new Map();

  constructor(private config: RateLimitConfig = DEFAULT_CONFIG) {}

  /**
   * Debounced request with rate limiting and caching
   */
  async makeRequest<T>(
    key: string,
    requestFn: () => Promise<T>,
    customConfig?: Partial<RateLimitConfig>
  ): Promise<T> {
    const effectiveConfig = { ...this.config, ...customConfig };

    // Check cache first
    const cached = this.getCachedResponse<T>(key);
    if (cached) {
      console.log(`🎯 [RateLimiter] Returning cached response for: ${key}`);
      return cached;
    }

    // Check for pending request
    if (this.pendingRequests.has(key)) {
      console.log(`🔄 [RateLimiter] Reusing pending request for: ${key}`);
      return this.pendingRequests.get(key)!;
    }

    // Create debounced request
    return new Promise((resolve, reject) => {
      // Clear existing timer
      if (this.debounceTimers.has(key)) {
        clearTimeout(this.debounceTimers.get(key)!);
      }

      // Set new debounce timer
      const timer = setTimeout(async () => {
        try {
          this.debounceTimers.delete(key);
          const result = await this.executeWithRateLimit(key, requestFn, effectiveConfig);
          resolve(result);
        } catch (error) {
          reject(error);
        }
      }, effectiveConfig.debounceDelay);

      this.debounceTimers.set(key, timer);
      console.log(`⏱️ [RateLimiter] Debouncing request for ${effectiveConfig.debounceDelay}ms: ${key}`);
    });
  }

  /**
   * Execute request with rate limiting
   */
  private async executeWithRateLimit<T>(
    key: string,
    requestFn: () => Promise<T>,
    config: RateLimitConfig
  ): Promise<T> {
    const now = Date.now();
    const oneMinuteAgo = now - 60000;
    const oneSecondAgo = now - 1000;

    // Get request history
    const requests = this.requestQueue.get(key) || [];

    // Clean old requests
    const recentRequests = requests.filter(time => time > oneMinuteAgo);
    const veryRecentRequests = recentRequests.filter(time => time > oneSecondAgo);

    // Check rate limits
    if (recentRequests.length >= config.maxRequestsPerMinute) {
      const waitTime = 60000 - (now - recentRequests[0]) + 1000;
      console.warn(`🚫 [RateLimiter] Per-minute rate limit exceeded for ${key}, waiting ${waitTime}ms`);
      await this.delay(waitTime);
    }

    if (veryRecentRequests.length >= config.maxRequestsPerSecond) {
      const waitTime = 1000 - (now - veryRecentRequests[veryRecentRequests.length - 1]) + 100;
      console.warn(`🚫 [RateLimiter] Per-second rate limit exceeded for ${key}, waiting ${waitTime}ms`);
      await this.delay(waitTime);
    }

    // Execute request with retry logic
    const promise = this.retryWithExponentialBackoff(requestFn, config.retryConfig);
    this.pendingRequests.set(key, promise);

    try {
      const result = await promise;

      // Record successful request
      recentRequests.push(Date.now());
      this.requestQueue.set(key, recentRequests);

      // Cache result
      this.setCachedResponse(key, result, config.cache.ttl);

      console.log(`✅ [RateLimiter] Request succeeded: ${key}`);
      return result;
    } finally {
      this.pendingRequests.delete(key);
    }
  }

  /**
   * Retry with exponential backoff
   */
  private async retryWithExponentialBackoff<T>(
    requestFn: () => Promise<T>,
    retryConfig: RateLimitConfig['retryConfig'],
    attempt: number = 1
  ): Promise<T> {
    try {
      return await requestFn();
    } catch (error: any) {
      const status = error?.response?.status;

      // Don't retry client errors (except 429)
      if (status >= 400 && status < 500 && status !== 429) {
        console.error(`❌ [RateLimiter] Client error (${status}), not retrying:`, error?.response?.data);
        throw error;
      }

      if (attempt > retryConfig.maxRetries) {
        console.error(`❌ [RateLimiter] Max retries exceeded after ${attempt - 1} attempts`);
        throw error;
      }

      // Calculate delay with exponential backoff
      let delay = Math.min(
        retryConfig.baseDelay * Math.pow(retryConfig.backoffMultiplier, attempt - 1),
        retryConfig.maxDelay
      );

      // Handle rate limiting specifically
      if (status === 429) {
        const retryAfter = error.response?.headers['retry-after'];
        if (retryAfter) {
          delay = parseInt(retryAfter) * 1000 + 1000; // Add 1 second buffer
        }
        console.warn(`🚫 [RateLimiter] Rate limited (429), waiting ${delay}ms before retry ${attempt}/${retryConfig.maxRetries}`);
      } else {
        console.warn(`⚠️ [RateLimiter] Request failed, retrying in ${delay}ms (attempt ${attempt}/${retryConfig.maxRetries}):`, error.message);
      }

      await this.delay(delay);
      return this.retryWithExponentialBackoff(requestFn, retryConfig, attempt + 1);
    }
  }

  /**
   * Get cached response
   */
  private getCachedResponse<T>(key: string): T | null {
    const cached = this.requestCache.get(key);
    if (cached && Date.now() - cached.timestamp < cached.ttl) {
      return cached.data;
    }

    if (cached) {
      this.requestCache.delete(key);
    }

    return null;
  }

  /**
   * Set cached response
   */
  private setCachedResponse<T>(key: string, data: T, ttl: number): void {
    // Implement LRU cache eviction
    if (this.requestCache.size >= this.config.cache.maxSize) {
      const oldestKey = this.requestCache.keys().next().value;
      this.requestCache.delete(oldestKey);
    }

    this.requestCache.set(key, {
      data,
      timestamp: Date.now(),
      ttl
    });
  }

  /**
   * Clear debounce timers for a specific key
   */
  public clearDebounce(key: string): void {
    if (this.debounceTimers.has(key)) {
      clearTimeout(this.debounceTimers.get(key)!);
      this.debounceTimers.delete(key);
      console.log(`🧹 [RateLimiter] Cleared debounce for: ${key}`);
    }
  }

  /**
   * Clear all debounce timers
   */
  public clearAllDebounces(): void {
    for (const [key, timer] of this.debounceTimers) {
      clearTimeout(timer);
    }
    this.debounceTimers.clear();
    console.log(`🧹 [RateLimiter] Cleared all debounce timers`);
  }

  /**
   * Get current rate limit status
   */
  public getRateLimitStatus(key: string): {
    requestsInLastMinute: number;
    requestsInLastSecond: number;
    canMakeRequest: boolean;
    waitTime: number;
  } {
    const now = Date.now();
    const requests = this.requestQueue.get(key) || [];
    const recentRequests = requests.filter(time => time > now - 60000);
    const veryRecentRequests = requests.filter(time => time > now - 1000);

    const minuteLimit = recentRequests.length < this.config.maxRequestsPerMinute;
    const secondLimit = veryRecentRequests.length < this.config.maxRequestsPerSecond;

    let waitTime = 0;
    if (!minuteLimit) {
      waitTime = Math.max(waitTime, 60000 - (now - recentRequests[0]) + 1000);
    }
    if (!secondLimit) {
      waitTime = Math.max(waitTime, 1000 - (now - veryRecentRequests[veryRecentRequests.length - 1]) + 100);
    }

    return {
      requestsInLastMinute: recentRequests.length,
      requestsInLastSecond: veryRecentRequests.length,
      canMakeRequest: minuteLimit && secondLimit,
      waitTime
    };
  }

  /**
   * Utility delay function
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// Export singleton instance
export const aiSuggestionsRateLimiter = new AdvancedRateLimiter({
  ...DEFAULT_CONFIG,
  maxRequestsPerMinute: 6, // Very conservative for AI suggestions
  maxRequestsPerSecond: 0.1, // 1 request every 10 seconds
  debounceDelay: 3000, // 3 second debounce for AI suggestions
});

// Export general rate limiter
export const generalRateLimiter = new AdvancedRateLimiter(DEFAULT_CONFIG);

export default AdvancedRateLimiter;