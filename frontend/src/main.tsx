import React from "react";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { AuthProvider } from "./context/AuthContext";
import { FirebaseAuthProvider } from "./context/FirebaseAuthContext";
import { UserProvider } from "./context/UserContext";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AuthProvider>
      <FirebaseAuthProvider>
        <UserProvider>
          <App />
        </UserProvider>
      </FirebaseAuthProvider>
    </AuthProvider>
  </StrictMode>
);
