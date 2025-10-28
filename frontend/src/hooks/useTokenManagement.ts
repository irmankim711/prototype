import { useState, useEffect, useCallback } from "react";

import { useFirebaseAuth } from "../context/FirebaseAuthContext";

import { environmentConfig } from "../config/environment";

interface TokenInfo {
  token: string | null;
  
expiresAt: number | null;
  
isValid: boolean;
  
timeUntilExpiry: number;
}

export function useTokenManagement() {
  const { firebaseUser, isDevelopmentBypass } = useFirebaseAuth();
  
const [tokenInfo, setTokenInfo] = useState<TokenInfo>({
    token: null,
    expiresAt: null,
    isValid: false,
    timeUntilExpiry: 0,
  });

  // Parse JWT token to extract expiration
  const parseToken = useCallback((token: string): TokenInfo => {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      
const expiresAt = payload.exp ? payload.exp * 1000 : null; // Convert to milliseconds
      const now = Date.now();
      
const isValid = expiresAt ? expiresAt > now : true;
      
const timeUntilExpiry = expiresAt ? expiresAt - now : 0;

return {
        token,
        expiresAt,
        isValid,
        timeUntilExpiry,
      };
    } catch (error) {
      console.error('Failed to parse token:', error);
      
return {
        token,
        expiresAt: null,
        isValid: false,
        timeUntilExpiry: 0,
      };
    }
  }, []);

  // Update token info when Firebase user changes
  useEffect(() => {
    if (isDevelopmentBypass) {
      setTokenInfo({
        token: 'dev-bypass-token',
        expiresAt: null,
        isValid: true,
        timeUntilExpiry: Infinity,
      });
      return;
    }

    const updateFromFirebase = async () => {
      if (firebaseUser) {
        try {
          const idToken = await firebaseUser.getIdToken();
          setTokenInfo(parseToken(idToken));
        } catch (e) {
          setTokenInfo({
            token: null,
            expiresAt: null,
            isValid: false,
            timeUntilExpiry: 0,
          });
        }
      } else {
        setTokenInfo({
          token: null,
          expiresAt: null,
          isValid: false,
          timeUntilExpiry: 0,
        });
      }
    };

    updateFromFirebase();
  }, [firebaseUser, isDevelopmentBypass, parseToken]);

  // Auto-refresh timer for expiring tokens
  useEffect(() => {
    if (!tokenInfo.isValid || !tokenInfo.expiresAt || isDevelopmentBypass) {
      return;
    }

    const timeUntilRefresh = Math.max(tokenInfo.timeUntilExpiry - 60000, 0); // Refresh 1 minute before expiry
    
    const timer = setTimeout(() => {
      console.log('Token expiring soon, triggering refresh...');
      // This will trigger the refresh logic in AuthContext
    }, timeUntilRefresh);

return () => clearTimeout(timer);
  }, [tokenInfo, isDevelopmentBypass]);

  // Check if token needs refresh
  const needsRefresh = useCallback(() => {
    if (isDevelopmentBypass) return false;
    
    // Refresh if token expires in less than 5 minutes
    return tokenInfo.timeUntilExpiry < 300000;
  }, [tokenInfo.timeUntilExpiry, isDevelopmentBypass]);

  // Get token for API requests
  const getTokenForRequest = useCallback(() => {
    if (isDevelopmentBypass) {
      return 'dev-bypass-token';
    }
    
    if (tokenInfo.isValid && tokenInfo.token) {
      return tokenInfo.token;
    }
    
    return null;
  }, [tokenInfo, isDevelopmentBypass]);

  // Format time until expiry for display
  const formatTimeUntilExpiry = useCallback(() => {
    if (!tokenInfo.expiresAt || isDevelopmentBypass) {
      return 'Never';
    }

    const minutes = Math.floor(tokenInfo.timeUntilExpiry / 60000);
    
const seconds = Math.floor((tokenInfo.timeUntilExpiry % 60000) / 1000);

if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    }
    return `${seconds}s`;
  }, [tokenInfo, isDevelopmentBypass]);

return {
    tokenInfo,
    needsRefresh,
    getTokenForRequest,
    formatTimeUntilExpiry,
    isDevelopmentBypass,
  };
}

export default useTokenManagement;
