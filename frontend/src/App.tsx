import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { theme } from './theme';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import ReportBuilder from './pages/ReportBuilder/ReportBuilder';
import ReportTemplates from './pages/ReportTemplates/ReportTemplates';
import ReportHistory from './pages/ReportHistory/ReportHistory';
import Settings from './pages/Settings/Settings';
import Submission from './pages/Submission';
import Form from './pages/Form';
import LandingPage from './pages/LandingPage';
import UserProfile from './pages/UserProfile';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Simple authentication setup

// Protected route component
interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  // In a real app, this would check for a token or session
  // For demo purposes, we'll use localStorage
  const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true';
  
  if (!isAuthenticated) {
    return <Navigate to="/landing" replace />;
  }
  
  return <>{children}</>;
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/landing" element={<LandingPage />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Layout>
                  <Dashboard />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/submission" element={
              <ProtectedRoute>
                <Layout>
                  <Submission />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/form" element={
              <ProtectedRoute>
                <Layout>
                  <Form />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/reports/new" element={
              <ProtectedRoute>
                <Layout>
                  <ReportBuilder />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/reports/templates" element={
              <ProtectedRoute>
                <Layout>
                  <ReportTemplates />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/reports/history" element={
              <ProtectedRoute>
                <Layout>
                  <ReportHistory />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/settings" element={
              <ProtectedRoute>
                <Layout>
                  <Settings />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="/profile" element={
              <ProtectedRoute>
                <Layout>
                  <UserProfile />
                </Layout>
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/landing" replace />} />
          </Routes>
        </Router>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
