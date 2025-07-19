import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
  useLocation,
} from "react-router-dom";
import { ThemeProvider } from "@mui/material/styles";
import { CssBaseline, Box } from "@mui/material";
import { theme } from "./theme";
import { AuthProvider, AuthContext } from "./context/AuthContext";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useContext } from "react";
import Sidebar from "./components/Layout/Sidebar";

// Import pages
import LandingPage from "./pages/LandingPage/LandingPage";
import Dashboard from "./pages/Dashboard/Dashboard";

import Submission from "./pages/Submission/Submission";
import ReportBuilder from "./pages/ReportBuilder/ReportBuilder";
import ReportHistory from "./pages/ReportHistory/ReportHistory";
import ReportTemplates from "./pages/ReportTemplates/ReportTemplates";
import RealtimeDashboard from "./pages/RealtimeDashboard";
import FormBuilderAdmin from "./pages/FormBuilderAdmin/FormBuilderAdmin";
import UserProfile from "./pages/UserProfile/UserProfile";
import Settings from "./pages/Settings/Settings";
import AboutUs from './pages/AboutUs/AboutUs';

const queryClient = new QueryClient();

function AppLayout() {
  // const { user } = useContext(AuthContext);
  const location = useLocation();
  // Sidebar is visible on all pages except landing page
  const showSidebar = location.pathname !== "/";

  return (
    <Box sx={{ display: "flex", minHeight: "100vh" }}>
      {showSidebar && <Sidebar />}
      <Box component="main" sx={{ flexGrow: 1, p: 3, ml: showSidebar ? "240px" : 0 }}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/about" element={<AboutUs />} />
          <Route path="/dashboard" element={<Dashboard />} />

          <Route path="/submission" element={<Submission />} />
          <Route path="/report-builder" element={<ReportBuilder />} />
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
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <Router>
            <AppLayout />
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
