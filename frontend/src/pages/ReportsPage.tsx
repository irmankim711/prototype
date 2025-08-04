import React from "react";
import { Container, Box, Typography, Tabs, Tab } from "@mui/material";
import { Assessment, Form, Analytics } from "@mui/icons-material";
import ReportDashboard from "../components/ReportDashboard";

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`report-tabpanel-${index}`}
      aria-labelledby={`report-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `report-tab-${index}`,
    "aria-controls": `report-tabpanel-${index}`,
  };
}

const ReportsPage: React.FC = () => {
  const [value, setValue] = React.useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ py: 3 }}>
        <Typography variant="h3" component="h1" gutterBottom sx={{ mb: 4 }}>
          Automated Report Generation
        </Typography>

        <Typography
          variant="h6"
          color="text.secondary"
          gutterBottom
          sx={{ mb: 4 }}
        >
          AI-powered reports generated from form submissions
        </Typography>

        <Box sx={{ borderBottom: 1, borderColor: "divider", mb: 3 }}>
          <Tabs
            value={value}
            onChange={handleChange}
            aria-label="report navigation tabs"
          >
            <Tab
              label="All Reports"
              icon={<Assessment />}
              iconPosition="start"
              {...a11yProps(0)}
            />
            <Tab
              label="Form Reports"
              icon={<Form />}
              iconPosition="start"
              {...a11yProps(1)}
            />
            <Tab
              label="Analytics"
              icon={<Analytics />}
              iconPosition="start"
              {...a11yProps(2)}
            />
          </Tabs>
        </Box>

        <TabPanel value={value} index={0}>
          <ReportDashboard />
        </TabPanel>

        <TabPanel value={value} index={1}>
          <Typography variant="h6" gutterBottom>
            Form-Specific Reports
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            View reports generated for specific forms. Select a form to see its
            dedicated reports.
          </Typography>
          {/* This would show a form selector and then ReportDashboard with formId */}
          <ReportDashboard />
        </TabPanel>

        <TabPanel value={value} index={2}>
          <Typography variant="h6" gutterBottom>
            Report Analytics
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Overview of report generation statistics and trends.
          </Typography>
          {/* This would show analytics about the reports themselves */}
        </TabPanel>
      </Box>
    </Container>
  );
};

export default ReportsPage;
