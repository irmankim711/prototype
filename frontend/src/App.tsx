
import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { CssBaseline, Box } from "@mui/material";
import enhancedTheme from "./theme/enhancedTheme";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "react-hot-toast";
import EnhancedSidebar from "./components/Layout/EnhancedSidebar";
import { environmentConfig, environmentUtils } from "./config/environment";
import { ErrorProvider } from "./context/ErrorContext";

// Import enhanced styles
import "./styles/enhancedDashboard.css";

// Import quick setup utilities for browser console
import "./utils/quickSetup";

// Import pages
import LandingPageEnhanced from "./pages/LandingPage/LandingPageEnhanced";
import Dashboard from "./pages/Dashboard/Dashboard";
import PublicForms from "./pages/PublicForms/PublicForms";
import PublicFormBuilder from "./pages/PublicFormBuilder/PublicFormBuilder";

import Submission from "./pages/Submission/Submission";

import ReportHistory from "./pages/ReportHistory/ReportHistory";
import ReportTemplates from "./pages/ReportTemplates/ReportTemplates";
import RealtimeDashboard from "./pages/RealtimeDashboard";
import FormBuilderAdmin from "./pages/FormBuilderAdmin/FormBuilderAdmin";
import FormBuilderDashboardEnhanced from "./pages/FormBuilderAdmin/FormBuilderDashboardEnhanced";
import UserProfile from "./pages/UserProfile/UserProfile";
import Settings from "./pages/Settings/Settings";
import AboutUs from "./pages/AboutUs/AboutUs";
import PublicFormAccess from "./components/PublicFormAccess/PublicFormAccess";

import NextGenReportBuilderPage from "./pages/NextGenReportBuilder/NextGenReportBuilderPage";
import AuthTestPage from "./pages/NextGenReportBuilder/AuthTestPage";
import ErrorHandlingDemo from "./pages/ErrorHandlingDemo/ErrorHandlingDemo";
import FormDataExportDemo from "./pages/FormDataExportDemo/FormDataExportDemo";
import ReportsPage from "./pages/ReportsPage";

const queryClient = new QueryClient();

function AppLayout() {
  const location = useLocation();
  // Sidebar is visible on all pages except landing page, about us page, public forms, public form builder, and access code page
  const showSidebar =
    location.pathname !== "/" &&
    location.pathname !== "/about" &&
    location.pathname !== "/forms/public" &&
    location.pathname !== "/public-form-builder" &&
    location.pathname !== "/access-forms";

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      {showSidebar && <EnhancedSidebar />}
      <Box
        component="main"
        sx={{ flexGrow: 1, p: 3, ml: showSidebar ? "260px" : 0 }}
      >
        <Routes>
          <Route path="/" element={<LandingPageEnhanced />} />
          <Route path="/about" element={<AboutUs />} />
          <Route path="/forms/public" element={<PublicForms />} />
          <Route path="/public-form-builder" element={<PublicFormBuilder />} />
          <Route path="/access-forms" element={<PublicFormAccess />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route
            path="/dashboard-enhanced"
            element={<FormBuilderDashboardEnhanced />}
          />
          <Route path="/submission" element={<Submission />} />

          <Route
            path="/next-gen-report-builder"
            element={<NextGenReportBuilderPage />}
          />
          <Route
            path="/next-gen-report-builder/auth-test"
            element={<AuthTestPage />}
          />

          <Route path="/error-handling-demo" element={<ErrorHandlingDemo />} />
          <Route path="/form-data-export-demo" element={<FormDataExportDemo />} />
          <Route path="/reports" element={<ReportsPage />} />

          <Route path="/report-history" element={<ReportHistory />} />
          <Route path="/report-templates" element={<ReportTemplates />} />
          <Route path="/realtime-dashboard" element={<RealtimeDashboard />} />
          <Route path="/form-builder-admin" element={<FormBuilderAdmin />} />
          <Route path="/profile" element={<UserProfile />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Box>
    </Box>
  );
}

function App() {
  // Validate environment on app startup
  React.useEffect(() => {
    try {
      const isValid = environmentUtils.validate();
      if (isValid) {
        console.log('Environment configuration loaded successfully:', {
          environment: environmentConfig.app.environment,
          apiUrl: environmentConfig.api.baseUrl,
          appName: environmentConfig.app.name,
          version: environmentConfig.app.version,
          features: environmentConfig.features,
        });
      }
    } catch (error) {
      console.error('Failed to validate environment configuration:', error);
    }
  }, []);

  return (
    <ErrorProvider>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider theme={enhancedTheme}>
          <CssBaseline />
          <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <AppLayout />
          </Router>
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 5000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#4caf50',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 6000,
                iconTheme: {
                  primary: '#f44336',
                  secondary: '#fff',
                },
              },
            }}
          />
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorProvider>
  );
}

export default App;
