/**
 * Real-time Data Panel
 * Displays live data updates, connection status, and performance metrics
 */

import React, { useState, useEffect, useCallback } from 'react';
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
  Switch,
  FormControlLabel,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel
} from '@mui/material';
import { 
  ExpandMore, 
  Wifi, 
  WifiOff, 
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
  Stream
} from '@mui/icons-material';
import type { DataUpdate, RealTimeStats, SubscriptionConfig } from '../../services/realTimeDataService';
import type { DataSourceConfig, DataSourceStatus, DataSourceHealth } from '../../services/backendDataService';
import { realTimeDataService } from '../../services/realTimeDataService';
import { backendDataService } from '../../services/backendDataService';

interface RealTimeDataPanelProps {
  onDataUpdate?: (update: DataUpdate) => void;
  onDataSourceChange?: (sourceId: string) => void;
}

const RealTimeDataPanel: React.FC<RealTimeDataPanelProps> = ({ 
  onDataUpdate, 
  onDataSourceChange 
}) => {
  const theme = useTheme();
  const [isConnected, setIsConnected] = useState(false);
  const [realTimeStats, setRealTimeStats] = useState<RealTimeStats | null>(null);
  const [dataUpdates, setDataUpdates] = useState<DataUpdate[]>([]);
  const [dataSources, setDataSources] = useState<DataSourceConfig[]>([]);
  const [dataSourceStatuses, setDataSourceStatuses] = useState<DataSourceStatus[]>([]);
  const [selectedDataSource, setSelectedDataSource] = useState<string>('');
  const [autoConnect, setAutoConnect] = useState(false);
  const [updateBufferSize, setUpdateBufferSize] = useState(100);
  const [connectionEndpoint, setConnectionEndpoint] = useState('ws://localhost:8000/ws/data');
  const [streamSource, setStreamSource] = useState<'websocket' | 'server-sent-events' | 'polling'>('websocket');
  const [updateFrequency, setUpdateFrequency] = useState(1000);

  useEffect(() => {
    // Initialize data sources
    const sources = backendDataService.getDataSources();
    setDataSources(sources);
    if (sources.length > 0) {
      setSelectedDataSource(sources[0].id);
    }

    // Set up real-time data subscription
    const subscriptionId = 'realtime-panel';
    realTimeDataService.subscribe(subscriptionId, handleDataUpdate);

    // Start stats monitoring
    const statsInterval = setInterval(() => {
      setRealTimeStats(realTimeDataService.getStats());
    }, 1000);

    return () => {
      realTimeDataService.unsubscribe(subscriptionId);
      clearInterval(statsInterval);
    };
  }, []);

  useEffect(() => {
    // Monitor data source statuses
    const statusInterval = setInterval(() => {
      setDataSourceStatuses(backendDataService.getAllDataSourceStatuses());
    }, 2000);

    return () => clearInterval(statusInterval);
  }, []);

  const handleDataUpdate = useCallback((update: DataUpdate) => {
    setDataUpdates(prev => {
      const newUpdates = [update, ...prev.slice(0, updateBufferSize - 1)];
      return newUpdates;
    });

    if (onDataUpdate) {
      onDataUpdate(update);
    }
  }, [onDataUpdate, updateBufferSize]);

  const handleConnect = async () => {
    try {
      // Connection logic would be implemented here
      // This would typically establish a WebSocket or SSE connection
      
      // Simulate connection delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setIsConnected(true);
    } catch (error: any) {
      // Handle connection error silently for now
      // In production, this would show user feedback
    }
  };

  const handleDisconnect = () => {
    realTimeDataService.disconnect();
    setIsConnected(false);
  };

  const handleDataSourceConnect = async (sourceId: string) => {
    try {
      await backendDataService.connectDataSource(sourceId);
      if (onDataSourceChange) {
        onDataSourceChange(sourceId);
      }
    } catch (error: any) {
      // Handle connection error silently for now
      // In production, this would show user feedback
    }
  };

  const handleDataSourceDisconnect = async (sourceId: string) => {
    try {
      await backendDataService.disconnectDataSource(sourceId);
    } catch (error: any) {
      // Handle disconnection error silently for now
      // In production, this would show user feedback
    }
  };

  const handleTestConnection = async (sourceId: string) => {
    try {
      const isHealthy = await backendDataService.testConnection(sourceId);
      if (isHealthy) {
        // Connection test successful
      } else {
        // Connection test failed
      }
    } catch (error: any) {
      // Handle connection test error silently for now
      // In production, this would show user feedback
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

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Real-time Data Monitoring
      </Typography>

      {/* Connection Controls */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <Typography variant="subtitle1">Real-time Connection</Typography>
          <Chip 
            label={isConnected ? 'Connected' : 'Disconnected'} 
            color={isConnected ? 'success' : 'default'}
            icon={isConnected ? <Wifi /> : <WifiOff />}
          />
          <Button
            variant="contained"
            startIcon={isConnected ? <Stop /> : <PlayArrow />}
            onClick={isConnected ? handleDisconnect : handleConnect}
            color={isConnected ? 'error' : 'primary'}
          >
            {isConnected ? 'Disconnect' : 'Connect'}
          </Button>
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <FormControl fullWidth size="small">
              <InputLabel>Stream Source</InputLabel>
              <Select
                value={streamSource}
                onChange={(e) => setStreamSource(e.target.value as any)}
                label="Stream Source"
              >
                <MenuItem value="websocket">WebSocket</MenuItem>
                <MenuItem value="server-sent-events">Server-Sent Events</MenuItem>
                <MenuItem value="polling">Polling</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              size="small"
              label="Update Frequency (ms)"
              type="number"
              value={updateFrequency}
              onChange={(e) => setUpdateFrequency(Number(e.target.value))}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              size="small"
              label="Connection Endpoint"
              value={connectionEndpoint}
              onChange={(e) => setConnectionEndpoint(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              size="small"
              label="Buffer Size"
              type="number"
              value={updateBufferSize}
              onChange={(e) => setUpdateBufferSize(Number(e.target.value))}
            />
          </Grid>
        </Grid>
      </Paper>

      {/* Real-time Statistics */}
      {realTimeStats && (
        <Paper sx={{ p: 2, mb: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Connection Statistics
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {realTimeStats.messagesReceived}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Messages Received
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="secondary">
                    {realTimeStats.messagesSent}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Messages Sent
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="info">
                    {formatDuration(realTimeStats.connectionUptime)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Uptime
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={6} md={3}>
              <Card>
                <CardContent sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="success">
                    {realTimeStats.dataLatency}ms
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Latency
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Data Sources */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Typography variant="subtitle1" gutterBottom>
          Data Sources
        </Typography>
        <Grid container spacing={2}>
          {dataSources.map((source) => {
            const status = dataSourceStatuses.find(s => s.id === source.id);
            const isConnected = status?.status === 'connected';
            
            return (
              <Grid item xs={12} md={6} key={source.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      {getDataSourceIcon(source.type)}
                      <Typography variant="subtitle2">{source.name}</Typography>
                      <Chip 
                        label={status?.status || 'unknown'} 
                        color={getConnectionStatusColor(status?.status || 'disconnected')}
                        size="small"
                      />
                    </Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {source.type} • {source.connectionString}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                      <Button
                        size="small"
                        variant={isConnected ? 'outlined' : 'contained'}
                        onClick={() => isConnected 
                          ? handleDataSourceDisconnect(source.id)
                          : handleDataSourceConnect(source.id)
                        }
                      >
                        {isConnected ? 'Disconnect' : 'Connect'}
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleTestConnection(source.id)}
                      >
                        Test
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      </Paper>

      {/* Live Data Updates */}
      <Paper sx={{ p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
          <Typography variant="subtitle1">Live Data Updates</Typography>
          <Chip 
            label={`${dataUpdates.length} updates`} 
            color="primary" 
            size="small"
          />
        </Box>
        
        <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
          {dataUpdates.length === 0 ? (
            <Alert severity="info">No data updates yet. Connect to a data source to see live updates.</Alert>
          ) : (
            <List dense>
              {dataUpdates.map((update, index) => (
                <ListItem key={index} divider>
                  <ListItemIcon>
                    <Timeline color="primary" />
                  </ListItemIcon>
                  <ListItemText
                    primary={`${update.type} from ${update.source}`}
                    secondary={`${update.timestamp.toLocaleTimeString()} • ${Array.isArray(update.data) ? update.data.length : 1} records`}
                  />
                  <Chip 
                    label={update.type} 
                    size="small" 
                    color="primary" 
                    variant="outlined"
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Box>
      </Paper>
    </Box>
  );
};

export default RealTimeDataPanel;
