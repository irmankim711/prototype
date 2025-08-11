import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Avatar,
  Grid,
  Button,
  Paper,
  Tabs,
  Tab,
  Divider,
  styled,
  CircularProgress,
  IconButton,
  Alert,
  Snackbar,
  Fade,
  Chip,
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
import { useUserProfileForm } from "../../hooks/useUserProfileForm";
import { useUser } from "../../hooks/useUser";
import {
  EnhancedFormField,
  EnhancedSelectField,
  EnhancedSwitchField,
} from "../../components/EnhancedFormFields";
import type { EnhancedUserProfileData } from "../../utils/userProfileValidation";

// Styled components (keeping the existing styles)
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
}));

const StyledPaper = styled(Paper)(() => ({
  padding: "24px",
  borderRadius: "12px",
  boxShadow: "0 4px 15px rgba(0, 0, 0, 0.05)",
  border: "1px solid rgba(74, 105, 221, 0.1)",
}));

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
      id={`user-profile-tabpanel-${index}`}
      aria-labelledby={`user-profile-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export default function EnhancedUserProfile() {
  const [value, setValue] = useState(0);
  const [editMode, setEditMode] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [originalData, setOriginalData] =
    useState<EnhancedUserProfileData | null>(null);
  const { currentUser, updateUserData, refreshUserData } = useUser();

  // Initialize the enhanced form
  const [formState, formActions] = useUserProfileForm({
    validateOnChange: true,
    onSubmit: handleProfileUpdate,
    onCancel: handleCancel,
  });

  useEffect(() => {
    const loadData = async () => {
      try {
        setIsFetching(true);
        setError(null);

        // Use centralized user data refresh
        await refreshUserData();

        // Get profile data from centralized context
        if (currentUser) {
          const profileData: EnhancedUserProfileData = {
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
          };

          setOriginalData(profileData);
          formActions.reset(profileData);
        } else {
          // Fallback to direct API call if currentUser is not available
          const profile = await fetchUserProfile();

          const profileData: EnhancedUserProfileData = {
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
          };

          setOriginalData(profileData);
          formActions.reset(profileData);
        }
      } catch (err) {
        setError("Failed to load profile data");
        console.error("Error loading profile:", err);
      } finally {
        setIsFetching(false);
      }
    };

    loadData();
  }, [formActions, currentUser, refreshUserData]);

  async function handleProfileUpdate(data: EnhancedUserProfileData) {
    try {
      formActions.setLoading(true);
      setError(null);

      // Use centralized user data management
      const response = await updateUserData(data);

      // Update local state with the response
      const updatedData = {
        ...data,
        ...response.user,
      };

      setOriginalData(updatedData);
      formActions.reset(updatedData);
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
      throw err;
    }
  }

  function handleCancel() {
    setEditMode(false);
    setError(null);
  }

  const handleChange = (_: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  const handleUploadClick = () => {
    // Avatar upload functionality would go here
    console.log("Avatar upload clicked");
  };

  const getDisplayName = () => {
    const { first_name, last_name, username } = formState.data;
    if (first_name || last_name) {
      return `${first_name} ${last_name}`.trim();
    }
    return username || "User";
  };

  const timezoneOptions = [
    { value: "UTC", label: "UTC" },
    { value: "America/New_York", label: "Eastern Time (US)" },
    { value: "America/Chicago", label: "Central Time (US)" },
    { value: "America/Denver", label: "Mountain Time (US)" },
    { value: "America/Los_Angeles", label: "Pacific Time (US)" },
    { value: "Europe/London", label: "London" },
    { value: "Europe/Paris", label: "Paris" },
    { value: "Asia/Tokyo", label: "Tokyo" },
    { value: "Asia/Shanghai", label: "Shanghai" },
    { value: "Asia/Kuala_Lumpur", label: "Kuala Lumpur" },
  ];

  const languageOptions = [
    { value: "en", label: "English" },
    { value: "ms", label: "Bahasa Malaysia" },
    { value: "zh", label: "中文" },
    { value: "ta", label: "தமிழ்" },
  ];

  const themeOptions = [
    { value: "light", label: "Light" },
    { value: "dark", label: "Dark" },
    { value: "auto", label: "Auto" },
  ];

  if (isFetching) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", py: 8 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1200, mx: "auto", p: 3 }}>
      {/* Profile Header */}
      <ProfileHeader>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={2}>
            <Box sx={{ position: "relative", display: "inline-block" }}>
              <ProfileAvatar
                src={originalData?.username || ""}
                alt={getDisplayName()}
                sx={{
                  backgroundColor: "#4a69dd",
                  fontSize: "2rem",
                  fontWeight: 600,
                }}
              >
                {getDisplayName().charAt(0).toUpperCase()}
              </ProfileAvatar>
              <IconButton
                size="small"
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
            <Box sx={{ display: "flex", gap: 1, mb: 1, flexWrap: "wrap" }}>
              {formState.data.job_title && (
                <Chip
                  label={formState.data.job_title}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              )}
              {formState.data.company && (
                <Chip
                  label={formState.data.company}
                  size="small"
                  color="secondary"
                  variant="outlined"
                />
              )}
            </Box>
            {formState.isDirty && (
              <Chip
                icon={<EditIcon sx={{ fontSize: 16 }} />}
                label="Unsaved Changes"
                size="small"
                color="warning"
                variant="filled"
              />
            )}
          </Grid>
          <Grid item xs={12} md={2} sx={{ textAlign: "right" }}>
            <EditButton
              aria-label={editMode ? "Save profile" : "Edit profile"}
              onClick={
                editMode ? formActions.handleSubmit : () => setEditMode(true)
              }
              disabled={formState.isLoading || (editMode && !formState.isValid)}
            >
              {formState.isLoading ? (
                <CircularProgress size={20} color="inherit" />
              ) : editMode ? (
                <SaveIcon />
              ) : (
                <EditIcon />
              )}
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
        TransitionComponent={Fade}
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
        TransitionComponent={Fade}
      >
        <Alert
          onClose={() => setSuccess(null)}
          severity="success"
          sx={{ width: "100%" }}
        >
          {success}
        </Alert>
      </Snackbar>

      {/* Tabs */}
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

      {/* Personal Info Tab */}
      <TabPanel value={value} index={0}>
        <StyledPaper>
          <SectionTitle>Personal Information</SectionTitle>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <EnhancedFormField
                name="first_name"
                label="First Name"
                value={formState.data.first_name}
                onChange={(e) =>
                  formActions.updateField("first_name", e.target.value)
                }
                onBlur={() => formActions.markFieldTouched("first_name")}
                error={
                  formState.touchedFields.has("first_name")
                    ? formState.errors.first_name
                    : null
                }
                disabled={!editMode}
                maxLength={50}
                autoComplete="given-name"
                tooltip="Your given name or first name"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <EnhancedFormField
                name="last_name"
                label="Last Name"
                value={formState.data.last_name}
                onChange={(e) =>
                  formActions.updateField("last_name", e.target.value)
                }
                onBlur={() => formActions.markFieldTouched("last_name")}
                error={
                  formState.touchedFields.has("last_name")
                    ? formState.errors.last_name
                    : null
                }
                disabled={!editMode}
                maxLength={50}
                autoComplete="family-name"
                tooltip="Your family name or surname"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <EnhancedFormField
                name="username"
                label="Username"
                value={formState.data.username}
                onChange={(e) =>
                  formActions.updateField("username", e.target.value)
                }
                onBlur={() => formActions.markFieldTouched("username")}
                error={
                  formState.touchedFields.has("username")
                    ? formState.errors.username
                    : null
                }
                disabled={!editMode}
                required
                maxLength={30}
                autoComplete="username"
                tooltip="Unique identifier for your account"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <EnhancedFormField
                name="phone"
                label="Phone Number"
                value={formState.data.phone}
                onChange={(e) =>
                  formActions.updateField("phone", e.target.value)
                }
                onBlur={() => formActions.markFieldTouched("phone")}
                error={
                  formState.touchedFields.has("phone")
                    ? formState.errors.phone
                    : null
                }
                disabled={!editMode}
                type="tel"
                maxLength={20}
                autoComplete="tel"
                tooltip="Your contact phone number"
                placeholder="+1234567890"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <EnhancedFormField
                name="company"
                label="Company"
                value={formState.data.company}
                onChange={(e) =>
                  formActions.updateField("company", e.target.value)
                }
                onBlur={() => formActions.markFieldTouched("company")}
                error={
                  formState.touchedFields.has("company")
                    ? formState.errors.company
                    : null
                }
                disabled={!editMode}
                maxLength={100}
                autoComplete="organization"
                tooltip="Your organization or company name"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <EnhancedFormField
                name="job_title"
                label="Job Title"
                value={formState.data.job_title}
                onChange={(e) =>
                  formActions.updateField("job_title", e.target.value)
                }
                onBlur={() => formActions.markFieldTouched("job_title")}
                error={
                  formState.touchedFields.has("job_title")
                    ? formState.errors.job_title
                    : null
                }
                disabled={!editMode}
                maxLength={100}
                autoComplete="organization-title"
                tooltip="Your job title or role"
              />
            </Grid>

            <Grid item xs={12}>
              <EnhancedSelectField
                name="timezone"
                label="Timezone"
                value={formState.data.timezone}
                onChange={(value) => formActions.updateField("timezone", value)}
                options={timezoneOptions}
                error={formState.errors.timezone}
                disabled={!editMode}
                required
                tooltip="Your local timezone for proper date/time display"
              />
            </Grid>

            <Grid item xs={12}>
              <EnhancedFormField
                name="bio"
                label="Bio"
                value={formState.data.bio}
                onChange={(e) => formActions.updateField("bio", e.target.value)}
                onBlur={() => formActions.markFieldTouched("bio")}
                error={
                  formState.touchedFields.has("bio")
                    ? formState.errors.bio
                    : null
                }
                disabled={!editMode}
                multiline
                rows={4}
                maxLength={500}
                tooltip="A brief description about yourself"
                placeholder="Tell us about yourself..."
              />
            </Grid>

            {editMode && (
              <Grid item xs={12} sx={{ textAlign: "right" }}>
                <Box
                  sx={{ display: "flex", gap: 2, justifyContent: "flex-end" }}
                >
                  <Button
                    variant="outlined"
                    startIcon={<CancelIcon />}
                    onClick={formActions.handleCancel}
                    disabled={formState.isLoading}
                  >
                    Cancel
                  </Button>
                  <StyledButton
                    variant="contained"
                    startIcon={
                      formState.isLoading ? (
                        <CircularProgress size={20} color="inherit" />
                      ) : (
                        <SaveIcon />
                      )
                    }
                    onClick={formActions.handleSubmit}
                    disabled={
                      formState.isLoading ||
                      !formState.isValid ||
                      !formState.isDirty
                    }
                  >
                    {formState.isLoading ? "Saving..." : "Save Changes"}
                  </StyledButton>
                </Box>
              </Grid>
            )}
          </Grid>
        </StyledPaper>
      </TabPanel>

      {/* Notifications Tab */}
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

            <Grid item xs={12}>
              <EnhancedSwitchField
                name="email_notifications"
                label="Email Notifications"
                description="Receive important updates and notifications via email"
                checked={formState.data.email_notifications}
                onChange={(checked) =>
                  formActions.updateField("email_notifications", checked)
                }
                disabled={!editMode}
                tooltip="Toggle email notifications for account activity"
              />
            </Grid>

            <Grid item xs={12}>
              <EnhancedSwitchField
                name="push_notifications"
                label="Push Notifications"
                description="Receive real-time browser notifications"
                checked={formState.data.push_notifications}
                onChange={(checked) =>
                  formActions.updateField("push_notifications", checked)
                }
                disabled={!editMode}
                tooltip="Toggle browser push notifications"
              />
            </Grid>

            {editMode && (
              <Grid item xs={12} sx={{ textAlign: "right" }}>
                <Box
                  sx={{ display: "flex", gap: 2, justifyContent: "flex-end" }}
                >
                  <Button
                    variant="outlined"
                    startIcon={<CancelIcon />}
                    onClick={formActions.handleCancel}
                    disabled={formState.isLoading}
                  >
                    Cancel
                  </Button>
                  <StyledButton
                    variant="contained"
                    startIcon={
                      formState.isLoading ? (
                        <CircularProgress size={20} color="inherit" />
                      ) : (
                        <SaveIcon />
                      )
                    }
                    onClick={formActions.handleSubmit}
                    disabled={
                      formState.isLoading ||
                      !formState.isValid ||
                      !formState.isDirty
                    }
                  >
                    {formState.isLoading ? "Saving..." : "Save Changes"}
                  </StyledButton>
                </Box>
              </Grid>
            )}
          </Grid>
        </StyledPaper>
      </TabPanel>

      {/* Security Tab */}
      <TabPanel value={value} index={2}>
        <StyledPaper>
          <SectionTitle>Security Settings</SectionTitle>
          <Divider sx={{ mb: 3 }} />

          <Typography variant="body1" color="text.secondary">
            Security settings will be available in a future update. This will
            include password change functionality, two-factor authentication,
            and security logs.
          </Typography>
        </StyledPaper>
      </TabPanel>

      {/* Preferences Tab */}
      <TabPanel value={value} index={3}>
        <StyledPaper>
          <SectionTitle>Display Preferences</SectionTitle>
          <Divider sx={{ mb: 3 }} />

          <Grid container spacing={3}>
            <Grid item xs={12} sm={6}>
              <EnhancedSelectField
                name="language"
                label="Language"
                value={formState.data.language}
                onChange={(value) => formActions.updateField("language", value)}
                options={languageOptions}
                error={formState.errors.language}
                disabled={!editMode}
                required
                tooltip="Select your preferred interface language"
              />
            </Grid>

            <Grid item xs={12} sm={6}>
              <EnhancedSelectField
                name="theme"
                label="Theme"
                value={formState.data.theme}
                onChange={(value) => formActions.updateField("theme", value)}
                options={themeOptions}
                error={formState.errors.theme}
                disabled={!editMode}
                required
                tooltip="Choose your preferred color theme"
              />
            </Grid>

            {editMode && (
              <Grid item xs={12} sx={{ textAlign: "right" }}>
                <Box
                  sx={{ display: "flex", gap: 2, justifyContent: "flex-end" }}
                >
                  <Button
                    variant="outlined"
                    startIcon={<CancelIcon />}
                    onClick={formActions.handleCancel}
                    disabled={formState.isLoading}
                  >
                    Cancel
                  </Button>
                  <StyledButton
                    variant="contained"
                    startIcon={
                      formState.isLoading ? (
                        <CircularProgress size={20} color="inherit" />
                      ) : (
                        <SaveIcon />
                      )
                    }
                    onClick={formActions.handleSubmit}
                    disabled={
                      formState.isLoading ||
                      !formState.isValid ||
                      !formState.isDirty
                    }
                  >
                    {formState.isLoading ? "Saving..." : "Save Changes"}
                  </StyledButton>
                </Box>
              </Grid>
            )}
          </Grid>
        </StyledPaper>
      </TabPanel>
    </Box>
  );
}
