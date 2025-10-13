/**
 * Data Source Management Panel
 * Allows users to configure, test, and monitor various data sources
 */

import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Paper, 
  Typography, 
  Accordion, 
  AccordionSummary, 
  AccordionDetails, 
  Chip, 
  LinearProgress, 
  Alert, 
  List, 
  ListItem, 
  ListItemText, 
  ListItemIcon, 
  Divider, 
  Grid, 
  Card, 
  CardContent, 
  Button, 
  IconButton, 
  Tooltip, 
  alpha, 
  useTheme,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { 
  ExpandMore, 
  Add, 
  Edit, 
  Delete, 
  Refresh, 
  PlayArrow, 
  Stop, 
  Settings, 
  Timeline, 
  DataUsage, 
  Speed, 
  Error, 
  CheckCircle, 
  Warning,
  CloudQueue,
  Storage,
  Api,
  Description,
  Stream,
  Visibility,
  VisibilityOff,
  Security,
  Speed as SpeedIcon
} from '@mui/icons-material';
import type { DataSourceConfig, DataSourceStatus, DataSourceHealth, QueryConfig } from '../../services/backendDataService';
import { backendDataService } from '../../services/backendDataService';

interface DataSourceManagementPanelProps {
  onDataSourceChange?: (sourceId: string) => void;
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
      id={`datasource-tabpanel-${index}`}
      aria-labelledby={`datasource-tab-${index}`}
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

const DataSourceManagementPanel: React.FC<DataSourceManagementPanelProps> = ({ 
  onDataSourceChange 
}) => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [dataSources, setDataSources] = useState<DataSourceConfig[]>([]);
  const [dataSourceStatuses, setDataSourceStatuses] = useState<DataSourceStatus[]>([]);
  const [selectedDataSource, setSelectedDataSource] = useState<string>('');
  const [isAddDialogOpen, setIsAddDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [editingDataSource, setEditingDataSource] = useState<DataSourceConfig | null>(null);
  const [isTestingConnection, setIsTestingConnection] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});

  // Form state for new/edit data source
  const [formData, setFormData] = useState<Partial<DataSourceConfig>>({
    name: '',
    type: 'database',
    connectionString: '',
    options: {
      timeout: 30000,
      maxConnections: 10,
      ssl: false,
      cache: true,
      cacheTTL: 300000,
    },
  });

  useEffect(() => {
    loadDataSources();
    startStatusMonitoring();
  }, []);

  const loadDataSources = () => {
    const sources = backendDataService.getDataSources();
    setDataSources(sources);
    if (sources.length > 0 && !selectedDataSource) {
      setSelectedDataSource(sources[0].id);
    }
  };

  const startStatusMonitoring = () => {
    const interval = setInterval(() => {
      setDataSourceStatuses(backendDataService.getAllDataSourceStatuses());
    }, 2000);

    return () => clearInterval(interval);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleAddDataSource = () => {
    setFormData({
      name: '',
      type: 'database',
      connectionString: '',
      options: {
        timeout: 30000,
        maxConnections: 10,
        ssl: false,
        cache: true,
        cacheTTL: 300000,
      },
    });
    setIsAddDialogOpen(true);
  };

  const handleEditDataSource = (source: DataSourceConfig) => {
    setEditingDataSource(source);
    setFormData({
      name: source.name,
      type: source.type,
      connectionString: source.connectionString || '',
      credentials: source.credentials,
      options: source.options,
      schema: source.schema,
    });
    setIsEditDialogOpen(true);
  };

  const handleDeleteDataSource = async (sourceId: string) => {
    if (window.confirm('Are you sure you want to delete this data source?')) {
      backendDataService.removeDataSource(sourceId);
      loadDataSources();
    }
  };

  const handleSaveDataSource = () => {
    if (!formData.name || !formData.type) {
      alert('Please fill in all required fields');
      return;
    }

    const newSource: DataSourceConfig = {
      id: editingDataSource?.id || `ds-${Date.now()}`,
      name: formData.name,
      type: formData.type as any,
      connectionString: formData.connectionString,
      credentials: formData.credentials,
      options: formData.options,
      schema: formData.schema,
    };

    if (editingDataSource) {
      // Update existing
      backendDataService.removeDataSource(editingDataSource.id);
      backendDataService.addDataSource(newSource);
    } else {
      // Add new
      backendDataService.addDataSource(newSource);
    }

    loadDataSources();
    setIsAddDialogOpen(false);
    setIsEditDialogOpen(false);
    setEditingDataSource(null);
  };

  const handleTestConnection = async (sourceId: string) => {
    setIsTestingConnection(true);
    try {
      const result = await backendDataService.testConnection(sourceId);
      setTestResults(prev => ({ ...prev, [sourceId]: result }));
    } catch (error) {
      setTestResults(prev => ({ ...prev, [sourceId]: false }));
    } finally {
      setIsTestingConnection(false);
    }
  };

  const handleConnectDataSource = async (sourceId: string) => {
    try {
      await backendDataService.connectDataSource(sourceId);
      if (onDataSourceChange) {
        onDataSourceChange(sourceId);
      }
    } catch (error: any) {
      setError(`Failed to connect to data source: ${error.message}`);
    }
  };

  const handleDisconnectDataSource = async (sourceId: string) => {
          try {
        await backendDataService.disconnectDataSource(sourceId);
      } catch (error: any) {
        setError(`Failed to disconnect from data source: ${error.message}`);
      }
  };

  const getConnectionStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'success';
      case 'connecting': return 'warning';
      case 'disconnected': return 'default';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  const getDataSourceIcon = (type: string) => {
    switch (type) {
      case 'database': return <Storage />;
      case 'api': return <Api />;
      case 'file': return <Description />;
      case 'stream': return <Stream />;
      case 'cloud': return <CloudQueue />;
      default: return <DataUsage />;
    }
  };

  const getDataSourceTypeColor = (type: string) => {
    switch (type) {
      case 'database': return 'primary';
      case 'api': return 'secondary';
      case 'file': return 'success';
      case 'stream': return 'warning';
      case 'cloud': return 'info';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6">Data Source Management</Typography>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={handleAddDataSource}
        >
          Add Data Source
        </Button>
      </Box>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tabValue} onChange={handleTabChange}>
          <Tab label="Overview" />
          <Tab label="Configuration" />
          <Tab label="Monitoring" />
          <Tab label="Schema" />
        </Tabs>
      </Box>

      {/* Overview Tab */}
      <TabPanel value={tabValue} index={0}>
        <Grid container spacing={2}>
          {dataSources.map((source) => {
            const status = dataSourceStatuses.find(s => s.id === source.id);
            const isConnected = status?.status === 'connected';
            const testResult = testResults[source.id];
            
            return (
              <Grid item xs={12} md={6} key={source.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      {getDataSourceIcon(source.type)}
                      <Typography variant="subtitle1">{source.name}</Typography>
                      <Chip 
                        label={source.type} 
                        color={getDataSourceTypeColor(source.type)}
                        size="small"
                        variant="outlined"
                      />
                    </Box>
                    
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {source.connectionString}
                    </Typography>

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                      <Chip 
                        label={status?.status || 'unknown'} 
                        color={getConnectionStatusColor(status?.status || 'disconnected')}
                        size="small"
                      />
                      {testResult !== undefined && (
                        <Chip 
                          label={testResult ? 'Test Passed' : 'Test Failed'} 
                          color={testResult ? 'success' : 'error'}
                          size="small"
                          icon={testResult ? <CheckCircle /> : <Error />}
                        />
                      )}
                    </Box>

                    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Button
                        size="small"
                        variant={isConnected ? 'outlined' : 'contained'}
                        onClick={() => isConnected 
                          ? handleDisconnectDataSource(source.id)
                          : handleConnectDataSource(source.id)
                        }
                      >
                        {isConnected ? 'Disconnect' : 'Connect'}
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleTestConnection(source.id)}
                        disabled={isTestingConnection}
                      >
                        Test
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleEditDataSource(source)}
                      >
                        Edit
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        color="error"
                        onClick={() => handleDeleteDataSource(source.id)}
                      >
                        Delete
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </TabPanel>

      {/* Configuration Tab */}
      <TabPanel value={tabValue} index={1}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Data Source Configuration
          </Typography>
          <Grid container spacing={2}>
            {dataSources.map((source) => (
              <Grid item xs={12} key={source.id}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getDataSourceIcon(source.type)}
                      <Typography>{source.name}</Typography>
                      <Chip label={source.type} size="small" />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Name"
                          value={source.name}
                          disabled
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Type"
                          value={source.type}
                          disabled
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="Connection String"
                          value={source.connectionString || ''}
                          disabled
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Timeout (ms)"
                          value={source.options?.timeout || ''}
                          disabled
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <TextField
                          fullWidth
                          label="Max Connections"
                          value={source.options?.maxConnections || ''}
                          disabled
                          size="small"
                        />
                      </Grid>
                      <Grid item xs={12}>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <FormControlLabel
                            control={
                              <Switch
                                checked={source.options?.ssl || false}
                                disabled
                              />
                            }
                            label="SSL"
                          />
                          <FormControlLabel
                            control={
                              <Switch
                                checked={source.options?.cache || false}
                                disabled
                              />
                            }
                            label="Cache"
                          />
                          <FormControlLabel
                            control={
                              <Switch
                                checked={source.options?.compression || false}
                                disabled
                              />
                            }
                            label="Compression"
                          />
                        </Box>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              </Grid>
            ))}
          </Grid>
        </Paper>
      </TabPanel>

      {/* Monitoring Tab */}
      <TabPanel value={tabValue} index={2}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Performance Monitoring
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Data Source</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Avg Query Time</TableCell>
                  <TableCell>Total Queries</TableCell>
                  <TableCell>Failed Queries</TableCell>
                  <TableCell>Error Rate</TableCell>
                  <TableCell>Last Connection</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {dataSourceStatuses.map((status) => {
                  const source = dataSources.find(s => s.id === status.id);
                  const errorRate = status.performance.totalQueries > 0 
                    ? (status.performance.failedQueries / status.performance.totalQueries) * 100 
                    : 0;
                  
                  return (
                    <TableRow key={status.id}>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {source && getDataSourceIcon(source.type)}
                          {source?.name || status.id}
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={status.status} 
                          color={getConnectionStatusColor(status.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{status.performance.avgQueryTime.toFixed(2)}ms</TableCell>
                      <TableCell>{status.performance.totalQueries}</TableCell>
                      <TableCell>{status.performance.failedQueries}</TableCell>
                      <TableCell>
                        <Chip 
                          label={`${errorRate.toFixed(1)}%`} 
                          color={errorRate > 10 ? 'error' : errorRate > 5 ? 'warning' : 'success'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{status.lastConnection.toLocaleString()}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </TabPanel>

      {/* Schema Tab */}
      <TabPanel value={tabValue} index={3}>
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Schema Information
          </Typography>
          <Grid container spacing={2}>
            {dataSources.map((source) => (
              <Grid item xs={12} key={source.id}>
                <Accordion>
                  <AccordionSummary expandIcon={<ExpandMore />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getDataSourceIcon(source.type)}
                      <Typography>{source.name}</Typography>
                      <Chip label="Schema" size="small" />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Typography variant="body2" color="text.secondary">
                      Schema information will be displayed here when connected to the data source.
                    </Typography>
                  </AccordionDetails>
                </Accordion>
              </Grid>
            ))}
          </Grid>
        </Paper>
      </TabPanel>

      {/* Add Data Source Dialog */}
      <Dialog open={isAddDialogOpen} onClose={() => setIsAddDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Add New Data Source</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={formData.type}
                  onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value as any }))}
                  label="Type"
                >
                  <MenuItem value="database">Database</MenuItem>
                  <MenuItem value="api">API</MenuItem>
                  <MenuItem value="file">File</MenuItem>
                  <MenuItem value="stream">Stream</MenuItem>
                  <MenuItem value="cloud">Cloud</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Connection String"
                value={formData.connectionString}
                onChange={(e) => setFormData(prev => ({ ...prev, connectionString: e.target.value }))}
                placeholder="e.g., postgresql://localhost:5432/db, https://api.example.com, /path/to/file"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Timeout (ms)"
                type="number"
                value={formData.options?.timeout}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  options: { ...prev.options, timeout: Number(e.target.value) }
                }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Connections"
                type="number"
                value={formData.options?.maxConnections}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  options: { ...prev.options, maxConnections: Number(e.target.value) }
                }))}
              />
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.options?.ssl || false}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        options: { ...prev.options, ssl: e.target.checked }
                      }))}
                    />
                  }
                  label="SSL"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.options?.cache || false}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        options: { ...prev.options, cache: e.target.checked }
                      }))}
                    />
                  }
                  label="Cache"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.options?.compression || false}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        options: { ...prev.options, compression: e.target.checked }
                      }))}
                    />
                  }
                  label="Compression"
                />
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsAddDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveDataSource} variant="contained">Save</Button>
        </DialogActions>
      </Dialog>

      {/* Edit Data Source Dialog */}
      <Dialog open={isEditDialogOpen} onClose={() => setIsEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Data Source</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                required
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={formData.type}
                  onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value as any }))}
                  label="Type"
                >
                  <MenuItem value="database">Database</MenuItem>
                  <MenuItem value="api">API</MenuItem>
                  <MenuItem value="file">File</MenuItem>
                  <MenuItem value="stream">Stream</MenuItem>
                  <MenuItem value="cloud">Cloud</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Connection String"
                value={formData.connectionString}
                onChange={(e) => setFormData(prev => ({ ...prev, connectionString: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Timeout (ms)"
                type="number"
                value={formData.options?.timeout}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  options: { ...prev.options, timeout: Number(e.target.value) }
                }))}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Max Connections"
                type="number"
                value={formData.options?.maxConnections}
                onChange={(e) => setFormData(prev => ({ 
                  ...prev, 
                  options: { ...prev.options, maxConnections: Number(e.target.value) }
                }))}
              />
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.options?.ssl || false}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        options: { ...prev.options, ssl: e.target.checked }
                      }))}
                    />
                  }
                  label="SSL"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.options?.cache || false}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        options: { ...prev.options, cache: e.target.checked }
                      }))}
                    />
                  }
                  label="Cache"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={formData.options?.compression || false}
                      onChange={(e) => setFormData(prev => ({ 
                        ...prev, 
                        options: { ...prev.options, compression: e.target.checked }
                      }))}
                    />
                  }
                  label="Compression"
                />
              </Box>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveDataSource} variant="contained">Update</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default DataSourceManagementPanel;
