import React from "react";
import { useState } from "react";
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Card,
  CardContent,
  Alert,
  AlertTitle,
  Chip,
  Button,
  Grid,
} from "@mui/material";
import {
  Psychology as BrainIcon,
  Analytics,
  Lightbulb as LightbulbIcon,
  AutoAwesome as SmartIcon,
  Gavel as ValidateIcon,
  TrendingUp,
} from "@mui/icons-material";
import AIAnalysisDashboard from "./AIAnalysisDashboard";
import AIReportSuggestions from "./AIReportSuggestions";
import AISmartPlaceholders from "./AISmartPlaceholders";
import type {
  AIAnalysisResult,
  AIReportSuggestion,
  AIPlaceholder,
} from "../../services/aiService";

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
      id={`ai-tabpanel-${index}`}
      aria-labelledby={`ai-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `ai-tab-${index}`,
    "aria-controls": `ai-tabpanel-${index}`,
  };
}

interface AIHubProps {
  data?: Record<string, unknown>;
  reports?: Record<string, unknown>[];
  context?: string;
  onAnalysisComplete?: (result: AIAnalysisResult) => void;
  onSuggestionApply?: (suggestion: AIReportSuggestion) => void;
  onPlaceholderSelect?: (placeholder: AIPlaceholder) => void;
}

export const AIHub: React.FC<AIHubProps> = ({
  data,
  reports = [],
  context = "general",
  onAnalysisComplete,
  onSuggestionApply,
  onPlaceholderSelect,
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [aiFeatures] = useState({
    analysis: true,
    suggestions: true,
    placeholders: true,
    validation: false, // Not implemented yet
    optimization: false, // Not implemented yet
  });

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const getTabIcon = (index: number) => {
    switch (index) {
      case 0:
        return <Analytics />;
      case 1:
        return <LightbulbIcon />;
      case 2:
        return <SmartIcon />;
      case 3:
        return <ValidateIcon />;
      case 4:
        return <TrendingUp />;
      default:
        return <BrainIcon />;
    }
  };

  return (
    <Box sx={{ width: "100%" }}>
      {/* Header */}
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 3 }}>
        <BrainIcon color="primary" sx={{ fontSize: 40 }} />
        <Box>
          <Typography variant="h3" component="h1" fontWeight="bold">
            AI Hub
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Intelligent insights and automation for your reports
          </Typography>
        </Box>
      </Box>

      {/* Feature Status */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <AlertTitle>AI Features Status</AlertTitle>
        <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 1 }}>
          <Chip
            label="Data Analysis"
            color={aiFeatures.analysis ? "success" : "default"}
            variant={aiFeatures.analysis ? "filled" : "outlined"}
            size="small"
          />
          <Chip
            label="Report Suggestions"
            color={aiFeatures.suggestions ? "success" : "default"}
            variant={aiFeatures.suggestions ? "filled" : "outlined"}
            size="small"
          />
          <Chip
            label="Smart Placeholders"
            color={aiFeatures.placeholders ? "success" : "default"}
            variant={aiFeatures.placeholders ? "filled" : "outlined"}
            size="small"
          />
          <Chip
            label="Data Validation"
            color={aiFeatures.validation ? "success" : "default"}
            variant={aiFeatures.validation ? "filled" : "outlined"}
            size="small"
          />
          <Chip
            label="Template Optimization"
            color={aiFeatures.optimization ? "success" : "default"}
            variant={aiFeatures.optimization ? "filled" : "outlined"}
            size="small"
          />
        </Box>
      </Alert>

      {/* Tabs Navigation */}
      <Card elevation={1}>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <Tabs
            value={activeTab}
            onChange={handleTabChange}
            aria-label="AI Hub tabs"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab
              icon={getTabIcon(0)}
              label="Data Analysis"
              {...a11yProps(0)}
              disabled={!aiFeatures.analysis}
            />
            <Tab
              icon={getTabIcon(1)}
              label="Report Suggestions"
              {...a11yProps(1)}
              disabled={!aiFeatures.suggestions}
            />
            <Tab
              icon={getTabIcon(2)}
              label="Smart Placeholders"
              {...a11yProps(2)}
              disabled={!aiFeatures.placeholders}
            />
            <Tab
              icon={getTabIcon(3)}
              label="Data Validation"
              {...a11yProps(3)}
              disabled={!aiFeatures.validation}
            />
            <Tab
              icon={getTabIcon(4)}
              label="Template Optimization"
              {...a11yProps(4)}
              disabled={!aiFeatures.optimization}
            />
          </Tabs>
        </Box>

        {/* Tab Panels */}
        <TabPanel value={activeTab} index={0}>
          <AIAnalysisDashboard
            data={data || {}}
            context={context}
            onAnalysisComplete={onAnalysisComplete}
            autoAnalyze={false}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={1}>
          <AIReportSuggestions
            reports={reports}
            context={context}
            onSuggestionApply={onSuggestionApply}
            autoGenerate={false}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={2}>
          <AISmartPlaceholders
            context={context}
            industry="general"
            onPlaceholderSelect={onPlaceholderSelect}
            autoGenerate={false}
          />
        </TabPanel>

        <TabPanel value={activeTab} index={3}>
          <Box sx={{ p: 3 }}>
            <Card elevation={2}>
              <CardContent sx={{ py: 6 }}>
                <Box
                  sx={{
                    textAlign: "center",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 2,
                  }}
                >
                  <ValidateIcon sx={{ fontSize: 64, color: "text.disabled" }} />
                  <Box>
                    <Typography
                      variant="h6"
                      fontWeight="bold"
                      color="text.primary"
                    >
                      Data Validation (Coming Soon)
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      AI-powered data quality checks and validation rules
                    </Typography>
                  </Box>
                  <Button variant="outlined" disabled>
                    Feature In Development
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </TabPanel>

        <TabPanel value={activeTab} index={4}>
          <Box sx={{ p: 3 }}>
            <Card elevation={2}>
              <CardContent sx={{ py: 6 }}>
                <Box
                  sx={{
                    textAlign: "center",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                    gap: 2,
                  }}
                >
                  <TrendingUp sx={{ fontSize: 64, color: "text.disabled" }} />
                  <Box>
                    <Typography
                      variant="h6"
                      fontWeight="bold"
                      color="text.primary"
                    >
                      Template Optimization (Coming Soon)
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      AI suggestions to improve report templates and layouts
                    </Typography>
                  </Box>
                  <Button variant="outlined" disabled>
                    Feature In Development
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Box>
        </TabPanel>
      </Card>

      {/* Quick Actions */}
      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
          Quick Actions
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<Analytics />}
              onClick={() => setActiveTab(0)}
              disabled={!data || Object.keys(data).length === 0}
            >
              Analyze Current Data
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<LightbulbIcon />}
              onClick={() => setActiveTab(1)}
              disabled={!reports || reports.length === 0}
            >
              Get Report Ideas
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<SmartIcon />}
              onClick={() => setActiveTab(2)}
            >
              Generate Placeholders
            </Button>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<BrainIcon />}
              disabled
            >
              More AI Features
            </Button>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
};

export default AIHub;
