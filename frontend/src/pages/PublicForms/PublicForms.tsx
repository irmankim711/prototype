import { useState, useEffect, useCallback } from "react";
import {
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  Grid,
  Box,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Fade,
  Slide,
  alpha,
  useTheme,
  keyframes,
  styled,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import {
  ArrowBack,
  Description,
  AccessTime,
  Logout,
  RocketLaunch,
  AutoAwesome,
  CheckCircleOutline,
  OpenInNew,
  Refresh as RefreshIcon,
} from "@mui/icons-material";
import { formBuilderAPI } from "../../services/formBuilder";

// Define the public form structure that comes from the API
interface PublicForm {
  id: number;
  title: string;
  description: string;
  created_at: string;
  updated_at: string;
  creator_name: string;
  submission_count: number;
  field_count: number;
  has_external_url: boolean;
  external_url?: string;
  is_public: boolean;
  is_active: boolean;
  view_count: number;
}

// External form interface (from localStorage)
interface ExternalForm {
  id: string;
  title: string;
  url: string;
  description?: string;
  createdAt: Date | string;
  qrCode?: string;
}

// Combined form type for display
interface DisplayForm {
  id: string | number;
  title: string;
  description?: string;
  created_at?: string;
  creator_name?: string;
  submission_count?: number;
  field_count?: number;
  external_url?: string;
  is_external?: boolean;
  is_public?: boolean;
  is_active?: boolean;
  view_count?: number;
}

// Apple-style animations
const float = keyframes`
  0%, 100% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-10px) rotate(1deg); }
`;

const pulse = keyframes`
  0% { transform: scale(1); opacity: 0.8; }
  50% { transform: scale(1.05); opacity: 1; }
  100% { transform: scale(1); opacity: 0.8; }
`;

// Styled Components with Apple Design Language
const AppleCard = styled(Card)(({ theme }) => ({
  background: `linear-gradient(145deg, ${alpha(
    theme.palette.common.white,
    0.9
  )}, ${alpha(theme.palette.common.white, 0.7)})`,
  backdropFilter: "blur(20px)",
  border: `1px solid ${alpha(theme.palette.common.white, 0.2)}`,
  borderRadius: "20px",
  boxShadow: `
    0 8px 32px ${alpha(theme.palette.common.black, 0.1)},
    0 2px 8px ${alpha(theme.palette.common.black, 0.05)},
    inset 0 1px 0 ${alpha(theme.palette.common.white, 0.6)}
  `,
  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
  overflow: "hidden",
  position: "relative",
  "&::before": {
    content: '""',
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    height: "1px",
    background: `linear-gradient(90deg, transparent, ${alpha(
      theme.palette.common.white,
      0.8
    )}, transparent)`,
  },
  "&:hover": {
    transform: "translateY(-4px)",
    boxShadow: `
      0 20px 40px ${alpha(theme.palette.common.black, 0.15)},
      0 4px 12px ${alpha(theme.palette.common.black, 0.08)},
      inset 0 1px 0 ${alpha(theme.palette.common.white, 0.7)}
    `,
  },
}));

const AppleButton = styled(Button)(({ theme }) => ({
  borderRadius: "12px",
  textTransform: "none",
  fontWeight: 600,
  fontSize: "16px",
  padding: "12px 24px",
  background: `linear-gradient(145deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
  boxShadow: `
    0 4px 14px ${alpha(theme.palette.primary.main, 0.3)},
    inset 0 1px 0 ${alpha(theme.palette.common.white, 0.2)}
  `,
  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
  position: "relative",
  overflow: "hidden",
  "&::before": {
    content: '""',
    position: "absolute",
    top: 0,
    left: "-100%",
    width: "100%",
    height: "100%",
    background: `linear-gradient(90deg, transparent, ${alpha(
      theme.palette.common.white,
      0.2
    )}, transparent)`,
    transition: "left 0.5s",
  },
  "&:hover": {
    transform: "translateY(-2px)",
    boxShadow: `
      0 8px 25px ${alpha(theme.palette.primary.main, 0.4)},
      inset 0 1px 0 ${alpha(theme.palette.common.white, 0.3)}
    `,
    "&::before": {
      left: "100%",
    },
  },
  "&:active": {
    transform: "translateY(0px)",
  },
}));

const FloatingIcon = styled(Box)(({ theme }) => ({
  animation: `${float} 3s ease-in-out infinite`,
  background: `linear-gradient(145deg, ${alpha(
    theme.palette.primary.main,
    0.1
  )}, ${alpha(theme.palette.primary.main, 0.05)})`,
  borderRadius: "50%",
  padding: "20px",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  backdropFilter: "blur(10px)",
  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
  boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
  "& .MuiSvgIcon-root": {
    fontSize: "48px",
    color: theme.palette.primary.main,
  },
}));

const GradientText = styled(Typography)(({ theme }) => ({
  background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
  WebkitBackgroundClip: "text",
  WebkitTextFillColor: "transparent",
  backgroundClip: "text",
  fontWeight: 700,
}));

export default function PublicForms() {
  const navigate = useNavigate();
  const theme = useTheme();
  const [forms, setForms] = useState<DisplayForm[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Fetch both API forms and external forms
  const fetchAllForms = useCallback(async () => {
    try {
      setLoading(true);
      setError(""); // Clear previous errors

      console.log("PublicForms: Fetching all forms (API + external)");

      // Fetch public forms from API
      const apiResponse = await formBuilderAPI.getPublicForms();
      console.log("PublicForms: API forms fetched successfully:", apiResponse);

      // Handle the response format from our backend
      const apiFormsData = apiResponse.forms || [];
      const apiForms: DisplayForm[] = Array.isArray(apiFormsData)
        ? apiFormsData.map((form: PublicForm) => ({
            ...form,
            is_external: false,
          }))
        : [];

      // Fetch external forms from localStorage
      const storedExternalForms = localStorage.getItem("externalForms");
      const externalForms: DisplayForm[] = storedExternalForms
        ? JSON.parse(storedExternalForms).map((form: ExternalForm) => {
            // Handle date parsing safely
            let createdAt: string;
            try {
              if (typeof form.createdAt === "string") {
                createdAt = form.createdAt;
              } else if (form.createdAt instanceof Date) {
                createdAt = form.createdAt.toISOString();
              } else {
                createdAt = new Date().toISOString();
              }
            } catch (dateError) {
              console.warn("Date parsing error for external form:", dateError);
              createdAt = new Date().toISOString();
            }

            return {
              id: form.id,
              title: form.title,
              description: form.description || "",
              external_url: form.url,
              is_external: true,
              is_active: true,
              is_public: true,
              created_at: createdAt,
              creator_name: "External",
              submission_count: 0,
              field_count: 0,
              view_count: 0,
            };
          })
        : [];

      console.log(
        "PublicForms: External forms from localStorage:",
        externalForms
      );

      // Combine both sources
      const allForms = [...apiForms, ...externalForms];
      setForms(allForms);
    } catch (err) {
      console.error("Error fetching forms:", err);

      // Handle different error types
      if (err instanceof Error) {
        if (err.message.includes("500")) {
          setError(
            "Server error: The forms service is experiencing issues. Please try again later."
          );
        } else if (err.message.includes("401") || err.message.includes("403")) {
          setError("Access denied: Unable to load public forms.");
        } else if (err.message.includes("404")) {
          setError("Forms service not found. Please contact support.");
        } else if (err.message.includes("Subject must be a string")) {
          setError(
            "Authentication error: Invalid session data. Please refresh the page."
          );
        } else {
          setError(`Failed to load forms: ${err.message}`);
        }
      } else {
        setError("An unexpected error occurred while loading forms.");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Call the function on component mount
    fetchAllForms();

    // Auto-refetch on window focus to handle deletions in other tabs
    const handleFocus = () => {
      fetchAllForms();
    };
    window.addEventListener("focus", handleFocus);

    // Poll every 30 seconds for updates
    const pollInterval = setInterval(() => {
      fetchAllForms();
    }, 30000);

    return () => {
      window.removeEventListener("focus", handleFocus);
      clearInterval(pollInterval);
    };
  }, [fetchAllForms]); // Now fetchAllForms is stable with useCallback

  const handleFormAccess = (form: DisplayForm) => {
    if (form.external_url) {
      // Open external URL in new tab
      window.open(form.external_url, "_blank");
    } else {
      // Navigate to internal form fill page
      navigate(`/forms/fill/${form.id}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("quickAccessToken");
    localStorage.removeItem("quickAccessUser");
    navigate("/");
  };

  if (loading) {
    return (
      <Box
        sx={{
          minHeight: "100vh",
          background: `linear-gradient(135deg, 
            ${alpha(theme.palette.primary.main, 0.05)} 0%, 
            ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Box sx={{ textAlign: "center" }}>
          <CircularProgress
            size={60}
            thickness={3}
            sx={{
              color: theme.palette.primary.main,
              mb: 2,
            }}
          />
          <Typography
            variant="h6"
            color="textSecondary"
            sx={{ fontWeight: 500 }}
          >
            Loading your forms...
          </Typography>
        </Box>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        minHeight: "100vh",
        background: `linear-gradient(135deg, 
          ${alpha(theme.palette.primary.main, 0.03)} 0%, 
          ${alpha(theme.palette.secondary.main, 0.03)} 50%,
          ${alpha(theme.palette.primary.main, 0.02)} 100%)`,
        pb: 8,
      }}
    >
      {/* Apple-style Header */}
      <Box
        sx={{
          background: `linear-gradient(145deg, 
            ${alpha(theme.palette.common.white, 0.95)}, 
            ${alpha(theme.palette.common.white, 0.85)})`,
          backdropFilter: "blur(20px)",
          borderBottom: `1px solid ${alpha(theme.palette.common.white, 0.2)}`,
          py: 3,
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <Container maxWidth="lg">
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
              <IconButton
                onClick={() => navigate("/")}
                sx={{
                  background: `linear-gradient(145deg, 
                    ${alpha(theme.palette.primary.main, 0.1)}, 
                    ${alpha(theme.palette.primary.main, 0.05)})`,
                  backdropFilter: "blur(10px)",
                  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
                  borderRadius: "12px",
                  padding: "12px",
                  transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
                  "&:hover": {
                    background: `linear-gradient(145deg, 
                      ${alpha(theme.palette.primary.main, 0.15)}, 
                      ${alpha(theme.palette.primary.main, 0.1)})`,
                    transform: "translateY(-2px)",
                    boxShadow: `0 8px 25px ${alpha(
                      theme.palette.primary.main,
                      0.2
                    )}`,
                  },
                }}
              >
                <ArrowBack sx={{ color: theme.palette.primary.main }} />
              </IconButton>

              <Box>
                <GradientText variant="h4" sx={{ mb: 0.5 }}>
                  Available Forms
                </GradientText>
                <Typography
                  variant="body2"
                  color="textSecondary"
                  sx={{ fontWeight: 500 }}
                >
                  Welcome! You can access and fill out the following public
                  forms.
                </Typography>
              </Box>
            </Box>

            <AppleButton
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={fetchAllForms}
              sx={{
                background: "transparent",
                border: `2px solid ${alpha(theme.palette.primary.main, 0.3)}`,
                color: theme.palette.primary.main,
                "&:hover": {
                  background: `linear-gradient(145deg, 
                    ${alpha(theme.palette.primary.main, 0.1)}, 
                    ${alpha(theme.palette.primary.main, 0.05)})`,
                  border: `2px solid ${alpha(theme.palette.primary.main, 0.5)}`,
                },
              }}
            >
              Refresh
            </AppleButton>
            <AppleButton
              variant="contained"
              startIcon={<Logout />}
              onClick={handleLogout}
              sx={{
                background: `linear-gradient(145deg, 
                  ${alpha(theme.palette.error.main, 0.9)}, 
                  ${alpha(theme.palette.error.dark, 0.9)})`,
                "&:hover": {
                  background: `linear-gradient(145deg, 
                    ${alpha(theme.palette.error.main, 1)}, 
                    ${alpha(theme.palette.error.dark, 1)})`,
                },
              }}
            >
              Logout
            </AppleButton>
          </Box>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ pt: 6 }}>
        {error && (
          <Fade in={!!error}>
            <Alert
              severity="error"
              sx={{
                mb: 3,
                borderRadius: "16px",
                backdropFilter: "blur(10px)",
                background: `linear-gradient(145deg, 
                  ${alpha(theme.palette.error.main, 0.1)}, 
                  ${alpha(theme.palette.error.main, 0.05)})`,
              }}
            >
              {error}
            </Alert>
          </Fade>
        )}

        {forms.length === 0 ? (
          <Fade in={!loading} timeout={800}>
            <Box>
              <AppleCard
                sx={{
                  textAlign: "center",
                  py: 8,
                  px: 4,
                  maxWidth: 600,
                  mx: "auto",
                  position: "relative",
                  overflow: "visible",
                }}
              >
                <FloatingIcon sx={{ mx: "auto", mb: 4 }}>
                  <AutoAwesome />
                </FloatingIcon>

                <GradientText variant="h3" sx={{ mb: 2, fontWeight: 800 }}>
                  You're All Caught Up!
                </GradientText>

                <Typography
                  variant="h6"
                  color="textSecondary"
                  sx={{
                    mb: 4,
                    fontWeight: 400,
                    lineHeight: 1.6,
                    maxWidth: 400,
                    mx: "auto",
                  }}
                >
                  No public forms are available right now. Check back later for
                  new opportunities to share your thoughts!
                </Typography>

                <Box
                  sx={{
                    display: "flex",
                    gap: 2,
                    justifyContent: "center",
                    flexWrap: "wrap",
                  }}
                >
                  <AppleButton
                    variant="contained"
                    startIcon={<CheckCircleOutline />}
                    onClick={() => navigate("/")}
                  >
                    Back to Home
                  </AppleButton>

                  <AppleButton
                    variant="outlined"
                    startIcon={<RocketLaunch />}
                    onClick={() => window.location.reload()}
                    sx={{
                      background: "transparent",
                      border: `2px solid ${alpha(
                        theme.palette.primary.main,
                        0.3
                      )}`,
                      color: theme.palette.primary.main,
                      "&:hover": {
                        background: `linear-gradient(145deg, 
                          ${alpha(theme.palette.primary.main, 0.1)}, 
                          ${alpha(theme.palette.primary.main, 0.05)})`,
                        border: `2px solid ${alpha(
                          theme.palette.primary.main,
                          0.5
                        )}`,
                      },
                    }}
                  >
                    Refresh
                  </AppleButton>
                </Box>

                {/* Decorative elements */}
                <Box
                  sx={{
                    position: "absolute",
                    top: -20,
                    right: -20,
                    width: 40,
                    height: 40,
                    borderRadius: "50%",
                    background: `linear-gradient(145deg, 
                      ${alpha(theme.palette.secondary.main, 0.2)}, 
                      ${alpha(theme.palette.secondary.main, 0.1)})`,
                    animation: `${pulse} 2s ease-in-out infinite`,
                  }}
                />
                <Box
                  sx={{
                    position: "absolute",
                    bottom: -10,
                    left: -10,
                    width: 30,
                    height: 30,
                    borderRadius: "50%",
                    background: `linear-gradient(145deg, 
                      ${alpha(theme.palette.primary.main, 0.2)}, 
                      ${alpha(theme.palette.primary.main, 0.1)})`,
                    animation: `${pulse} 2s ease-in-out infinite 0.5s`,
                  }}
                />
              </AppleCard>
            </Box>
          </Fade>
        ) : (
          <Grid container spacing={3}>
            {forms.map((form, index) => (
              <Grid item xs={12} md={6} lg={4} key={form.id}>
                <Slide in={!loading} direction="up" timeout={600 + index * 100}>
                  <AppleCard>
                    <CardContent sx={{ p: 3 }}>
                      <Box
                        sx={{ display: "flex", alignItems: "center", mb: 2 }}
                      >
                        <Box
                          sx={{
                            p: 1.5,
                            borderRadius: "12px",
                            background: `linear-gradient(145deg, 
                              ${alpha(theme.palette.primary.main, 0.1)}, 
                              ${alpha(theme.palette.primary.main, 0.05)})`,
                            mr: 2,
                          }}
                        >
                          <Description
                            sx={{ color: theme.palette.primary.main }}
                          />
                        </Box>
                        <Typography variant="h6" sx={{ fontWeight: 700 }}>
                          {form.title}
                        </Typography>
                      </Box>

                      <Typography
                        variant="body2"
                        color="textSecondary"
                        sx={{ mb: 3, lineHeight: 1.6 }}
                      >
                        {form.description}
                      </Typography>

                      <Box
                        sx={{
                          display: "flex",
                          alignItems: "center",
                          gap: 2,
                          mb: 3,
                          flexWrap: "wrap",
                        }}
                      >
                        <Chip
                          icon={<AccessTime />}
                          label={
                            form.created_at
                              ? new Date(form.created_at).toLocaleDateString()
                              : "N/A"
                          }
                          size="small"
                          sx={{
                            background: `linear-gradient(145deg, 
                              ${alpha(theme.palette.info.main, 0.1)}, 
                              ${alpha(theme.palette.info.main, 0.05)})`,
                            color: theme.palette.info.main,
                            border: `1px solid ${alpha(
                              theme.palette.info.main,
                              0.2
                            )}`,
                          }}
                        />
                        <Chip
                          icon={<Description />}
                          label={`${form.field_count || 0} fields`}
                          size="small"
                          sx={{
                            background: `linear-gradient(145deg, 
                              ${alpha(theme.palette.success.main, 0.1)}, 
                              ${alpha(theme.palette.success.main, 0.05)})`,
                            color: theme.palette.success.main,
                            border: `1px solid ${alpha(
                              theme.palette.success.main,
                              0.2
                            )}`,
                          }}
                        />
                        {form.external_url && (
                          <Chip
                            icon={<OpenInNew />}
                            label={
                              form.is_external
                                ? "External Form"
                                : "External Link"
                            }
                            size="small"
                            sx={{
                              background: `linear-gradient(145deg, 
                                ${alpha(theme.palette.warning.main, 0.1)}, 
                                ${alpha(theme.palette.warning.main, 0.05)})`,
                              color: theme.palette.warning.main,
                              border: `1px solid ${alpha(
                                theme.palette.warning.main,
                                0.2
                              )}`,
                            }}
                          />
                        )}
                      </Box>

                      <AppleButton
                        fullWidth
                        variant="contained"
                        onClick={() => handleFormAccess(form)}
                        startIcon={
                          form.external_url ? <OpenInNew /> : undefined
                        }
                      >
                        {form.external_url
                          ? "Open External Form"
                          : "Start Form"}
                      </AppleButton>
                    </CardContent>
                  </AppleCard>
                </Slide>
              </Grid>
            ))}
          </Grid>
        )}
      </Container>
    </Box>
  );
}
