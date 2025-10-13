/**
 * Development-only logger utility
 * Prevents console flooding in production
 */

const IS_DEV = import.meta.env.DEV;

export const logger = {
  log: (...args: any[]) => {
    if (IS_DEV) {
      console.log(...args);
    }
  },
  
  warn: (...args: any[]) => {
    if (IS_DEV) {
      console.warn(...args);
    }
  },
  
  error: (...args: any[]) => {
    // Always log errors, but limit in production
    if (IS_DEV) {
      console.error(...args);
    } else {
      // In production, only log the first argument (usually the message)
      console.error(args[0]);
    }
  },
  
  info: (...args: any[]) => {
    if (IS_DEV) {
      console.info(...args);
    }
  },
  
  debug: (...args: any[]) => {
    if (IS_DEV) {
      console.debug(...args);
    }
  }
};

export default logger;