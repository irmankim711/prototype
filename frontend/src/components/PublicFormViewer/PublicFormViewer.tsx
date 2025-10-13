import React from "react";
import { useState, useEffect, useCallback } from "react";
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  CardActions,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  IconButton,
  Fade,
  alpha,
  useTheme,
  styled,
  keyframes,
} from "@mui/material";
import {
  Description,
  OpenInNew,
  Send,
  ExitToApp,
  AccessTime,
  Security,
  CheckCircle,
} from "@mui/icons-material";
import { formBuilderAPI } from "../../services/formBuilder";

// Styled components with modern design
const float = keyframes`
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-5px); }
`;

const FormCard = styled(Card)(({ theme }) => ({
  background: `linear-gradient(145deg, ${alpha(
    theme.palette.common.white,
    0.9
  )}, ${alpha(theme.palette.common.white, 0.7)})`,
  backdropFilter: "blur(20px)",
  border: `1px solid ${alpha(theme.palette.common.white, 0.2)}`,
  borderRadius: "20px",
  boxShadow: `
    0 8px 32px ${alpha(theme.palette.common.black, 0.1)},
    0 2px 8px ${alpha(theme.palette.common.black, 0.05)}
  `,
  transition: "all 0.3s ease-in-out",
  "&:hover": {
    transform: "translateY(-4px)",
    boxShadow: `
      0 12px 40px ${alpha(theme.palette.common.black, 0.15)},
      0 4px 12px ${alpha(theme.palette.common.black, 0.1)}
    `,
  },
}));

const FloatingHeader = styled(Box)(({ theme }) => ({
  background: `linear-gradient(135deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
  borderRadius: "24px",
  padding: theme.spacing(3),
  color: "white",
  textAlign: "center",
  marginBottom: theme.spacing(4),
  animation: `${float} 3s ease-in-out infinite`,
  boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.3)}`,
}));

interface AccessibleForm {
  id: string | number;
  title: string;
  description?: string;
  type: "internal" | "external";
  external_url?: string;
  field_count?: number;
  created_at?: string;
}

interface AccessCodeInfo {
  title: string;
  description?: string;
}

interface PublicFormViewerProps {
  accessToken: string;
  onLogout: () => void;
}

const PublicFormViewer: React.FC<PublicFormViewerProps> = ({
  accessToken,
  onLogout,
}) => {
  const [accessibleForms, setAccessibleForms] = useState<AccessibleForm[]>([]);
  const [accessCodeInfo, setAccessCodeInfo] = useState<AccessCodeInfo | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const theme = useTheme();

  const fetchAccessibleForms = useCallback(async () => {
    try {
      setLoading(true);
      const response = await formBuilderAPI.getAccessibleForms(accessToken);
      setAccessibleForms(response.accessible_forms || []);
      setAccessCodeInfo(response.access_code_info);
    } catch (error: unknown) {
      const axiosError = error as { response?: { data?: { error?: string } } };
      setError(
        axiosError.response?.data?.error || "Failed to load accessible forms"
      );
    } finally {
      setLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    fetchAccessibleForms();
  }, [fetchAccessibleForms]);

  const handleFormAccess = (form: AccessibleForm) => {
    if (form.type === "external" && form.external_url) {
      // Open external form in new tab
      window.open(form.external_url, "_blank");
    } else {
      // Navigate to internal form
      window.open(`/forms/${form.id}?access_token=${accessToken}`, "_blank");
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return "N/A";
    return new Date(dateString).toLocaleDateString();
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 8, textAlign: "center" }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading accessible forms...
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Fade in timeout={800}>
        <Box>
          {/* Header */}
          <FloatingHeader>
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <Box>
                <Typography variant="h4" sx={{ fontWeight: "bold", mb: 1 }}>
                  {accessCodeInfo?.title || "Accessible Forms"}
                </Typography>
                {accessCodeInfo?.description && (
                  <Typography variant="body1" sx={{ opacity: 0.9 }}>
                    {accessCodeInfo.description}
                  </Typography>
                )}
              </Box>
              <IconButton
                onClick={onLogout}
                sx={{
                  color: "white",
                  bgcolor: alpha(theme.palette.common.white, 0.2),
                  "&:hover": {
                    bgcolor: alpha(theme.palette.common.white, 0.3),
                  },
                }}
              >
                <ExitToApp />
              </IconButton>
            </Box>
          </FloatingHeader>

          {error && (
            <Alert severity="error" sx={{ mb: 3, borderRadius: "12px" }}>
              {error}
            </Alert>
          )}

          {/* Forms Grid */}
          {accessibleForms.length === 0 ? (
            <Box sx={{ textAlign: "center", py: 8 }}>
              <Security sx={{ fontSize: 64, color: "text.secondary", mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Forms Available
              </Typography>
              <Typography color="text.secondary">
                No forms are currently accessible with your access code.
              </Typography>
            </Box>
          ) : (
            <Grid container spacing={3}>
              {accessibleForms.map((form, index) => (
                <Grid item xs={12} md={6} lg={4} key={form.id}>
                  <Fade in timeout={800 + index * 100}>
                    <FormCard>
                      <CardContent sx={{ p: 3 }}>
                        <Box
                          sx={{
                            display: "flex",
                            alignItems: "flex-start",
                            mb: 2,
                          }}
                        >
                          <Description
                            sx={{
                              mr: 1,
                              mt: 0.5,
                              color:
                                form.type === "external"
                                  ? "secondary.main"
                                  : "primary.main",
                            }}
                          />
                          <Box sx={{ flex: 1 }}>
                            <Typography
                              variant="h6"
                              sx={{ fontWeight: "bold", mb: 1 }}
                            >
                              {form.title}
                            </Typography>
                            <Chip
                              label={
                                form.type === "external"
                                  ? "External"
                                  : "Internal"
                              }
                              size="small"
                              color={
                                form.type === "external"
                                  ? "secondary"
                                  : "primary"
                              }
                              sx={{ mb: 1 }}
                            />
                          </Box>
                        </Box>

                        {form.description && (
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ mb: 2 }}
                          >
                            {form.description}
                          </Typography>
                        )}

                        <Box
                          sx={{
                            display: "flex",
                            gap: 1,
                            flexWrap: "wrap",
                            mb: 2,
                          }}
                        >
                          {form.field_count !== undefined &&
                            form.field_count > 0 && (
                              <Chip
                                label={`${form.field_count} fields`}
                                size="small"
                                variant="outlined"
                              />
                            )}
                          {form.created_at && (
                            <Chip
                              label={formatDate(form.created_at)}
                              size="small"
                              variant="outlined"
                              icon={<AccessTime />}
                            />
                          )}
                        </Box>
                      </CardContent>

                      <CardActions sx={{ p: 3, pt: 0 }}>
                        <Button
                          fullWidth
                          variant="contained"
                          startIcon={
                            form.type === "external" ? <OpenInNew /> : <Send />
                          }
                          onClick={() => handleFormAccess(form)}
                          sx={{
                            py: 1.5,
                            borderRadius: "12px",
                            background:
                              form.type === "external"
                                ? `linear-gradient(45deg, ${theme.palette.secondary.main}, ${theme.palette.secondary.dark})`
                                : `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
                            "&:hover": {
                              transform: "translateY(-2px)",
                              boxShadow: `0 8px 20px ${alpha(
                                form.type === "external"
                                  ? theme.palette.secondary.main
                                  : theme.palette.primary.main,
                                0.3
                              )}`,
                            },
                            transition: "all 0.3s ease-in-out",
                          }}
                        >
                          {form.type === "external"
                            ? "Open External Form"
                            : "Access Form"}
                        </Button>
                      </CardActions>
                    </FormCard>
                  </Fade>
                </Grid>
              ))}
            </Grid>
          )}

          {/* Footer */}
          <Box
            sx={{
              textAlign: "center",
              mt: 6,
              pt: 4,
              borderTop: 1,
              borderColor: "divider",
            }}
          >
            <Typography variant="body2" color="text.secondary">
              <CheckCircle
                sx={{ fontSize: 16, mr: 1, verticalAlign: "middle" }}
              />
              Secure access provided by access code authentication
            </Typography>
          </Box>
        </Box>
      </Fade>
    </Container>
  );
};

export default PublicFormViewer;
