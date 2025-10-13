import React from "react";
import EnhancedAutomatedReportDashboard from "../components/EnhancedAutomatedReportDashboard";
import { Box } from "@mui/material";

// Simple page component to integrate the enhanced automated reports
const AutomatedReportsPage: React.FC = () => {
  return (
    <Box sx={{ minHeight: "100vh", backgroundColor: "#f5f5f5" }}>
      <EnhancedAutomatedReportDashboard />
    </Box>
  );
};

export default AutomatedReportsPage;
