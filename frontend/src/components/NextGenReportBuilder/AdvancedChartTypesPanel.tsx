/**
 * Advanced Chart Types & Export Panel
 * Phase 5: Advanced chart types, export features, and collaboration
 */

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  Button,
  Chip,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Alert,
  LinearProgress,
  Rating,
  useTheme
} from '@mui/material';
import {
  ExpandMore,
  Add,
  Download,
  Share,
  Comment as CommentIcon,
  History,
  Group,
  Link,
  ThreeDRotation,
  GridOn,
  Radar,
  BubbleChart
} from '@mui/icons-material';

import type { ChartData, ChartConfig } from './types';
import { advancedChartService } from '../../services/advancedChartService';
import { chartExportService } from '../../services/chartExportService';
import { collaborationService } from '../../services/collaborationService';

interface AdvancedChartTypesPanelProps {
  chartData?: ChartData;
  chartConfig?: ChartConfig;
  onChartConfigChange?: (config: any) => void;
  onExport?: (result: any) => void;
}

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
      id={`advanced-chart-tabpanel-${index}`}
      aria-labelledby={`advanced-chart-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const AdvancedChartTypesPanel: React.FC<AdvancedChartTypesPanelProps> = ({
  chartData,
  chartConfig,
  onChartConfigChange,
  onExport
}) => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [isExporting, setIsExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState('png');
  const [templates, setTemplates] = useState<any[]>([]);
  const [presets, setPresets] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [currentConfig, setCurrentConfig] = useState<ChartConfig | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = () => {
    setTemplates(advancedChartService.getChartTemplates());
    setPresets(advancedChartService.getChartPresets());
    setCurrentConfig(chartConfig || null);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleExport = async (format: string) => {
    try {
      setIsExporting(true);
      setError(null);
      
      // Export logic would be implemented here
      const exportData = {
        format,
        chartConfig: currentConfig,
        timestamp: new Date().toISOString()
      };
      
      // Simulate export delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Handle export result
      if (format === 'json') {
        const dataStr = JSON.stringify(exportData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `chart-config-${Date.now()}.json`;
        link.click();
        URL.revokeObjectURL(url);
      }
    } catch (error: any) {
      setError(error.message || 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Advanced Chart Types & Export Features
      </Typography>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Chart Templates" />
          <Tab label="Export Options" />
          <Tab label="Collaboration" />
          <Tab label="Advanced Features" />
        </Tabs>
      </Box>

      {/* Chart Templates Tab */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={2}>
          {templates.map((template) => (
            <Grid item xs={12} md={6} key={template.id}>
              <Card>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    {template.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {template.description}
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Chip label={template.category} size="small" color="primary" variant="outlined" />
                    <Rating value={template.rating} readOnly size="small" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* Export Options Tab */}
      <TabPanel value={tabValue} index={1}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Export Settings
              </Typography>
              
              <FormControl fullWidth size="small" sx={{ mb: 2 }}>
                <InputLabel>Format</InputLabel>
                <Select
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value)}
                  label="Format"
                >
                  <MenuItem value="png">PNG Image</MenuItem>
                  <MenuItem value="svg">SVG Vector</MenuItem>
                  <MenuItem value="pdf">PDF Document</MenuItem>
                  <MenuItem value="excel">Excel Spreadsheet</MenuItem>
                  <MenuItem value="csv">CSV Data</MenuItem>
                  <MenuItem value="json">JSON Config</MenuItem>
                </Select>
              </FormControl>
              
              <Button
                variant="contained"
                startIcon={<Download />}
                onClick={() => handleExport(exportFormat)}
                disabled={isExporting}
                fullWidth
              >
                Export Chart
              </Button>
              
              {isExporting && (
                <Box sx={{ mt: 2 }}>
                  <LinearProgress />
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Exporting...
                  </Typography>
                </Box>
              )}
              {error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {error}
                </Alert>
              )}
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Export Templates
              </Typography>
              
              <List>
                <ListItem>
                  <ListItemIcon>
                    <Download />
                  </ListItemIcon>
                  <ListItemText
                    primary="High Quality PNG"
                    secondary="1920x1080, 300 DPI for presentations"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Download />
                  </ListItemIcon>
                  <ListItemText
                    primary="Web Optimized PNG"
                    secondary="800x600, 72 DPI for web use"
                  />
                </ListItem>
                <ListItem>
                  <ListItemIcon>
                    <Download />
                  </ListItemIcon>
                  <ListItemText
                    primary="Vector SVG"
                    secondary="Scalable vector graphics"
                  />
                </ListItem>
              </List>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Collaboration Tab */}
      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="subtitle1">
                  Collaboration
                </Typography>
                <Button
                  variant="contained"
                  size="small"
                  startIcon={<Add />}
                >
                  New Session
                </Button>
              </Box>
              
              <Alert severity="info">
                Start collaborating with your team in real-time!
              </Alert>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Share & Export
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Button
                    variant="outlined"
                    startIcon={<Share />}
                    fullWidth
                  >
                    Share
                  </Button>
                </Grid>
                <Grid item xs={6}>
                  <Button
                    variant="outlined"
                    startIcon={<Link />}
                    fullWidth
                  >
                    Get Link
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>

      {/* Advanced Features Tab */}
      <TabPanel value={tabValue} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Chart Presets
              </Typography>
              
              <Grid container spacing={2}>
                {presets.map((preset) => (
                  <Grid item xs={12} key={preset.id}>
                    <Card>
                      <CardContent>
                        <Typography variant="subtitle2" gutterBottom>
                          {preset.name}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {preset.description}
                        </Typography>
                        <Chip 
                          label={preset.category} 
                          size="small" 
                          color="secondary" 
                          variant="outlined"
                          sx={{ mt: 1 }}
                        />
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Advanced Chart Types
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Card sx={{ textAlign: 'center', p: 2 }}>
                    <ThreeDRotation sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                    <Typography variant="subtitle2">3D Charts</Typography>
                  </Card>
                </Grid>
                
                                  <Grid item xs={6}>
                    <Card sx={{ textAlign: 'center', p: 2 }}>
                      <GridOn sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                      <Typography variant="subtitle2">Heatmaps</Typography>
                    </Card>
                  </Grid>
                
                <Grid item xs={6}>
                  <Card sx={{ textAlign: 'center', p: 2 }}>
                    <Radar sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                    <Typography variant="subtitle2">Radar Charts</Typography>
                  </Card>
                </Grid>
                
                <Grid item xs={6}>
                  <Card sx={{ textAlign: 'center', p: 2 }}>
                    <BubbleChart sx={{ fontSize: 40, color: 'warning.main', mb: 1 }} />
                    <Typography variant="subtitle2">Bubble Charts</Typography>
                  </Card>
                </Grid>
              </Grid>
            </Paper>
          </Grid>
        </Grid>
      </TabPanel>
    </Box>
  );
};

export default AdvancedChartTypesPanel;
