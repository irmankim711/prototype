/**
 * Progressive Web App (PWA) Components and Utilities
 * Service worker, offline support, and PWA installation
 */

import React from "react";
import { useState, useEffect } from "react";
import { Download, Wifi, WifiOff, Smartphone } from "lucide-react";
import { MobileButton } from "./MobileComponents";
import { useNetworkStatus } from "../../hooks/useTouchGestures";

// Types for PWA features
interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

// PWA Install Button Component
export const PWAInstallButton: React.FC = () => {
  const [deferredPrompt, setDeferredPrompt] =
    useState<BeforeInstallPromptEvent | null>(null);
  const [showInstallButton, setShowInstallButton] = useState(false);
  const [isInstalling, setIsInstalling] = useState(false);

  useEffect(() => {
    // Check if app is already installed
    const isStandalone = window.matchMedia(
      "(display-mode: standalone)"
    ).matches;
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isInstalled = isStandalone || (window.navigator as any).standalone;

    if (isInstalled) {
      setShowInstallButton(false);
      return;
    }

    // Handle the beforeinstallprompt event
    const handleBeforeInstallPrompt = (e: BeforeInstallPromptEvent) => {
      // Prevent Chrome 67 and earlier from automatically showing the prompt
      e.preventDefault();
      setDeferredPrompt(e);
      setShowInstallButton(true);
    };

    // Handle app installed event
    const handleAppInstalled = () => {
      setShowInstallButton(false);
      setDeferredPrompt(null);
      console.log("PWA was installed");
    };

    window.addEventListener(
      "beforeinstallprompt",
      handleBeforeInstallPrompt as any
    );
    window.addEventListener("appinstalled", handleAppInstalled);

    // For iOS devices, show install instructions
    if (isIOS && !isInstalled) {
      setShowInstallButton(true);
    }

    return () => {
      window.removeEventListener(
        "beforeinstallprompt",
        handleBeforeInstallPrompt as any
      );
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) {
      // For iOS or other browsers, show instructions
      showInstallInstructions();
      return;
    }

    setIsInstalling(true);

    try {
      // Show the install prompt
      deferredPrompt.prompt();

      // Wait for the user to respond to the prompt
      const { outcome } = await deferredPrompt.userChoice;

      console.log(`User response to the install prompt: ${outcome}`);

      if (outcome === "accepted") {
        console.log("User accepted the A2HS prompt");
        // Haptic feedback
        if ("vibrate" in navigator) {
          navigator.vibrate([100, 50, 100]);
        }
      } else {
        console.log("User dismissed the A2HS prompt");
      }

      setDeferredPrompt(null);
      setShowInstallButton(false);
    } catch (error) {
      console.error("Error during PWA installation:", error);
    } finally {
      setIsInstalling(false);
    }
  };

  const showInstallInstructions = () => {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isSafari =
      /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);

    let instructions = "";

    if (isIOS && isSafari) {
      instructions = `To install this app:
1. Tap the Share button in Safari
2. Scroll down and tap "Add to Home Screen"
3. Tap "Add" to confirm`;
    } else if (isIOS) {
      instructions = `To install this app:
1. Open this page in Safari
2. Tap the Share button
3. Tap "Add to Home Screen"`;
    } else {
      instructions = `To install this app:
1. Look for the install icon in your browser's address bar
2. Click it and follow the prompts
3. Or check your browser's menu for "Install" option`;
    }

    alert(instructions);
  };

  if (!showInstallButton) return null;

  return (
    <div className="pwa-install-container">
      <MobileButton
        onClick={handleInstallClick}
        variant="primary"
        disabled={isInstalling}
        loading={isInstalling}
        startIcon={<Smartphone size={16} />}
        className="pwa-install-button"
      >
        {isInstalling ? "Installing..." : "Install App"}
      </MobileButton>
    </div>
  );
};

// Offline Status Component
export const OfflineStatus: React.FC = () => {
  const { isOnline } = useNetworkStatus();
  const [showOfflineBanner, setShowOfflineBanner] = useState(false);

  useEffect(() => {
    setShowOfflineBanner(!isOnline);
  }, [isOnline]);

  const handleRetry = () => {
    window.location.reload();
  };

  if (!showOfflineBanner) return null;

  return (
    <div className="offline-status-banner">
      <div className="offline-status-content">
        <WifiOff size={20} className="offline-icon" />
        <div className="offline-text">
          <span className="offline-title">You're offline</span>
          <span className="offline-message">
            Check your connection and try again
          </span>
        </div>
        <MobileButton variant="ghost" size="small" onClick={handleRetry}>
          Retry
        </MobileButton>
      </div>
    </div>
  );
};

// Network Status Indicator Component
export const NetworkStatusIndicator: React.FC = () => {
  const { isOnline, connectionType, isSlowConnection } = useNetworkStatus();

  if (isOnline && !isSlowConnection) return null;

  return (
    <div
      className={`network-status-indicator ${!isOnline ? "offline" : "slow"}`}
    >
      {!isOnline ? (
        <>
          <WifiOff size={16} />
          <span>Offline</span>
        </>
      ) : (
        <>
          <Wifi size={16} />
          <span>Slow connection ({connectionType})</span>
        </>
      )}
    </div>
  );
};

// PWA Update Available Component
export const PWAUpdateNotification: React.FC = () => {
  const [showUpdateBanner, setShowUpdateBanner] = useState(false);
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(
    null
  );

  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.addEventListener("controllerchange", () => {
        window.location.reload();
      });

      navigator.serviceWorker.ready.then((registration: any) => {
        registration.addEventListener("updatefound", () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener("statechange", () => {
              if (
                newWorker.state === "installed" &&
                navigator.serviceWorker.controller
              ) {
                setWaitingWorker(newWorker);
                setShowUpdateBanner(true);
              }
            });
          }
        });
      });
    }
  }, []);

  const handleUpdate = () => {
    if (waitingWorker) {
      waitingWorker.postMessage({ type: "SKIP_WAITING" });
      setShowUpdateBanner(false);
    }
  };

  const handleDismiss = () => {
    setShowUpdateBanner(false);
  };

  if (!showUpdateBanner) return null;

  return (
    <div className="pwa-update-banner">
      <div className="pwa-update-content">
        <div className="pwa-update-icon">
          <Download size={20} />
        </div>
        <div className="pwa-update-text">
          <span className="pwa-update-title">Update Available</span>
          <span className="pwa-update-message">
            A new version of the app is ready
          </span>
        </div>
        <div className="pwa-update-actions">
          <MobileButton variant="ghost" size="small" onClick={handleDismiss}>
            Later
          </MobileButton>
          <MobileButton variant="primary" size="small" onClick={handleUpdate}>
            Update
          </MobileButton>
        </div>
      </div>
    </div>
  );
};

// Service Worker Registration
export const registerServiceWorker = async (): Promise<void> => {
  if ("serviceWorker" in navigator) {
    try {
      const registration = await navigator.serviceWorker.register("/sw.js");

      console.log("Service Worker registered successfully:", registration);

      // Check for updates immediately
      registration.update();

      // Check for updates every 60 seconds when the app is active
      setInterval(() => {
        if (document.visibilityState === "visible") {
          registration.update();
        }
      }, 60000);
    } catch (error) {
      console.error("Service Worker registration failed:", error);
    }
  }
};

// Unregister Service Worker (for development)
export const unregisterServiceWorker = async (): Promise<void> => {
  if ("serviceWorker" in navigator) {
    try {
      const registration = await navigator.serviceWorker.ready;
      await registration.unregister();
      console.log("Service Worker unregistered successfully");
    } catch (error) {
      console.error("Service Worker unregistration failed:", error);
    }
  }
};

// PWA Utilities
export const PWAUtils = {
  // Check if app is installed
  isInstalled: (): boolean => {
    const isStandalone = window.matchMedia(
      "(display-mode: standalone)"
    ).matches;
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    return isStandalone || (window.navigator as any).standalone || false;
  },

  // Check if browser supports PWA
  isSupported: (): boolean => {
    return "serviceWorker" in navigator && "PushManager" in window;
  },

  // Check if device is mobile
  isMobile: (): boolean => {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    );
  },

  // Get install prompt availability
  canInstall: (): boolean => {
    return !PWAUtils.isInstalled() && PWAUtils.isSupported();
  },

  // Add to cache (for offline functionality)
  addToCache: async (url: string): Promise<void> => {
    if ("caches" in window) {
      try {
        const cache = await caches.open("app-cache-v1");
        await cache.add(url);
        console.log(`Added ${url} to cache`);
      } catch (error) {
        console.error("Failed to add to cache:", error);
      }
    }
  },

  // Remove from cache
  removeFromCache: async (url: string): Promise<void> => {
    if ("caches" in window) {
      try {
        const cache = await caches.open("app-cache-v1");
        await cache.delete(url);
        console.log(`Removed ${url} from cache`);
      } catch (error) {
        console.error("Failed to remove from cache:", error);
      }
    }
  },

  // Clear all caches
  clearCache: async (): Promise<void> => {
    if ("caches" in window) {
      try {
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames.map((cacheName: any) => caches.delete(cacheName))
        );
        console.log("All caches cleared");
      } catch (error) {
        console.error("Failed to clear caches:", error);
      }
    }
  },
};

// Main PWA Manager Component
export const PWAManager: React.FC = () => {
  return (
    <>
      <OfflineStatus />
      <NetworkStatusIndicator />
      <PWAUpdateNotification />
    </>
  );
};

export default PWAManager;
