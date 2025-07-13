import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { CssBaseline } from "@mui/material";
import { theme } from "./theme";
import { AuthProvider } from "./context/AuthContext";

// Import pages
import LandingPage from "./pages/LandingPage/LandingPage";
import Dashboard from "./pages/Dashboard/Dashboard";
import Form from "./pages/Form/Form";
import Submission from "./pages/Submission/Submission";
import ReportBuilder from "./pages/ReportBuilder/ReportBuilder";
import ReportHistory from "./pages/ReportHistory/ReportHistory";
import ReportTemplates from "./pages/ReportTemplates/ReportTemplates";
import RealtimeDashboard from "./pages/RealtimeDashboard";
import FormBuilderAdmin from "./pages/FormBuilderAdmin/FormBuilderAdmin";
import UserProfile from "./pages/UserProfile/UserProfile";
import Settings from "./pages/Settings/Settings";

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <Router>
          <div className="App">
            <Routes>
              {/* Public routes */}
              <Route path="/" element={<LandingPage />} />

              {/* Protected routes */}
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/form" element={<Form />} />
              <Route path="/submission" element={<Submission />} />
              <Route path="/report-builder" element={<ReportBuilder />} />
              <Route path="/report-history" element={<ReportHistory />} />
              <Route path="/report-templates" element={<ReportTemplates />} />
              <Route
                path="/realtime-dashboard"
                element={<RealtimeDashboard />}
              />
              <Route
                path="/form-builder-admin"
                element={<FormBuilderAdmin />}
              />
              <Route path="/profile" element={<UserProfile />} />
              <Route path="/settings" element={<Settings />} />

              {/* Redirect any unknown routes to landing page */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
