import React from "react";
import { Container, Box, Typography, Tabs, Tab } from "@mui/material";
import { Assessment, Assignment, Analytics, Description } from "@mui/icons-material";
import ReportDashboard from "../components/ReportDashboard";
import DocxReportGenerator from "../components/DocxReportGenerator";
import ExcelToDocxConverter from "../components/ExcelToDocxConverter";
import ReportNavigator from "../components/ReportNavigator";
import ReportAccessGuide from "../components/ReportAccessGuide";

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

  const handleReportGenerated = (report: unknown) => {
    // Refresh the dashboard when a new report is generated
    console.log('New report generated:', report);
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
          AI-powered reports generated from form submissions and document uploads
        </Typography>

        {/* Step-by-step guide for users */}
        <ReportAccessGuide />

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
              icon={<Assignment />}
              iconPosition="start"
              {...a11yProps(1)}
            />
            <Tab
              label="DOCX Generator"
              icon={<Description />}
              iconPosition="start"
              {...a11yProps(2)}
            />
            <Tab
              label="Analytics"
              icon={<Analytics />}
              iconPosition="start"
              {...a11yProps(3)}
            />
          </Tabs>
        </Box>

        <TabPanel value={value} index={0}>
          <Box sx={{ mb: 3 }}>
            <ReportNavigator 
              onViewReport={(reportId) => {
                console.log('View report:', reportId);
                // Navigate to report view or open preview modal
              }}
              onEditReport={(reportId) => {
                console.log('Edit report:', reportId);
                // Navigate to report editor
              }}
              onDownloadReport={(reportId) => {
                console.log('Download report:', reportId);
                // Trigger download
              }}
            />
          </Box>
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
          <Box sx={{ mb: 4 }}>
            <Typography variant="h6" gutterBottom>
              Excel to DOCX Converter
            </Typography>
            <Typography variant="body2" color="text.secondary" paragraph>
              Upload Excel files and automatically generate professional DOCX reports with data analysis.
            </Typography>
            <ExcelToDocxConverter 
              onReportGenerated={handleReportGenerated}
              onEditReport={(reportId) => {
                // Navigate to edit mode or open editor modal
                console.log('Edit report:', reportId);
              }}
            />
          </Box>
          
          <Typography variant="h6" gutterBottom sx={{ mt: 4 }}>
            Advanced DOCX Generator
          </Typography>
          <DocxReportGenerator onReportGenerated={handleReportGenerated} />
        </TabPanel>

        <TabPanel value={value} index={3}>
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
