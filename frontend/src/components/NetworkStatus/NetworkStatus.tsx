import React, { useState, useEffect } from 'react';
import {
  Box,
  Chip,
  IconButton,
  Tooltip,
  Typography,
  Collapse,
  Alert,
  AlertTitle,
  LinearProgress,
  useTheme,
} from '@mui/material';
import {
  Wifi,
  WifiOff,
  SignalCellular4Bar,
  SignalCellularConnectedNoInternet4Bar,
  Refresh,
  ExpandMore,
  ExpandLess,
  Speed,
  Router,
} from '@mui/icons-material';
import { useError } from '../../context/ErrorContext';
import { enhancedApiService } from '../../services/enhancedApiService';

interface NetworkMetrics {
  latency: number;
  connectionType: string;
  lastChecked: Date;
  isStable: boolean;
}

export const NetworkStatus: React.FC = () => {
  const theme = useTheme();
  const { state: errorState, checkNetworkStatus } = useError();
  const [isExpanded, setIsExpanded] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [metrics, setMetrics] = useState<NetworkMetrics>({
    latency: -1,
    connectionType: 'unknown',
    lastChecked: new Date(),
    isStable: true,
  });

  const { networkStatus } = errorState;

  // Check network status and get metrics
  const performNetworkCheck = async () => {
    setIsChecking(true);
    try {
      const status = await enhancedApiService.getNetworkStatus();
      
      setMetrics({
        latency: status.latency,
        connectionType: status.connectionType || 'unknown',
        lastChecked: new Date(),
        isStable: status.latency > 0 && status.latency < 1000,
      });

      // Update error context network status
      await checkNetworkStatus();
    } catch (error) {
      console.error('Network check failed:', error);
      setMetrics(prev => ({
        ...prev,
        latency: -1,
        isStable: false,
        lastChecked: new Date(),
      }));
    } finally {
      setIsChecking(false);
    }
  };

  // Auto-check network status every 30 seconds
  useEffect(() => {
    const interval = setInterval(performNetworkCheck, 30000);
    performNetworkCheck(); // Initial check

    return () => clearInterval(interval);
  }, []);

  // Get network status icon
  const getNetworkIcon = () => {
    if (!networkStatus.isOnline) {
      return <WifiOff color="error" />;
    }

    if (metrics.latency > 1000) {
      return <SignalCellularConnectedNoInternet4Bar color="warning" />;
    }

    if (metrics.connectionType === 'cellular') {
      return <SignalCellular4Bar color="success" />;
    }

    return <Wifi color="success" />;
  };

  // Get network status color
  const getNetworkColor = () => {
    if (!networkStatus.isOnline) return 'error';
    if (metrics.latency > 1000) return 'warning';
    if (metrics.latency > 500) return 'warning';
    return 'success';
  };

  // Get network status text
  const getNetworkStatusText = () => {
    if (!networkStatus.isOnline) return 'Offline';
    if (metrics.latency === -1) return 'Checking...';
    if (metrics.latency > 1000) return 'Slow';
    if (metrics.latency > 500) return 'Fair';
    return 'Good';
  };

  // Get latency color
  const getLatencyColor = () => {
    if (metrics.latency === -1) return theme.palette.grey[500];
    if (metrics.latency < 100) return theme.palette.success.main;
    if (metrics.latency < 500) return theme.palette.warning.main;
    return theme.palette.error.main;
  };

  // Format latency
  const formatLatency = (latency: number) => {
    if (latency === -1) return 'Unknown';
    if (latency < 1000) return `${latency}ms`;
    return `${(latency / 1000).toFixed(1)}s`;
  };

  // Get connection type display text
  const getConnectionTypeText = (type: string) => {
    switch (type) {
      case 'wifi':
        return 'WiFi';
      case 'cellular':
        return 'Cellular';
      case 'ethernet':
        return 'Ethernet';
      default:
        return 'Unknown';
    }
  };

  // Get connection type icon
  const getConnectionTypeIcon = (type: string) => {
    switch (type) {
      case 'wifi':
        return <Wifi fontSize="small" />;
      case 'cellular':
        return <SignalCellular4Bar fontSize="small" />;
      case 'ethernet':
        return <Router fontSize="small" />;
      default:
        return <Router fontSize="small" />;
    }
  };

  return (
    <Box>
      {/* Main Network Status Bar */}
      <Box
        display="flex"
        alignItems="center"
        gap={1}
        p={1}
        sx={{
          cursor: 'pointer',
          borderRadius: 1,
          '&:hover': {
            backgroundColor: theme.palette.action.hover,
          },
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {getNetworkIcon()}
        
        <Box display="flex" alignItems="center" gap={1}>
          <Chip
            label={getNetworkStatusText()}
            color={getNetworkColor()}
            size="small"
            variant="outlined"
          />
          
          {networkStatus.isOnline && metrics.latency > 0 && (
            <Box display="flex" alignItems="center" gap={0.5}>
              <Speed fontSize="small" />
              <Typography
                variant="caption"
                color={getLatencyColor()}
                sx={{ fontWeight: 'bold' }}
              >
                {formatLatency(metrics.latency)}
              </Typography>
            </Box>
          )}
        </Box>

        <Box ml="auto" display="flex" alignItems="center" gap={1}>
          <Tooltip title="Check Network Status">
            <IconButton
              size="small"
              onClick={(e) => {
                e.stopPropagation();
                performNetworkCheck();
              }}
              disabled={isChecking}
              sx={{ color: theme.palette.primary.main }}
            >
              <Refresh className={isChecking ? 'spin' : ''} />
            </IconButton>
          </Tooltip>
          
          {isExpanded ? <ExpandLess /> : <ExpandMore />}
        </Box>
      </Box>

      {/* Expanded Network Details */}
      <Collapse in={isExpanded}>
        <Box p={2} borderTop={1} borderColor="divider">
          {/* Network Status Alert */}
          {!networkStatus.isOnline && (
            <Alert severity="error" sx={{ mb: 2 }}>
              <AlertTitle>Network Connection Lost</AlertTitle>
              You are currently offline. Some features may be unavailable.
            </Alert>
          )}

          {networkStatus.isOnline && metrics.latency > 1000 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              <AlertTitle>Slow Network Connection</AlertTitle>
              Your connection is experiencing high latency. This may affect performance.
            </Alert>
          )}

          {/* Network Metrics */}
          <Box display="flex" flexDirection="column" gap={2}>
            {/* Connection Type */}
            <Box display="flex" alignItems="center" gap={1}>
              {getConnectionTypeIcon(metrics.connectionType)}
              <Typography variant="body2" color="textSecondary">
                Connection Type:
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {getConnectionTypeText(metrics.connectionType)}
              </Typography>
            </Box>

            {/* Latency */}
            {metrics.latency > 0 && (
              <Box>
                <Box display="flex" justifyContent="space-between" mb={1}>
                  <Typography variant="body2" color="textSecondary">
                    Response Time
                  </Typography>
                  <Typography
                    variant="body2"
                    fontWeight="bold"
                    color={getLatencyColor()}
                  >
                    {formatLatency(metrics.latency)}
                  </Typography>
                </Box>
                
                <LinearProgress
                  variant="determinate"
                  value={Math.min((metrics.latency / 1000) * 100, 100)}
                  sx={{
                    height: 6,
                    borderRadius: 3,
                    backgroundColor: theme.palette.grey[200],
                    '& .MuiLinearProgress-bar': {
                      backgroundColor: getLatencyColor(),
                    },
                  }}
                />
                
                <Box display="flex" justifyContent="space-between" mt={0.5}>
                  <Typography variant="caption" color="textSecondary">
                    Good
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    Poor
                  </Typography>
                </Box>
              </Box>
            )}

            {/* Last Checked */}
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="body2" color="textSecondary">
                Last Checked:
              </Typography>
              <Typography variant="body2">
                {metrics.lastChecked.toLocaleTimeString()}
              </Typography>
            </Box>

            {/* Network Stability */}
            <Box display="flex" alignItems="center" gap={1}>
              <Typography variant="body2" color="textSecondary">
                Stability:
              </Typography>
              <Chip
                label={metrics.isStable ? 'Stable' : 'Unstable'}
                color={metrics.isStable ? 'success' : 'warning'}
                size="small"
                variant="outlined"
              />
            </Box>
          </Box>

          {/* Manual Network Check Button */}
          <Box mt={2}>
            <Tooltip title="Perform a manual network check">
              <IconButton
                onClick={performNetworkCheck}
                disabled={isChecking}
                variant="outlined"
                size="small"
                fullWidth
              >
                <Refresh className={isChecking ? 'spin' : ''} />
                <Typography variant="body2" ml={1}>
                  {isChecking ? 'Checking...' : 'Check Network'}
                </Typography>
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
      </Collapse>

      {/* CSS for spinning animation */}
      <style jsx>{`
        .spin {
          animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </Box>
  );
};

export default NetworkStatus;
