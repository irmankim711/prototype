import React from "react";
import { useState, useEffect, useCallback } from "react";
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
} from "@mui/material";
import {
  Edit as EditIcon,
  Save as SaveIcon,
  CloudUpload as UploadIcon,
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  Settings as SettingsIcon,
  Person as PersonIcon,
  Cancel as CancelIcon,
} from "@mui/icons-material";
import { fetchUserProfile, updateUserProfile } from "../../services/api";
import { useUser } from "../../hooks/useUser";

// Styled components
const ProfileHeader = styled(Box)(() => ({
  position: "relative",
  padding: "24px",
  backgroundColor: "#f8fafc",
  borderRadius: "12px",
  marginBottom: "24px",
  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
}));

const ProfileAvatar = styled(Avatar)(() => ({
  width: 120,
  height: 120,
  border: "4px solid white",
  boxShadow: "0 4px 15px rgba(0, 0, 0, 0.1)",
}));

const EditButton = styled(IconButton)(() => ({
  position: "absolute",
  right: 24,
  top: 24,
  backgroundColor: "rgba(74, 105, 221, 0.1)",
  color: "#4a69dd",
  transition: "all 0.2s ease",
  "&:hover": {
    backgroundColor: "rgba(74, 105, 221, 0.2)",
  },
}));

const StyledTab = styled(Tab)(() => ({
  textTransform: "none",
  fontWeight: 500,
  fontSize: "0.95rem",
  fontFamily: '"Poppins", sans-serif',
  color: "#64748b",
  "&.Mui-selected": {
    color: "#4a69dd",
  },
}));

const StyledTabs = styled(Tabs)(() => ({
  "& .MuiTabs-indicator": {
    backgroundColor: "#4a69dd",
    height: 3,
    borderRadius: "3px",
  },
}));

const SectionTitle = styled(Typography)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 600,
  fontSize: "1.1rem",
  color: "#0e1c40",
  marginBottom: "16px",
}));

const StyledButton = styled(Button)(() => ({
  borderRadius: "8px",
  boxShadow: "0 4px 10px rgba(74, 105, 221, 0.2)",
  textTransform: "none",
  fontWeight: 500,
  padding: "8px 16px",
  background: "linear-gradient(90deg, #4a69dd, #3a59cd)",
  color: "white",
  "&:hover": {
    background: "linear-gradient(90deg, #3a59cd, #2a49bd)",
    boxShadow: "0 6px 12px rgba(74, 105, 221, 0.3)",
  },
}));

const StyledPaper = styled(Paper)(() => ({
  padding: "24px",
  borderRadius: "12px",
  boxShadow: "0 4px 12px rgba(0, 0, 0, 0.05)",
  border: "none",
}));

const StyledTextField = styled(TextField)(() => ({
  ".MuiOutlinedInput-root": {
    borderRadius: "8px",
  },
  marginBottom: "20px",
}));

const StyledBadge = styled(Badge)(() => ({
  "& .MuiBadge-badge": {
    backgroundColor: "#37cfab",
    color: "white",
    boxShadow: "0 0 0 2px white",
    "&::after": {
      position: "absolute",
      top: 0,
      left: 0,
      width: "100%",
      height: "100%",
      borderRadius: "50%",
      border: "1px solid currentColor",
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
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export default function UserProfile() {
  const [value, setValue] = useState(0);
  const [editMode, setEditMode] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const { currentUser, updateUserData, refreshUserData } = useUser();
  const [userData, setUserData] = useState({
    id: "",
    email: "",
    first_name: "",
    last_name: "",
    username: "",
    phone: "",
    company: "",
    job_title: "",
    bio: "",
    timezone: "UTC",
    language: "en",
    theme: "light",
    email_notifications: true,
    push_notifications: false,
    role: "",
    created_at: "",
    updated_at: "",
    avatar_url: "",
  });
  const [originalData, setOriginalData] = useState(userData);

  const loadUserProfile = useCallback(async () => {
    try {
      setIsFetching(true);
      setError(null);

      // Use centralized user data refresh
      await refreshUserData();

      // Get profile data from centralized context
      if (currentUser) {
        const profileData = {
          id: currentUser.id || "",
          email: currentUser.email || "",
          first_name: currentUser.first_name || "",
          last_name: currentUser.last_name || "",
          username: currentUser.username || "",
          phone: currentUser.phone || "",
          company: currentUser.company || "",
          job_title: currentUser.job_title || "",
          bio: currentUser.bio || "",
          timezone: currentUser.timezone || "UTC",
          language: currentUser.language || "en",
          theme: currentUser.theme || "light",
          email_notifications: currentUser.email_notifications !== false,
          push_notifications: currentUser.push_notifications === true,
          role: currentUser.role || "",
          created_at: currentUser.created_at || "",
          updated_at: currentUser.updated_at || "",
          avatar_url: currentUser.avatar_url || "",
        };
        setUserData(profileData);
        setOriginalData(profileData);
      } else {
        // Fallback to direct API call if currentUser is not available
        const profile = await fetchUserProfile();
        const profileData = {
          id: profile.id || "",
          email: profile.email || "",
          first_name: profile.first_name || "",
          last_name: profile.last_name || "",
          username: profile.username || "",
          phone: profile.phone || "",
          company: profile.company || "",
          job_title: profile.job_title || "",
          bio: profile.bio || "",
          timezone: profile.timezone || "UTC",
          language: profile.language || "en",
          theme: profile.theme || "light",
          email_notifications: profile.email_notifications !== false,
          push_notifications: profile.push_notifications === true,
          role: profile.role || "",
          created_at: profile.created_at || "",
          updated_at: profile.updated_at || "",
          avatar_url: profile.avatar_url || "",
        };
        setUserData(profileData);
        setOriginalData(profileData);
      }
    } catch (err) {
      setError("Failed to load profile data");
      console.error("Error loading profile:", err);
    } finally {
      setIsFetching(false);
    }
  }, [currentUser, refreshUserData]);

  useEffect(() => {
    loadUserProfile();
  }, [loadUserProfile]);

  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Validate required fields
      if (!userData.first_name.trim() && !userData.last_name.trim()) {
        setError("Please provide at least a first name or last name");
        return;
      }

      const updateData = {
        first_name: userData.first_name.trim(),
        last_name: userData.last_name.trim(),
        username: userData.username.trim(),
        phone: userData.phone.trim(),
        company: userData.company.trim(),
        job_title: userData.job_title.trim(),
        bio: userData.bio.trim(),
        timezone: userData.timezone,
        language: userData.language,
        theme: userData.theme,
        email_notifications: userData.email_notifications,
        push_notifications: userData.push_notifications,
      };

      // Use centralized user data management
      const response = await updateUserData(updateData);

      // Update local state with the response
      const updatedData = {
        ...userData,
        ...response.user,
        updated_at: response.user.updated_at || new Date().toISOString(),
      };

      setUserData(updatedData);
      setOriginalData(updatedData);
      setEditMode(false);
      setSuccess("Profile updated successfully!");
    } catch (err: unknown) {
      let errorMessage = "Failed to update profile";

      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === "object" && err !== null && "response" in err) {
        const response = (err as { response?: { data?: { error?: string } } })
          .response;
        errorMessage = response?.data?.error || "Failed to update profile";
      }

      setError(errorMessage);
      console.error("Error updating profile:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setUserData(originalData);
    setEditMode(false);
    setError(null);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setUserData((prev: any) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setUserData((prev: any) => ({ ...prev, [name]: value }));
  };

  const handleUploadClick = () => {
    // This would trigger file upload in a real implementation
    console.log("Upload profile picture");
  };

  const getDisplayName = () => {
    const firstName = userData.first_name.trim();
    const lastName = userData.last_name.trim();
    if (firstName && lastName) return `${firstName} ${lastName}`;
    if (firstName) return firstName;
    if (lastName) return lastName;
    return userData.email.split("@")[0] || "User";
  };

  const getInitials = () => {
    const firstName = userData.first_name.trim();
    const lastName = userData.last_name.trim();
    if (firstName && lastName) return `${firstName[0]}${lastName[0]}`;
    if (firstName) return firstName[0];
    if (lastName) return lastName[0];
    return userData.email[0]?.toUpperCase() || "U";
  };

  if (isFetching) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          height: "50vh",
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ padding: { xs: "16px", sm: "24px" } }}>
      <Typography
        variant="h5"
        sx={{
          fontFamily: '"Poppins", sans-serif',
          fontWeight: 700,
          fontSize: "1.75rem",
          color: "#0e1c40",
          marginBottom: "1.5rem",
          position: "relative",
          paddingBottom: "0.75rem",
          "&:after": {
            content: '""',
            position: "absolute",
            bottom: 0,
            left: 0,
            width: "60px",
            height: "4px",
            background: "linear-gradient(90deg, #4a69dd, #37cfab)",
            borderRadius: "2px",
          },
        }}
      >
        User Profile
      </Typography>

      <ProfileHeader>
        <Grid container spacing={3} alignItems="center">
          <Grid
            item
            xs={12}
            md={2}
            sx={{
              textAlign: { xs: "center", md: "center" },
              mb: { xs: 2, md: 0 },
            }}
          >
            <Box sx={{ position: "relative", display: "inline-block" }}>
              <StyledBadge
                overlap="circular"
                anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
                variant="dot"
              >
                <ProfileAvatar alt={getDisplayName()} src={userData.avatar_url}>
                  {getInitials()}
                </ProfileAvatar>
              </StyledBadge>
              <IconButton
                sx={{
                  position: "absolute",
                  bottom: 0,
                  right: 0,
                  backgroundColor: "#4a69dd",
                  color: "white",
                  width: 32,
                  height: 32,
                  "&:hover": {
                    backgroundColor: "#3a59cd",
                  },
                }}
                onClick={handleUploadClick}
              >
                <UploadIcon sx={{ fontSize: 18 }} />
              </IconButton>
            </Box>
          </Grid>
          <Grid item xs={12} md={8}>
            <Typography
              variant="h5"
              sx={{ fontWeight: 600, mb: 1, color: "#0e1c40" }}
            >
              {getDisplayName()}
            </Typography>
            <Typography variant="body1" sx={{ color: "#64748b", mb: 1 }}>
              {userData.role} {userData.company && `• ${userData.company}`}
            </Typography>
            <Typography variant="body2" sx={{ color: "#94a3b8" }}>
              {userData.created_at &&
                `Member since ${new Date(
                  userData.created_at
                ).toLocaleDateString("en-US", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}`}
            </Typography>
          </Grid>
          <Grid item xs={12} md={2} sx={{ textAlign: "right" }}>
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

      {/* Error and Success Messages */}
      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
        anchorOrigin={{ vertical: "top", horizontal: "center" }}
      >
        <Alert
          onClose={() => setError(null)}
          severity="error"
          sx={{ width: "100%" }}
        >
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={4000}
        onClose={() => setSuccess(null)}
        anchorOrigin={{ vertical: "top", horizontal: "center" }}
      >
        <Alert
          onClose={() => setSuccess(null)}
          severity="success"
          sx={{ width: "100%" }}
        >
          {success}
        </Alert>
      </Snackbar>

      <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
        <StyledTabs
          value={value}
          onChange={handleChange}
          aria-label="profile tabs"
        >
          <StyledTab
            icon={<PersonIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            label="Personal Info"
          />
          <StyledTab
            icon={<NotificationsIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            label="Notifications"
          />
          <StyledTab
            icon={<SecurityIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            label="Security"
          />
          <StyledTab
            icon={<SettingsIcon sx={{ fontSize: 20 }} />}
            iconPosition="start"
            label="Preferences"
          />
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
                label="First Name"
                name="first_name"
                value={userData.first_name}
                onChange={handleInputChange}
                disabled={!editMode}
                variant="outlined"
                autoComplete="given-name"
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
                variant="outlined"
                autoComplete="family-name"
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
                variant="outlined"
                autoComplete="username"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <StyledTextField
                fullWidth
                label="Email Address"
                name="email"
                value={userData.email}
                onChange={handleInputChange}
                disabled={true} // Email should not be editable
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
                label="Company"
                name="company"
                value={userData.company}
                onChange={handleInputChange}
                disabled={!editMode}
                variant="outlined"
                autoComplete="organization"
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
                variant="outlined"
                autoComplete="organization-title"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={!editMode}>
                <InputLabel>Timezone</InputLabel>
                <Select
                  value={userData.timezone}
                  label="Timezone"
                  onChange={(e: any) =>
                    handleSelectChange("timezone", e.target.value)
                  }
                >
                  <MenuItem value="UTC">UTC</MenuItem>
                  <MenuItem value="America/New_York">
                    Eastern Time (US)
                  </MenuItem>
                  <MenuItem value="America/Chicago">Central Time (US)</MenuItem>
                  <MenuItem value="America/Denver">Mountain Time (US)</MenuItem>
                  <MenuItem value="America/Los_Angeles">
                    Pacific Time (US)
                  </MenuItem>
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
                variant="outlined"
              />
            </Grid>
            <Grid item xs={12} sx={{ textAlign: "right" }}>
              {editMode && (
                <Box
                  sx={{ display: "flex", gap: 2, justifyContent: "flex-end" }}
                >
                  <Button
                    variant="outlined"
                    startIcon={<CancelIcon />}
                    onClick={handleCancel}
                    disabled={isLoading}
                  >
                    Cancel
                  </Button>
                  <StyledButton
                    variant="contained"
                    startIcon={
                      isLoading ? (
                        <CircularProgress size={20} color="inherit" />
                      ) : (
                        <SaveIcon />
                      )
                    }
                    onClick={handleSave}
                    disabled={isLoading}
                  >
                    {isLoading ? "Saving..." : "Save Changes"}
                  </StyledButton>
                </Box>
              )}
            </Grid>
          </Grid>
        </StyledPaper>
      </TabPanel>

      <TabPanel value={value} index={1}>
        <StyledPaper>
          <SectionTitle>Notification Preferences</SectionTitle>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Configure how you want to receive notifications about your
                account activity.
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={userData.email_notifications}
                    onChange={handleInputChange}
                    name="email_notifications"
                    disabled={!editMode}
                  />
                }
                label="Email Notifications"
              />
              <Typography
                variant="caption"
                color="text.secondary"
                display="block"
              >
                Receive notifications via email
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControlLabel
                control={
                  <Switch
                    checked={userData.push_notifications}
                    onChange={handleInputChange}
                    name="push_notifications"
                    disabled={!editMode}
                  />
                }
                label="Push Notifications"
              />
              <Typography
                variant="caption"
                color="text.secondary"
                display="block"
              >
                Receive browser notifications
              </Typography>
            </Grid>

            <Grid item xs={12} sx={{ textAlign: "right" }}>
              {editMode && (
                <Box
                  sx={{ display: "flex", gap: 2, justifyContent: "flex-end" }}
                >
                  <Button
                    variant="outlined"
                    startIcon={<CancelIcon />}
                    onClick={handleCancel}
                    disabled={isLoading}
                  >
                    Cancel
                  </Button>
                  <StyledButton
                    variant="contained"
                    startIcon={
                      isLoading ? (
                        <CircularProgress size={20} color="inherit" />
                      ) : (
                        <SaveIcon />
                      )
                    }
                    onClick={handleSave}
                    disabled={isLoading}
                  >
                    {isLoading ? "Saving..." : "Save Changes"}
                  </StyledButton>
                </Box>
              )}
            </Grid>
          </Grid>
        </StyledPaper>
      </TabPanel>

      <TabPanel value={value} index={2}>
        <StyledPaper>
          <SectionTitle>Security Settings</SectionTitle>
          <Divider sx={{ mb: 3 }} />
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Manage your account security and password here.
              </Typography>
            </Grid>

            <Grid item xs={12}>
              <Button
                variant="outlined"
                onClick={() => {
                  // In a real implementation, this would open a password change dialog
                  console.log("Open password change dialog");
                }}
              >
                Change Password
              </Button>
            </Grid>
          </Grid>
        </StyledPaper>
      </TabPanel>

      <TabPanel value={value} index={3}>
        <StyledPaper>
          <SectionTitle>Preferences</SectionTitle>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
                Configure your account preferences and display settings.
              </Typography>
            </Grid>

            <Grid item xs={12} sm={6}>
              <FormControl fullWidth disabled={!editMode}>
                <InputLabel>Language</InputLabel>
                <Select
                  value={userData.language}
                  label="Language"
                  onChange={(e: any) =>
                    handleSelectChange("language", e.target.value)
                  }
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
                  onChange={(e: any) =>
                    handleSelectChange("theme", e.target.value)
                  }
                >
                  <MenuItem value="light">Light</MenuItem>
                  <MenuItem value="dark">Dark</MenuItem>
                  <MenuItem value="auto">Auto</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} sx={{ textAlign: "right" }}>
              {editMode && (
                <Box
                  sx={{ display: "flex", gap: 2, justifyContent: "flex-end" }}
                >
                  <Button
                    variant="outlined"
                    startIcon={<CancelIcon />}
                    onClick={handleCancel}
                    disabled={isLoading}
                  >
                    Cancel
                  </Button>
                  <StyledButton
                    variant="contained"
                    startIcon={
                      isLoading ? (
                        <CircularProgress size={20} color="inherit" />
                      ) : (
                        <SaveIcon />
                      )
                    }
                    onClick={handleSave}
                    disabled={isLoading}
                  >
                    {isLoading ? "Saving..." : "Save Changes"}
                  </StyledButton>
                </Box>
              )}
            </Grid>
          </Grid>
        </StyledPaper>
      </TabPanel>
    </Box>
  );
}
