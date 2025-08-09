import React from "react";
import { Box, Container, Typography } from "@mui/material";
import AnalyticsDashboard from "../../components/Analytics/AnalyticsDashboard";

const Dashboard: React.FC = () => {
  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard Analytics
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Comprehensive analytics and insights for your forms and submissions
        </Typography>
      </Box>

      <AnalyticsDashboard />
    </Container>
  );
};

export default Dashboard;
