import { useState } from 'react';
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
  Badge
} from '@mui/material';
import {
  Edit as EditIcon,
  Save as SaveIcon,
  CloudUpload as UploadIcon,
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
} from '@mui/icons-material';

// Styled components
const ProfileHeader = styled(Box)(() => ({
  position: 'relative',
  padding: '24px',
  backgroundColor: '#f8fafc',
  borderRadius: '12px',
  marginBottom: '24px',
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
}));

const ProfileAvatar = styled(Avatar)(() => ({
  width: 120,
  height: 120,
  border: '4px solid white',
  boxShadow: '0 4px 15px rgba(0, 0, 0, 0.1)',
}));

const EditButton = styled(IconButton)(() => ({
  position: 'absolute',
  right: 24,
  top: 24,
  backgroundColor: 'rgba(74, 105, 221, 0.1)',
  color: '#4a69dd',
  transition: 'all 0.2s ease',
  '&:hover': {
    backgroundColor: 'rgba(74, 105, 221, 0.2)',
  },
}));

const StyledTab = styled(Tab)(() => ({
  textTransform: 'none',
  fontWeight: 500,
  fontSize: '0.95rem',
  fontFamily: '"Poppins", sans-serif',
  color: '#64748b',
  '&.Mui-selected': {
    color: '#4a69dd',
  },
}));

const StyledTabs = styled(Tabs)(() => ({
  '& .MuiTabs-indicator': {
    backgroundColor: '#4a69dd',
    height: 3,
    borderRadius: '3px',
  },
}));

const SectionTitle = styled(Typography)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 600,
  fontSize: '1.1rem',
  color: '#0e1c40',
  marginBottom: '16px',
}));

const StyledButton = styled(Button)(() => ({
  borderRadius: '8px',
  boxShadow: '0 4px 10px rgba(74, 105, 221, 0.2)',
  textTransform: 'none',
  fontWeight: 500,
  padding: '8px 16px',
  background: 'linear-gradient(90deg, #4a69dd, #3a59cd)',
  color: 'white',
  '&:hover': {
    background: 'linear-gradient(90deg, #3a59cd, #2a49bd)',
    boxShadow: '0 6px 12px rgba(74, 105, 221, 0.3)',
  },
}));

const StyledPaper = styled(Paper)(() => ({
  padding: '24px',
  borderRadius: '12px',
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.05)',
  border: 'none',
}));

const StyledTextField = styled(TextField)(() => ({
  '.MuiOutlinedInput-root': {
    borderRadius: '8px',
  },
  marginBottom: '20px',
}));

const StyledBadge = styled(Badge)(() => ({
  '& .MuiBadge-badge': {
    backgroundColor: '#37cfab',
    color: 'white',
    boxShadow: '0 0 0 2px white',
    '&::after': {
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      borderRadius: '50%',
      border: '1px solid currentColor',
      content: '""',
    },
  },
}));

// Tab panel component
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
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function UserProfile() {
  const [value, setValue] = useState(0);
  const [editMode, setEditMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [userData, setUserData] = useState({
    name: 'John Doe',
    email: 'john.doe@example.com',
    role: 'Administrator',
    phone: '+60 12 345 6789',
    department: 'IT Department',
    joinDate: '2023-05-01',
    bio: 'Experienced administrator with focus on data analytics and reporting solutions.',
  });

  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const handleSave = () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
      setEditMode(false);
    }, 1000);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setUserData(prev => ({ ...prev, [name]: value }));
  };

  const handleUploadClick = () => {
    // This would trigger file upload in a real implementation
    console.log('Upload profile picture');
  };

  return (
    <Box sx={{ padding: { xs: '16px', sm: '24px' } }}>
      <Typography
        variant="h5"
        sx={{
          fontFamily: '"Poppins", sans-serif',
          fontWeight: 700,
          fontSize: '1.75rem',
          color: '#0e1c40',
          marginBottom: '1.5rem',
          position: 'relative',
          paddingBottom: '0.75rem',
          '&:after': {
            content: '""',
            position: 'absolute',
            bottom: 0,
            left: 0,
            width: '60px',
            height: '4px',
            background: 'linear-gradient(90deg, #4a69dd, #37cfab)',
            borderRadius: '2px',
          },
        }}
      >
        User Profile
      </Typography>

      <ProfileHeader>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={2} sx={{ textAlign: { xs: 'center', md: 'center' }, mb: { xs: 2, md: 0 } }}>
            <Box sx={{ position: 'relative', display: 'inline-block' }}>
              <StyledBadge
                overlap="circular"
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
                variant="dot"
              >
                <ProfileAvatar alt={userData.name} src="/path/to/profile-pic.jpg">
                  {userData.name.split(' ').map(n => n[0]).join('')}
                </ProfileAvatar>
              </StyledBadge>
              <IconButton
                sx={{
                  position: 'absolute',
                  bottom: 0,
                  right: 0,
                  backgroundColor: '#4a69dd',
                  color: 'white',
                  width: 32,
                  height: 32,
                  '&:hover': {
                    backgroundColor: '#3a59cd',
                  },
                }}
                onClick={handleUploadClick}
              >
                <UploadIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Box>
          </Grid>
          <Grid item xs={12} md={8}>
            <Typography variant="h5" sx={{ fontWeight: 600, mb: 1, color: '#0e1c40' }}>
              {userData.name}
            </Typography>
            <Typography variant="body1" sx={{ color: '#64748b', mb: 1 }}>
              {userData.role} • {userData.department}
            </Typography>
            <Typography variant="body2" sx={{ color: '#94a3b8' }}>
              Member since {new Date(userData.joinDate).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </Typography>
          </Grid>
          <Grid item xs={12} md={2} sx={{ textAlign: 'right' }}>
            <EditButton
              aria-label="edit profile"
              onClick={() => setEditMode(!editMode)}
              disabled={isLoading}
            >
              {editMode ? <SaveIcon /> : <EditIcon />}
            </EditButton>
          </Grid>
        </Grid>
      </ProfileHeader>

      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <StyledTabs value={value} onChange={handleChange} aria-label="profile tabs">
          <StyledTab icon={<PersonIcon sx={{ fontSize: 20 }} />} iconPosition="start" label="Personal Info" />
          <StyledTab icon={<NotificationsIcon sx={{ fontSize: 20 }} />} iconPosition="start" label="Notifications" />
          <StyledTab icon={<SecurityIcon sx={{ fontSize: 20 }} />} iconPosition="start" label="Security" />
          <StyledTab icon={<SettingsIcon sx={{ fontSize: 20 }} />} iconPosition="start" label="Settings" />
        </StyledTabs>
      </Box>

      <TabPanel value={value} index={0}>
        <StyledPaper>
          <SectionTitle>Personal Information</SectionTitle>
          <Divider sx={{ mb: 3 }} />
          
          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <StyledTextField
                fullWidth
                label="Full Name"
                name="name"
                value={userData.name}
                onChange={handleInputChange}
                disabled={!editMode}
                variant="outlined"
                autoComplete="name"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StyledTextField
                fullWidth
                label="Email Address"
                name="email"
                value={userData.email}
                onChange={handleInputChange}
                disabled={!editMode}
                variant="outlined"
                autoComplete="email"
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
                variant="outlined"
                autoComplete="tel"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StyledTextField
                fullWidth
                label="Department"
                name="department"
                value={userData.department}
                onChange={handleInputChange}
                disabled={!editMode}
                variant="outlined"
                autoComplete="organization"
              />
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
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} sx={{ textAlign: 'right' }}>
              {editMode && (
                <StyledButton
                  variant="contained"
                  startIcon={isLoading ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
                  onClick={handleSave}
                  disabled={isLoading}
                >
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </StyledButton>
              )}
            </Grid>
          </Grid>
        </StyledPaper>
      </TabPanel>

      <TabPanel value={value} index={1}>
        <StyledPaper>
          <SectionTitle>Notification Preferences</SectionTitle>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="body1" color="text.secondary">
            Configure your notification settings here.
          </Typography>
          {/* Notification settings would go here */}
        </StyledPaper>
      </TabPanel>

      <TabPanel value={value} index={2}>
        <StyledPaper>
          <SectionTitle>Security Settings</SectionTitle>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="body1" color="text.secondary">
            Manage your account security and password here.
          </Typography>
          {/* Security settings would go here */}
        </StyledPaper>
      </TabPanel>

      <TabPanel value={value} index={3}>
        <StyledPaper>
          <SectionTitle>Account Settings</SectionTitle>
          <Divider sx={{ mb: 3 }} />
          <Typography variant="body1" color="text.secondary">
            Configure your account preferences and settings.
          </Typography>
          {/* Account settings would go here */}
        </StyledPaper>
      </TabPanel>
    </Box>
  );
}
