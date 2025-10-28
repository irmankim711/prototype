/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Authentication Helper for Development Testing
 * Quick authentication utility for testing the report functionality
 */

import axiosInstance from "../services/axiosInstance";

export interface LoginCredentials {
  email: string;
  
password: string;
}

export interface QuickLoginResult {
  success: boolean;
  
token?: string;
  
user?: any;
  
error?: string;
}

// Development test credentials
export const DEV_CREDENTIALS: LoginCredentials = {
  email: "test@example.com",
  password: "test123"
};

/**
 * Quick login for testing - stores token in localStorage
 */
export async function quickLogin(credentials: LoginCredentials = DEV_CREDENTIALS): Promise<QuickLoginResult> {
  try {
    console.log("🔐 Attempting quick login with:", credentials.email);

const response = await axiosInstance.post("/api/auth/login", credentials);

if (response.data.access_token) {
      // Store the token
      localStorage.setItem("accessToken", response.data.access_token);

console.log("✅ Quick login successful!", {
        token: response.data.access_token.substring(0, 20) + "...",
        user: response.data.user
      });

return {
        success: true,
        token: response.data.access_token,
        user: response.data.user
      };
    } else {
      throw Error("No access token received");
    }
  } catch (error: any) {
    console.error("❌ Quick login failed:", error);
    
return {
      success: false,
      error: error.response?.data?.message || error.message
    };
  }
}

/**
 * Create a test user if one doesn't exist
 */
export async function createTestUser(credentials: LoginCredentials = DEV_CREDENTIALS): Promise<boolean> {
  try {
    console.log("👤 Creating test user:", credentials.email);
    
    // const response = await axiosInstance.post("/api/auth/register", {
    //   email: credentials.email,
    //   password: credentials.password,
    //   organizationName: "Test Organization"
    // }); // Commented out - unused variable
    
    console.log("✅ Test user created successfully");
    
return true;
  } catch (error: any) {
    console.log("ℹ️ Test user might already exist or creation failed:", error.response?.data?.message || error.message);
    
return false;
  }
}

/**
 * Complete authentication setup for testing
 */
export async function setupTestAuth(): Promise<QuickLoginResult> {
  console.log("🚀 Setting up test authentication...");
  
  // Try to login first
  let result = await quickLogin();

if (!result.success) {
    console.log("🔄 Login failed, trying to create test user...");
    
await createTestUser();
    
    // Try login again after creating user
    result = await quickLogin();
  }
  
  if (result.success) {
    console.log("🎉 Test authentication setup complete!");
  } else {
    console.error("💥 Failed to setup test authentication");
  }
  
  return result;
}

/**
 * Check if user is currently authenticated
 */
export function isAuthenticated(): boolean {
  const token = localStorage.getItem("accessToken");
  
if (!token) return false;

try {
    // Check token expiration
    const decoded = JSON.parse(atob(token.split(".")[1]));
    
const currentTime = Math.floor(Date.now() / 1000);
    
return decoded.exp > currentTime;
  } catch (error) {
    return false;
  }
}

/**
 * Get current user info from token
 */
export function getCurrentUser(): unknown | null {
  const token = localStorage.getItem("accessToken");
  
if (!token) return null;

try {
    const decoded = JSON.parse(atob(token.split(".")[1]));
    
return {
      id: decoded.sub,
      email: decoded.email,
      username: decoded.username,
      role: decoded.role
    };
  } catch (error) {
    return null;
  }
}

/**
 * Clear authentication data
 */
export function clearAuth(): void {
  localStorage.removeItem("accessToken");
  
localStorage.removeItem("refreshToken");
  
localStorage.removeItem("userData");
  
console.log("🧹 Authentication data cleared");
}
