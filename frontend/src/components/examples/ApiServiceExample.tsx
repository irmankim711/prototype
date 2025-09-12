import React, { useEffect, useState } from 'react';
import { 
  Box, 
  Button, 
  Card, 
  CardContent, 
  Typography, 
  Alert, 
  CircularProgress,
  TextField,
  Grid
} from '@mui/material';
import useApi, { useApiData, useApiMutation } from '../../hooks/useApi';
import apiService from '../../services/apiService';
import type { User, Report } from '../../types/api.types';

/**
 * Example component demonstrating the new API service usage
 */
export const ApiServiceExample: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loginMessage, setLoginMessage] = useState('');

  // Using the general useApi hook
  const { get, post, isLoading, getCurrentError, clearError } = useApi();

  // Using the specialized useApiData hook for fetching data
  const { 
    data: users, 
    loading: usersLoading, 
    error: usersError, 
    refetch: refetchUsers 
  } = useApiData<User[]>('/users');

  // Using the specialized useApiMutation hook for mutations
  const { 
    mutate: createUser, 
    loading: createUserLoading, 
    error: createUserError, 
    reset: resetCreateUser 
  } = useApiMutation<User>();

  // Example: Fetch users on component mount
  useEffect(() => {
    refetchUsers();
  }, [refetchUsers]);

  // Example: Login using the API service
  const handleLogin = async () => {
    try {
      setLoginMessage('');
      const response = await apiService.login({ email, password });
      setLoginMessage(`Login successful! Welcome ${response.user.first_name || response.user.email}`);
      
      // Clear form
      setEmail('');
      setPassword('');
    } catch (error: any) {
      setLoginMessage(`Login failed: ${error.message}`);
    }
  };

  // Example: Fetch reports using the general hook
  const handleFetchReports = async () => {
    try {
      clearError();
      const reports = await get<Report[]>('/reports');
      console.log('Reports fetched:', reports);
    } catch (error) {
      console.error('Failed to fetch reports:', error);
    }
  };

  // Example: Create a new user using the mutation hook
  const handleCreateUser = async () => {
    try {
      const newUser = await createUser('POST', '/users', {
        email: 'newuser@example.com',
        password: 'password123',
        first_name: 'New',
        last_name: 'User'
      });
      console.log('User created:', newUser);
      
      // Refresh users list
      refetchUsers();
      
      // Reset mutation state
      resetCreateUser();
    } catch (error) {
      console.error('Failed to create user:', error);
    }
    // Note: Error handling is automatic with the mutation hook
  };

  // Example: Check authentication status
  const isAuthenticated = apiService.isAuthenticated();
  const currentToken = apiService.getAuthToken();
  const tokenExpiry = apiService.getTokenExpiry();

  return (
    <Box sx={{ p: 3, maxWidth: 1200, margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom>
        API Service Example
      </Typography>
      
      <Grid container spacing={3}>
        {/* Authentication Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Authentication
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Status: {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
                </Typography>
                {currentToken && (
                  <Typography variant="body2" color="text.secondary">
                    Token: {currentToken.substring(0, 20)}...
                  </Typography>
                )}
                {tokenExpiry && (
                  <Typography variant="body2" color="text.secondary">
                    Expires: {new Date(tokenExpiry).toLocaleString()}
                  </Typography>
                )}
              </Box>

              <TextField
                fullWidth
                label="Email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                sx={{ mb: 2 }}
              />
              
              <Button 
                variant="contained" 
                onClick={handleLogin}
                disabled={!email || !password}
                sx={{ mb: 2 }}
              >
                Login
              </Button>
              
              {loginMessage && (
                <Alert severity={loginMessage.includes('successful') ? 'success' : 'error'}>
                  {loginMessage}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* API Operations Section */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                API Operations
              </Typography>
              
              <Button 
                variant="outlined" 
                onClick={handleFetchReports}
                disabled={isLoading()}
                sx={{ mb: 2, mr: 2 }}
              >
                {isLoading() ? <CircularProgress size={20} /> : 'Fetch Reports'}
              </Button>
              
              <Button 
                variant="outlined" 
                onClick={handleCreateUser}
                disabled={createUserLoading}
                sx={{ mb: 2 }}
              >
                {createUserLoading ? <CircularProgress size={20} /> : 'Create User'}
              </Button>

              {getCurrentError() && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {getCurrentError()?.message}
                  <Button size="small" onClick={clearError} sx={{ ml: 2 }}>
                    Clear
                  </Button>
                </Alert>
              )}

              {createUserError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {createUserError.message}
                  <Button size="small" onClick={resetCreateUser} sx={{ ml: 2 }}>
                    Clear
                  </Button>
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Users Data Section */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Users Data (using useApiData hook)
              </Typography>
              
              <Button 
                variant="outlined" 
                onClick={refetchUsers}
                disabled={usersLoading}
                sx={{ mb: 2 }}
              >
                {usersLoading ? <CircularProgress size={20} /> : 'Refresh Users'}
              </Button>

              {usersError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {usersError.message}
                </Alert>
              )}

              {usersLoading ? (
                <Box display="flex" justifyContent="center" p={3}>
                  <CircularProgress />
                </Box>
              ) : users ? (
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Total Users: {users.length}
                  </Typography>
                  {users.slice(0, 5).map((user) => (
                    <Box key={user.id} sx={{ mb: 1, p: 1, bgcolor: 'grey.100' }}>
                      <Typography variant="body2">
                        {user.first_name} {user.last_name} ({user.email})
                      </Typography>
                    </Box>
                  ))}
                  {users.length > 5 && (
                    <Typography variant="body2" color="text.secondary">
                      ... and {users.length - 5} more
                    </Typography>
                  )}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  No users loaded
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Configuration Section */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Service Configuration
              </Typography>
              
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  Base URL: {apiService.getBaseURL()}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Environment: {import.meta.env.MODE || 'development'}
                </Typography>
              </Box>

              <Button 
                variant="outlined" 
                onClick={() => apiService.setBaseURL('http://localhost:3000')}
                sx={{ mr: 2 }}
              >
                Change to Port 3000
              </Button>
              
              <Button 
                variant="outlined" 
                onClick={() => apiService.setBaseURL('http://localhost:5000')}
                sx={{ mr: 2 }}
              >
                Change to Port 5000
              </Button>
              
              <Button 
                variant="outlined" 
                onClick={() => apiService.setRequestTimeout(60000)}
              >
                Set 60s Timeout
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ApiServiceExample;
