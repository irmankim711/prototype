import React, { useEffect, useRef } from "react";

interface GoogleSignInButtonProps {
  onSuccess: (credential: string) => void;
  onError: (error: string) => void;
  disabled?: boolean;
}

const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onSuccess,
  onError,
  disabled = false,
}) => {
  const buttonRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const initializeButton = () => {
      if (!window.google?.accounts?.id) {
        onError("Google Sign-In API not loaded");
        return;
      }

      if (!buttonRef.current) return;

      try {
        // Set up global callback
        (window as any).googleSignInCallback = (response: {
          credential?: string;
        }) => {
          if (response.credential) {
            onSuccess(response.credential);
          } else {
            onError("No credential received from Google");
          }
        };

        // Initialize and render the button
        window.google.accounts.id.initialize({
          client_id:
            "1008582896300-ivas6c0e7vnr30lbr0v1jeu7q7io7k1u.apps.googleusercontent.com",
          callback: (window as any).googleSignInCallback,
        });

        window.google.accounts.id.renderButton(buttonRef.current, {
          theme: "outline",
          size: "large",
          type: "standard",
          shape: "rectangular",
          text: "signin_with",
          logo_alignment: "left",
          width: 300,
        });
      } catch (error) {
        onError(`Failed to initialize Google Sign-In: ${error}`);
      }
    };

    // Check if Google API is loaded
    if (window.google?.accounts?.id) {
      initializeButton();
    } else {
      // Wait for Google API to load
      const checkGoogleAPI = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(checkGoogleAPI);
          initializeButton();
        }
      }, 100);

      // Cleanup after 10 seconds
      setTimeout(() => {
        clearInterval(checkGoogleAPI);
      }, 10000);

      return () => clearInterval(checkGoogleAPI);
    }
  }, [onSuccess, onError]);

  return (
    <div
      className={`google-signin-container ${
        disabled ? "opacity-50 pointer-events-none" : ""
      }`}
    >
      <div ref={buttonRef} className="google-signin-button" />
    </div>
  );
};

export default GoogleSignInButton;
