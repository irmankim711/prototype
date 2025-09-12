import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  IconButton,
  Tooltip,
  Collapse,
  Alert,
  AlertTitle,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Badge,
  Divider,
  useTheme,
} from '@mui/material';
import {
  Error,
  Warning,
  Info,
  Refresh,
  ClearAll,
  ExpandMore,
  ExpandLess,
  Timeline,
  Speed,
  NetworkCheck,
  BugReport,
  Security,
  CheckCircle,
} from '@mui/icons-material';
import { useError } from '../../context/ErrorContext';
import { formatDistanceToNow } from 'date-fns';

export const ErrorDashboard: React.FC = () => {
  const theme = useTheme();
  const { state, removeError, clearAllErrors, retryError, retryAllErrors } = useError();
  const [expandedErrors, setExpandedErrors] = useState<Set<string>>(new Set());
  const [selectedErrorType, setSelectedErrorType] = useState<string | null>(null);

  const { errors, networkStatus, globalErrorCount, isRetrying } = state;

  // Toggle error expansion
  const toggleErrorExpansion = (errorId: string) => {
    const newExpanded = new Set(expandedErrors);
    if (newExpanded.has(errorId)) {
      newExpanded.delete(errorId);
    } else {
      newExpanded.add(errorId);
    }
    setExpandedErrors(newExpanded);
  };

  // Filter errors by type
  const filteredErrors = selectedErrorType
    ? errors.filter(error => error.errorType === selectedErrorType)
    : errors;

  // Get error statistics
  const getErrorStats = () => {
    const stats = {
      total: errors.length,
      api: errors.filter(e => e.errorType === 'api').length,
      network: errors.filter(e => e.errorType === 'network').length,
      validation: errors.filter(e => e.errorType === 'validation').length,
      auth: errors.filter(e => e.errorType === 'auth').length,
      unknown: errors.filter(e => e.errorType === 'unknown').length,
      retryable: errors.filter(e => e.retryCount < e.maxRetries).length,
      retrying: errors.filter(e => e.isRetrying).length,
    };

    return stats;
  };

  // Get error type icon
  const getErrorTypeIcon = (errorType: string) => {
    switch (errorType) {
      case 'api':
        return <BugReport color="error" />;
      case 'network':
        return <NetworkCheck color="warning" />;
      case 'validation':
        return <Info color="info" />;
      case 'auth':
        return <Security color="warning" />;
      default:
        return <Error color="error" />;
    }
  };

  // Get error type color
  const getErrorTypeColor = (errorType: string) => {
    switch (errorType) {
      case 'api':
        return 'error';
      case 'network':
        return 'warning';
      case 'validation':
        return 'info';
      case 'auth':
        return 'warning';
      default:
        return 'error';
    }
  };

  // Get error severity
  const getErrorSeverity = (error: any) => {
    if (error.errorType === 'auth') return 'High';
    if (error.errorType === 'api' && error.status >= 500) return 'High';
    if (error.errorType === 'network') return 'Medium';
    if (error.errorType === 'validation') return 'Low';
    return 'Medium';
  };

  // Get error severity color
  const getErrorSeverityColor = (severity: string) => {
    switch (severity) {
      case 'High':
        return 'error';
      case 'Medium':
        return 'warning';
      case 'Low':
        return 'info';
      default:
        return 'default';
    }
  };

  // Format timestamp
  const formatTimestamp = (timestamp: Date) => {
    return formatDistanceToNow(timestamp, { addSuffix: true });
  };

  // Get retry status text
  const getRetryStatusText = (error: any) => {
    if (error.isRetrying) return 'Retrying...';
    if (error.retryCount >= error.maxRetries) return 'Max retries reached';
    if (error.retryCount > 0) return `${error.retryCount} retries attempted`;
    return 'No retries yet';
  };

  const stats = getErrorStats();

  return (
    <Box>
      {/* Header */}
      <Box display="flex" alignItems="center" gap={2} mb={3}>
        <Error sx={{ fontSize: 32, color: theme.palette.error.main }} />
        <Typography variant="h4" component="h1">
          Error Dashboard
        </Typography>
        <Badge badgeContent={globalErrorCount} color="error">
          <Chip
            label={`${globalErrorCount} Total Errors`}
            color={globalErrorCount > 0 ? 'error' : 'default'}
            variant="outlined"
          />
        </Badge>
      </Box>

      {/* Network Status Alert */}
      {!networkStatus.isOnline && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <AlertTitle>Network Offline</AlertTitle>
          You are currently offline. Some errors may be due to network connectivity issues.
        </Alert>
      )}

      {/* Error Statistics */}
      <Box display="flex" gap={2} mb={3} flexWrap="wrap">
        <Card sx={{ minWidth: 120 }}>
          <CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" color="error">
              {stats.total}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Total Errors
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 120 }}>
          <CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" color="warning">
              {stats.retryable}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Retryable
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 120 }}>
          <CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" color="info">
              {stats.network}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Network Errors
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 120 }}>
          <CardContent sx={{ textAlign: 'center', py: 2 }}>
            <Typography variant="h4" color="success">
              {stats.api}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              API Errors
            </Typography>
          </CardContent>
        </Card>
      </Box>

      {/* Error Type Filter */}
      <Box display="flex" gap={1} mb={3} flexWrap="wrap">
        <Button
          variant={selectedErrorType === null ? 'contained' : 'outlined'}
          size="small"
          onClick={() => setSelectedErrorType(null)}
        >
          All ({stats.total})
        </Button>
        <Button
          variant={selectedErrorType === 'api' ? 'contained' : 'outlined'}
          size="small"
          color="error"
          onClick={() => setSelectedErrorType('api')}
        >
          API ({stats.api})
        </Button>
        <Button
          variant={selectedErrorType === 'network' ? 'contained' : 'outlined'}
          size="small"
          color="warning"
          onClick={() => setSelectedErrorType('network')}
        >
          Network ({stats.network})
        </Button>
        <Button
          variant={selectedErrorType === 'validation' ? 'contained' : 'outlined'}
          size="small"
          color="info"
          onClick={() => setSelectedErrorType('validation')}
        >
          Validation ({stats.validation})
        </Button>
        <Button
          variant={selectedErrorType === 'auth' ? 'contained' : 'outlined'}
          size="small"
          color="warning"
          onClick={() => setSelectedErrorType('auth')}
        >
          Auth ({stats.auth})
        </Button>
      </Box>

      {/* Action Buttons */}
      <Box display="flex" gap={2} mb={3}>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={retryAllErrors}
          disabled={isRetrying || stats.retryable === 0}
        >
          {isRetrying ? 'Retrying...' : `Retry All (${stats.retryable})`}
        </Button>
        
        <Button
          variant="outlined"
          startIcon={<ClearAll />}
          onClick={clearAllErrors}
          disabled={errors.length === 0}
          color="error"
        >
          Clear All Errors
        </Button>
      </Box>

      {/* Errors Table */}
      {filteredErrors.length > 0 ? (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Type</TableCell>
                <TableCell>Message</TableCell>
                <TableCell>Endpoint</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Retry Status</TableCell>
                <TableCell>Timestamp</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredErrors.map((error) => (
                <React.Fragment key={error.id}>
                  <TableRow
                    hover
                    sx={{
                      backgroundColor: error.isRetrying
                        ? theme.palette.action.hover
                        : 'inherit',
                    }}
                  >
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {getErrorTypeIcon(error.errorType)}
                        <Chip
                          label={error.errorType.toUpperCase()}
                          color={getErrorTypeColor(error.errorType)}
                          size="small"
                        />
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 200 }}>
                        {error.message}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" noWrap sx={{ maxWidth: 150 }}>
                        {error.endpoint || 'N/A'}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        {error.status && (
                          <Chip
                            label={error.status}
                            color={error.status >= 500 ? 'error' : 'warning'}
                            size="small"
                            variant="outlined"
                          />
                        )}
                        <Chip
                          label={getErrorSeverity(error)}
                          color={getErrorSeverityColor(getErrorSeverity(error))}
                          size="small"
                          variant="outlined"
                        />
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="body2" color="textSecondary">
                          {getRetryStatusText(error)}
                        </Typography>
                        {error.isRetrying && (
                          <LinearProgress
                            sx={{ width: 60, height: 4 }}
                            color="primary"
                          />
                        )}
                      </Box>
                    </TableCell>
                    
                    <TableCell>
                      <Typography variant="body2" color="textSecondary">
                        {formatTimestamp(error.timestamp)}
                      </Typography>
                    </TableCell>
                    
                    <TableCell>
                      <Box display="flex" gap={1}>
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={() => toggleErrorExpansion(error.id)}
                          >
                            {expandedErrors.has(error.id) ? <ExpandLess /> : <ExpandMore />}
                          </IconButton>
                        </Tooltip>
                        
                        {error.retryCount < error.maxRetries && !error.isRetrying && (
                          <Tooltip title="Retry Request">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => retryError(error.id)}
                            >
                              <Refresh />
                            </IconButton>
                          </Tooltip>
                        )}
                        
                        <Tooltip title="Remove Error">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={() => removeError(error.id)}
                          >
                            <CheckCircle />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                  
                  {/* Expanded Error Details */}
                  <TableRow>
                    <TableCell colSpan={7} sx={{ py: 0 }}>
                      <Collapse in={expandedErrors.has(error.id)}>
                        <Box p={2} bgcolor={theme.palette.grey[50]}>
                          <Typography variant="h6" gutterBottom>
                            Error Details
                          </Typography>
                          
                          <Box display="flex" flexDirection="column" gap={2}>
                            {/* Error Context */}
                            {error.context && (
                              <Box>
                                <Typography variant="subtitle2" gutterBottom>
                                  Context Information:
                                </Typography>
                                <Box component="pre" sx={{ fontSize: '0.875rem' }}>
                                  {JSON.stringify(error.context, null, 2)}
                                </Box>
                              </Box>
                            )}
                            
                            {/* Retry Information */}
                            <Box display="flex" gap={2}>
                              <Typography variant="body2">
                                <strong>Retry Count:</strong> {error.retryCount} / {error.maxRetries}
                              </Typography>
                              <Typography variant="body2">
                                <strong>Last Attempt:</strong> {formatTimestamp(error.timestamp)}
                              </Typography>
                            </Box>
                            
                            {/* Error Stack (if available) */}
                            {error.context?.stack && (
                              <Box>
                                <Typography variant="subtitle2" gutterBottom>
                                  Stack Trace:
                                </Typography>
                                <Box
                                  component="pre"
                                  sx={{
                                    fontSize: '0.75rem',
                                    maxHeight: 200,
                                    overflow: 'auto',
                                    bgcolor: theme.palette.grey[100],
                                    p: 1,
                                    borderRadius: 1,
                                  }}
                                >
                                  {error.context.stack}
                                </Box>
                              </Box>
                            )}
                          </Box>
                        </Box>
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      ) : (
        <Card>
          <CardContent sx={{ textAlign: 'center', py: 4 }}>
            <CheckCircle sx={{ fontSize: 64, color: theme.palette.success.main, mb: 2 }} />
            <Typography variant="h6" color="textSecondary">
              No Errors Found
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {selectedErrorType
                ? `No ${selectedErrorType} errors to display.`
                : 'All systems are running smoothly!'}
            </Typography>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default ErrorDashboard;
