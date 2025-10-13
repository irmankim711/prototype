import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Typography,
  Avatar,
  Grid,
  TextField,
  Button,
  Paper,
  Tabs,
  Tab,
  Divider,
  styled,
  CircularProgress,
  IconButton,
  Badge,
  Alert,
  Snackbar,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  LinearProgress,
  Chip,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  FormHelperText,
  InputAdornment,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  CloudUpload as UploadIcon,
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
  Cancel as CancelIcon,
  PhotoCamera as PhotoCameraIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  LockReset as LockResetIcon,
  Shield as ShieldIcon,
  Language as LanguageIcon,
  Palette as PaletteIcon,
  Schedule as ScheduleIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  ExpandMore as ExpandMoreIcon,
} from '@mui/icons-material';
import { formBuilderAPI } from '../services/formBuilder';
import {
  enhancedUserProfileSchema,
  validateField,
  sanitizeFormData,
  hasFormChanges
} from '../utils/userProfileValidation';

// Enhanced styled components
const ProfileHeader = styled(Box)(({ theme }) => ({
  position: 'relative',
  padding: '32px',
  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  borderRadius: '16px',
  marginBottom: '32px',
  color: 'white',
  boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)',
}));

const ProfileAvatar = styled(Avatar)(({ theme }) => ({
  width: 140,
  height: 140,
  border: '5px solid white',
  boxShadow: '0 8px 24px rgba(0, 0, 0, 0.15)',
  fontSize: '3rem',
  fontWeight: 600,
}));

const StyledCard = styled(Card)(({ theme }) => ({
  borderRadius: '16px',
  boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
  border: 'none',
  marginBottom: '24px',
}));

const StyledTextField = styled(TextField)(({ theme }) => ({
  '& .MuiOutlinedInput-root': {
    borderRadius: '12px',
    transition: 'all 0.2s ease-in-out',
    '&:hover': {
      transform: 'translateY(-1px)',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
    },
    '&.Mui-focused': {
      transform: 'translateY(-2px)',
      boxShadow: '0 6px 20px rgba(102, 126, 234, 0.25)',
    },
  },
  marginBottom: '20px',
}));

const ActionButton = styled(Button)(({ theme }) => ({
  borderRadius: '12px',
  padding: '12px 24px',
  textTransform: 'none',
  fontWeight: 600,
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
  transition: 'all 0.2s ease-in-out',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: '0 6px 20px rgba(0, 0, 0, 0.25)',
  },
}));

interface UserData {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  username: string;
  phone: string;
  company: string;
  job_title: string;
  bio: string;
  timezone: string;
  language: string;
  theme: string;
  email_notifications: boolean;
  push_notifications: boolean;
  role?: string;
  created_at: string;
  updated_at: string;
  avatar_url: string;
  is_verified?: boolean;
}

interface ValidationErrors {
  [key: string]: string;
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
      id={`profile-tabpanel-${index}`}
      aria-labelledby={`profile-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

const EnhancedUserProfile: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [editMode, setEditMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [validationErrors, setValidationErrors] = useState<ValidationErrors>({});
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showPasswordDialog, setShowPasswordDialog] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [userData, setUserData] = useState<UserData>({
    id: '',
    email: '',
    first_name: '',
    last_name: '',
    username: '',
    phone: '',
    company: '',
    job_title: '',
    bio: '',
    timezone: 'UTC',
    language: 'en',
    theme: 'light',
    email_notifications: true,
    push_notifications: false,
    role: '',
    created_at: '',
    updated_at: '',
    avatar_url: '',
  });

  const [originalData, setOriginalData] = useState<UserData>(userData);
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [notifications, setNotifications] = useState({
    success: '',
    error: '',
  });

  // Load user profile data
  const loadUserProfile = useCallback(async () => {
    try {
      setIsFetching(true);
      setNotifications({ success: '', error: '' });

      // Replace with your actual API call
      const response = await formBuilderAPI.getUserProfile();

      if (response.success) {
        const profile = response.user;
        const profileData: UserData = {
          id: profile.id || '',
          email: profile.email || '',
          first_name: profile.first_name || '',
          last_name: profile.last_name || '',
          username: profile.username || '',
          phone: profile.phone || '',
          company: profile.company || '',
          job_title: profile.job_title || '',
          bio: profile.bio || '',
          timezone: profile.timezone || 'UTC',
          language: profile.language || 'en',
          theme: profile.theme || 'light',
          email_notifications: profile.email_notifications !== false,
          push_notifications: profile.push_notifications === true,
          role: profile.role || '',
          created_at: profile.created_at || '',
          updated_at: profile.updated_at || '',
          avatar_url: profile.avatar_url || '',
          is_verified: profile.is_verified || false,
        };

        setUserData(profileData);
        setOriginalData(profileData);
      }
    } catch (error) {
      console.error('Error loading profile:', error);
      setNotifications({ success: '', error: 'Failed to load profile data' });
    } finally {
      setIsFetching(false);
    }
  }, []);

  useEffect(() => {
    loadUserProfile();
  }, [loadUserProfile]);

  // Real-time validation
  const validateFormData = useCallback((data: Partial<UserData>) => {
    const errors: ValidationErrors = {};

    Object.keys(data).forEach((field) => {
      const error = validateField(field, data[field as keyof UserData]);
      if (error) {
        errors[field] = error;
      }
    });

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, []);

  // Handle input changes with validation
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : value;

    setUserData(prev => ({
      ...prev,
      [name]: newValue,
    }));

    // Real-time validation for the changed field
    if (type !== 'checkbox') {
      const error = validateField(name, newValue);
      setValidationErrors(prev => ({
        ...prev,
        [name]: error || '',
      }));
    }
  };

  const handleSelectChange = (name: string, value: string) => {
    setUserData(prev => ({ ...prev, [name]: value }));

    const error = validateField(name, value);
    setValidationErrors(prev => ({
      ...prev,
      [name]: error || '',
    }));
  };

  // Handle profile image upload
  const handleImageUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file
    if (!file.type.startsWith('image/')) {
      setNotifications({ success: '', error: 'Please select a valid image file' });
      return;
    }

    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      setNotifications({ success: '', error: 'Image size must be less than 5MB' });
      return;
    }

    try {
      setUploadingImage(true);

      const formData = new FormData();
      formData.append('avatar', file);

      // Replace with your actual upload API
      const response = await formBuilderAPI.uploadAvatar(formData);

      if (response.success) {
        setUserData(prev => ({
          ...prev,
          avatar_url: response.avatar_url,
        }));
        setNotifications({ success: 'Profile image updated successfully', error: '' });
      }
    } catch (error) {
      console.error('Error uploading image:', error);
      setNotifications({ success: '', error: 'Failed to upload image' });
    } finally {
      setUploadingImage(false);
    }
  };

  // Handle profile save
  const handleSave = async () => {
    try {
      setIsLoading(true);
      setNotifications({ success: '', error: '' });

      // Validate all data
      const isValid = validateFormData(userData);
      if (!isValid) {
        setNotifications({ success: '', error: 'Please fix validation errors before saving' });
        return;
      }

      // Sanitize and prepare data
      const sanitizedData = sanitizeFormData(userData);

      // Replace with your actual API call
      const response = await formBuilderAPI.updateUserProfile(sanitizedData);

      if (response.success) {
        const updatedData = {
          ...userData,
          ...response.user,
          updated_at: response.user.updated_at || new Date().toISOString(),
        };

        setUserData(updatedData);
        setOriginalData(updatedData);
        setEditMode(false);
        setNotifications({ success: 'Profile updated successfully!', error: '' });
      }
    } catch (error: any) {
      console.error('Error updating profile:', error);
      setNotifications({
        success: '',
        error: error.response?.data?.message || 'Failed to update profile'
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Handle password change
  const handlePasswordChange = async () => {
    try {
      if (passwordData.newPassword !== passwordData.confirmPassword) {
        setNotifications({ success: '', error: 'New passwords do not match' });
        return;
      }

      if (passwordData.newPassword.length < 8) {
        setNotifications({ success: '', error: 'Password must be at least 8 characters long' });
        return;
      }

      setIsLoading(true);

      // Replace with your actual API call
      const response = await formBuilderAPI.changePassword({
        currentPassword: passwordData.currentPassword,
        newPassword: passwordData.newPassword,
      });

      if (response.success) {
        setPasswordData({ currentPassword: '', newPassword: '', confirmPassword: '' });
        setShowPasswordDialog(false);
        setNotifications({ success: 'Password changed successfully!', error: '' });
      }
    } catch (error: any) {
      console.error('Error changing password:', error);
      setNotifications({
        success: '',
        error: error.response?.data?.message || 'Failed to change password'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setUserData(originalData);
    setEditMode(false);
    setValidationErrors({});
    setNotifications({ success: '', error: '' });
  };

  const getDisplayName = () => {
    const firstName = userData.first_name.trim();
    const lastName = userData.last_name.trim();
    if (firstName && lastName) return `${firstName} ${lastName}`;
    if (firstName) return firstName;
    if (lastName) return lastName;
    return userData.email.split('@')[0] || 'User';
  };

  const getInitials = () => {
    const firstName = userData.first_name.trim();
    const lastName = userData.last_name.trim();
    if (firstName && lastName) return `${firstName[0]}${lastName[0]}`;
    if (firstName) return firstName[0];
    if (lastName) return lastName[0];
    return userData.email[0]?.toUpperCase() || 'U';
  };

  const hasChanges = hasFormChanges(originalData, userData);

  if (isFetching) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="50vh">
        <CircularProgress size={60} />
      </Box>
    );
  }

  return (
    <Box sx={{ padding: { xs: 2, sm: 3 }, maxWidth: 1200, margin: '0 auto' }}>
      {/* Header */}
      <Typography
        variant="h4"
        sx={{
          fontWeight: 700,
          marginBottom: 3,
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          backgroundClip: 'text',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
        }}
      >
        User Profile
      </Typography>

      {/* Profile Header */}
      <ProfileHeader>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={3} sx={{ textAlign: { xs: 'center', md: 'left' } }}>
            <Box sx={{ position: 'relative', display: 'inline-block' }}>
              <Badge
                overlap="circular"
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                badgeContent={
                  userData.is_verified ? (
                    <CheckCircleIcon sx={{ color: '#4caf50', fontSize: 24 }} />
                  ) : (
                    <WarningIcon sx={{ color: '#ff9800', fontSize: 24 }} />
                  )
                }
              >
                <ProfileAvatar src={userData.avatar_url} alt={getDisplayName()}>
                  {uploadingImage ? <CircularProgress /> : getInitials()}
                </ProfileAvatar>
              </Badge>

              <input
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                ref={fileInputRef}
                style={{ display: 'none' }}
              />

              <IconButton
                sx={{
                  position: 'absolute',
                  bottom: 8,
                  right: 8,
                  backgroundColor: 'rgba(255, 255, 255, 0.9)',
                  color: '#667eea',
                  width: 40,
                  height: 40,
                  '&:hover': {
                    backgroundColor: 'white',
                    transform: 'scale(1.1)',
                  },
                }}
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadingImage}
              >
                <PhotoCameraIcon />
              </IconButton>
            </Box>
          </Grid>

          <Grid item xs={12} md={7}>
            <Typography variant="h5" sx={{ fontWeight: 600, marginBottom: 1 }}>
              {getDisplayName()}
            </Typography>
            <Typography variant="subtitle1" sx={{ opacity: 0.9, marginBottom: 1 }}>
              {userData.role} {userData.company && `• ${userData.company}`}
            </Typography>
            <Typography variant="body2" sx={{ opacity: 0.8 }}>
              Member since {new Date(userData.created_at || Date.now()).toLocaleDateString()}
            </Typography>

            <Box sx={{ marginTop: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label={userData.is_verified ? 'Verified' : 'Unverified'}
                color={userData.is_verified ? 'success' : 'warning'}
                size="small"
                icon={userData.is_verified ? <CheckCircleIcon /> : <WarningIcon />}
              />
              <Chip label={userData.theme} size="small" />
              <Chip label={userData.language.toUpperCase()} size="small" />
            </Box>
          </Grid>

          <Grid item xs={12} md={2} sx={{ textAlign: { xs: 'center', md: 'right' } }}>
            <ActionButton
              variant="contained"
              onClick={() => setEditMode(!editMode)}
              disabled={isLoading}
              startIcon={editMode ? <CancelIcon /> : <EditIcon />}
              sx={{
                background: editMode
                  ? 'linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%)'
                  : 'linear-gradient(135deg, #4caf50 0%, #45a049 100%)',
              }}
            >
              {editMode ? 'Cancel' : 'Edit Profile'}
            </ActionButton>
          </Grid>
        </Grid>
      </ProfileHeader>

      {/* Notifications */}
      <Snackbar
        open={!!notifications.error}
        autoHideDuration={6000}
        onClose={() => setNotifications(prev => ({ ...prev, error: '' }))}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="error" onClose={() => setNotifications(prev => ({ ...prev, error: '' }))}>
          {notifications.error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!notifications.success}
        autoHideDuration={4000}
        onClose={() => setNotifications(prev => ({ ...prev, success: '' }))}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert severity="success" onClose={() => setNotifications(prev => ({ ...prev, success: '' }))}>
          {notifications.success}
        </Alert>
      </Snackbar>

      {/* Changes Indicator */}
      {editMode && hasChanges && (
        <Alert severity="info" sx={{ marginBottom: 2 }}>
          You have unsaved changes. Don't forget to save your profile!
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', marginBottom: 3 }}>
        <Tabs
          value={currentTab}
          onChange={(_, newValue) => setCurrentTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<PersonIcon />} label="Personal Info" iconPosition="start" />
          <Tab icon={<NotificationsIcon />} label="Notifications" iconPosition="start" />
          <Tab icon={<SecurityIcon />} label="Security" iconPosition="start" />
          <Tab icon={<SettingsIcon />} label="Preferences" iconPosition="start" />
        </Tabs>
      </Box>

      {/* Personal Information Tab */}
      <TabPanel value={currentTab} index={0}>
        <StyledCard>
          <CardContent sx={{ padding: 4 }}>
            <Typography variant="h6" sx={{ marginBottom: 3, fontWeight: 600 }}>
              Personal Information
            </Typography>
            <Divider sx={{ marginBottom: 3 }} />

            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <StyledTextField
                  fullWidth
                  label="First Name"
                  name="first_name"
                  value={userData.first_name}
                  onChange={handleInputChange}
                  disabled={!editMode}
                  error={!!validationErrors.first_name}
                  helperText={validationErrors.first_name}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <StyledTextField
                  fullWidth
                  label="Last Name"
                  name="last_name"
                  value={userData.last_name}
                  onChange={handleInputChange}
                  disabled={!editMode}
                  error={!!validationErrors.last_name}
                  helperText={validationErrors.last_name}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <StyledTextField
                  fullWidth
                  label="Username"
                  name="username"
                  value={userData.username}
                  onChange={handleInputChange}
                  disabled={!editMode}
                  error={!!validationErrors.username}
                  helperText={validationErrors.username}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <StyledTextField
                  fullWidth
                  label="Email Address"
                  name="email"
                  value={userData.email}
                  disabled={true}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        {userData.is_verified ? (
                          <CheckCircleIcon color="success" />
                        ) : (
                          <WarningIcon color="warning" />
                        )}
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <StyledTextField
                  fullWidth
                  label="Phone Number"
                  name="phone"
                  value={userData.phone}
                  onChange={handleInputChange}
                  disabled={!editMode}
                  error={!!validationErrors.phone}
                  helperText={validationErrors.phone}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <StyledTextField
                  fullWidth
                  label="Company"
                  name="company"
                  value={userData.company}
                  onChange={handleInputChange}
                  disabled={!editMode}
                  error={!!validationErrors.company}
                  helperText={validationErrors.company}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <StyledTextField
                  fullWidth
                  label="Job Title"
                  name="job_title"
                  value={userData.job_title}
                  onChange={handleInputChange}
                  disabled={!editMode}
                  error={!!validationErrors.job_title}
                  helperText={validationErrors.job_title}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth disabled={!editMode}>
                  <InputLabel>Timezone</InputLabel>
                  <Select
                    value={userData.timezone}
                    label="Timezone"
                    onChange={(e) => handleSelectChange('timezone', e.target.value)}
                  >
                    <MenuItem value="UTC">UTC</MenuItem>
                    <MenuItem value="America/New_York">Eastern Time (US)</MenuItem>
                    <MenuItem value="America/Chicago">Central Time (US)</MenuItem>
                    <MenuItem value="America/Denver">Mountain Time (US)</MenuItem>
                    <MenuItem value="America/Los_Angeles">Pacific Time (US)</MenuItem>
                    <MenuItem value="Europe/London">London</MenuItem>
                    <MenuItem value="Europe/Paris">Paris</MenuItem>
                    <MenuItem value="Asia/Tokyo">Tokyo</MenuItem>
                    <MenuItem value="Asia/Shanghai">Shanghai</MenuItem>
                    <MenuItem value="Asia/Kuala_Lumpur">Kuala Lumpur</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12}>
                <StyledTextField
                  fullWidth
                  label="Bio"
                  name="bio"
                  value={userData.bio}
                  onChange={handleInputChange}
                  disabled={!editMode}
                  multiline
                  rows={4}
                  error={!!validationErrors.bio}
                  helperText={validationErrors.bio || `${userData.bio.length}/500 characters`}
                />
              </Grid>
            </Grid>

            {editMode && (
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', marginTop: 3 }}>
                <ActionButton
                  variant="outlined"
                  onClick={handleCancel}
                  disabled={isLoading}
                  startIcon={<CancelIcon />}
                >
                  Cancel
                </ActionButton>
                <ActionButton
                  variant="contained"
                  onClick={handleSave}
                  disabled={isLoading || Object.keys(validationErrors).some(key => validationErrors[key])}
                  startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
                  sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
                >
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </ActionButton>
              </Box>
            )}
          </CardContent>
        </StyledCard>
      </TabPanel>

      {/* Notifications Tab */}
      <TabPanel value={currentTab} index={1}>
        <StyledCard>
          <CardContent sx={{ padding: 4 }}>
            <Typography variant="h6" sx={{ marginBottom: 3, fontWeight: 600 }}>
              Notification Preferences
            </Typography>
            <Divider sx={{ marginBottom: 3 }} />

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={userData.email_notifications}
                      onChange={handleInputChange}
                      name="email_notifications"
                      disabled={!editMode}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body1">Email Notifications</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Receive updates and alerts via email
                      </Typography>
                    </Box>
                  }
                />
              </Grid>

              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={userData.push_notifications}
                      onChange={handleInputChange}
                      name="push_notifications"
                      disabled={!editMode}
                    />
                  }
                  label={
                    <Box>
                      <Typography variant="body1">Push Notifications</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Receive browser notifications for important updates
                      </Typography>
                    </Box>
                  }
                />
              </Grid>
            </Grid>

            {editMode && (
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', marginTop: 3 }}>
                <ActionButton
                  variant="outlined"
                  onClick={handleCancel}
                  disabled={isLoading}
                  startIcon={<CancelIcon />}
                >
                  Cancel
                </ActionButton>
                <ActionButton
                  variant="contained"
                  onClick={handleSave}
                  disabled={isLoading}
                  startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
                  sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
                >
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </ActionButton>
              </Box>
            )}
          </CardContent>
        </StyledCard>
      </TabPanel>

      {/* Security Tab */}
      <TabPanel value={currentTab} index={2}>
        <StyledCard>
          <CardContent sx={{ padding: 4 }}>
            <Typography variant="h6" sx={{ marginBottom: 3, fontWeight: 600 }}>
              Security Settings
            </Typography>
            <Divider sx={{ marginBottom: 3 }} />

            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card variant="outlined" sx={{ padding: 2 }}>
                  <Typography variant="subtitle1" sx={{ marginBottom: 1, fontWeight: 600 }}>
                    Password
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ marginBottom: 2 }}>
                    Last updated: {userData.updated_at ? new Date(userData.updated_at).toLocaleDateString() : 'Never'}
                  </Typography>
                  <ActionButton
                    variant="outlined"
                    startIcon={<LockResetIcon />}
                    onClick={() => setShowPasswordDialog(true)}
                  >
                    Change Password
                  </ActionButton>
                </Card>
              </Grid>

              <Grid item xs={12}>
                <Card variant="outlined" sx={{ padding: 2 }}>
                  <Typography variant="subtitle1" sx={{ marginBottom: 1, fontWeight: 600 }}>
                    Account Security
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ marginBottom: 2 }}>
                    Manage your account security and data
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <ActionButton
                      variant="outlined"
                      startIcon={<ShieldIcon />}
                      onClick={() => {/* Two-factor authentication setup */}}
                    >
                      Enable 2FA
                    </ActionButton>
                    <ActionButton
                      variant="outlined"
                      color="error"
                      startIcon={<DeleteIcon />}
                      onClick={() => setShowDeleteDialog(true)}
                    >
                      Delete Account
                    </ActionButton>
                  </Box>
                </Card>
              </Grid>
            </Grid>
          </CardContent>
        </StyledCard>
      </TabPanel>

      {/* Preferences Tab */}
      <TabPanel value={currentTab} index={3}>
        <StyledCard>
          <CardContent sx={{ padding: 4 }}>
            <Typography variant="h6" sx={{ marginBottom: 3, fontWeight: 600 }}>
              Application Preferences
            </Typography>
            <Divider sx={{ marginBottom: 3 }} />

            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth disabled={!editMode}>
                  <InputLabel>Language</InputLabel>
                  <Select
                    value={userData.language}
                    label="Language"
                    onChange={(e) => handleSelectChange('language', e.target.value)}
                    startAdornment={<LanguageIcon sx={{ marginRight: 1 }} />}
                  >
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="ms">Bahasa Malaysia</MenuItem>
                    <MenuItem value="zh">中文</MenuItem>
                    <MenuItem value="ta">தமிழ்</MenuItem>
                  </Select>
                </FormControl>
              </Grid>

              <Grid item xs={12} sm={6}>
                <FormControl fullWidth disabled={!editMode}>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={userData.theme}
                    label="Theme"
                    onChange={(e) => handleSelectChange('theme', e.target.value)}
                    startAdornment={<PaletteIcon sx={{ marginRight: 1 }} />}
                  >
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="auto">Auto</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            {editMode && (
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', marginTop: 3 }}>
                <ActionButton
                  variant="outlined"
                  onClick={handleCancel}
                  disabled={isLoading}
                  startIcon={<CancelIcon />}
                >
                  Cancel
                </ActionButton>
                <ActionButton
                  variant="contained"
                  onClick={handleSave}
                  disabled={isLoading}
                  startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
                  sx={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
                >
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </ActionButton>
              </Box>
            )}
          </CardContent>
        </StyledCard>
      </TabPanel>

      {/* Password Change Dialog */}
      <Dialog open={showPasswordDialog} onClose={() => setShowPasswordDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Change Password</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ marginTop: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Current Password"
                type={showPassword ? 'text' : 'password'}
                value={passwordData.currentPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, currentPassword: e.target.value }))}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton onClick={() => setShowPassword(!showPassword)}>
                        {showPassword ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="New Password"
                type={showPassword ? 'text' : 'password'}
                value={passwordData.newPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, newPassword: e.target.value }))}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Confirm New Password"
                type={showPassword ? 'text' : 'password'}
                value={passwordData.confirmPassword}
                onChange={(e) => setPasswordData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                error={passwordData.newPassword !== passwordData.confirmPassword && passwordData.confirmPassword !== ''}
                helperText={passwordData.newPassword !== passwordData.confirmPassword && passwordData.confirmPassword !== '' ? 'Passwords do not match' : ''}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowPasswordDialog(false)}>Cancel</Button>
          <ActionButton
            onClick={handlePasswordChange}
            disabled={isLoading || !passwordData.currentPassword || !passwordData.newPassword || passwordData.newPassword !== passwordData.confirmPassword}
            startIcon={isLoading ? <CircularProgress size={20} /> : <SaveIcon />}
          >
            {isLoading ? 'Changing...' : 'Change Password'}
          </ActionButton>
        </DialogActions>
      </Dialog>

      {/* Delete Account Dialog */}
      <Dialog open={showDeleteDialog} onClose={() => setShowDeleteDialog(false)}>
        <DialogTitle color="error">Delete Account</DialogTitle>
        <DialogContent>
          <Alert severity="error" sx={{ marginBottom: 2 }}>
            This action cannot be undone. All your data will be permanently deleted.
          </Alert>
          <Typography>
            Are you sure you want to delete your account? Type "DELETE" to confirm.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
          <Button color="error" variant="contained">
            Delete Account
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EnhancedUserProfile;