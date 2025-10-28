import React, { useState, useEffect } from "react";
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  alpha,
  useTheme,
  TextField,
  InputAdornment,
  Chip,
} from "@mui/material";
import {
  Description as ReportIcon,
  TableChart as FormsIcon,
  CloudUpload as ExportIcon,
  Assessment as AnalyticsIcon,
  TrendingUp,
  Build as BuildIcon,
  Search as SearchIcon,
  ArrowUpward,
  PlayArrow,
  Timeline as TimelineIcon,
} from "@mui/icons-material";
import { useNavigate } from "react-router-dom";

interface QuickActionCard {
  title: string;
  description: string;
  icon: React.ReactNode;
  path: string;
  color: string;
  gradient: string;
}

interface DashboardMetrics {
  reportsCreated: number;
  reportsData: number[];
  formsActive: number;
  formsMaximum: number;
  platformUsageChange: number;
}

const MiniSparkline: React.FC<{ data: number[] }> = ({ data }) => {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data
    .map((value, index) => {
      const x = (index / (data.length - 1)) * 100;
      const y = 100 - ((value - min) / range) * 100;
      return `${x},${y}`;
    })
    .join(" ");

  return (
    <svg
      width="100%"
      height="40"
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      style={{ display: "block" }}
    >
      <polyline
        points={points}
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        style={{ opacity: 0.8 }}
      />
    </svg>
  );
};

const CircularProgressRing: React.FC<{ percentage: number; size?: number }> = ({
  percentage,
  size = 80,
}) => {
  const strokeWidth = 8;
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <Box
      sx={{
        position: "relative",
        width: size,
        height: size,
        display: "inline-flex",
      }}
    >
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255, 255, 255, 0.2)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="white"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{
            transition: "stroke-dashoffset 0.5s ease",
          }}
        />
      </svg>
      <Box
        sx={{
          position: "absolute",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          color: "white",
          fontWeight: 700,
          fontSize: "1rem",
        }}
      >
        {percentage}%
      </Box>
    </Box>
  );
};

const Dashboard: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardMetrics();
  }, []);

  const fetchDashboardMetrics = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/dashboard/metrics");
      const data = await response.json();
      setMetrics(data);
    } catch (error) {
      console.error("Error fetching dashboard metrics:", error);
    } finally {
      setLoading(false);
    }
  };

  const quickActions: QuickActionCard[] = [
    {
      title: "Next-Gen Report Builder",
      description: "Create professional reports with AI-powered assistance",
      icon: <ReportIcon sx={{ fontSize: 48 }} />,
      path: "/next-gen-report-builder",
      color: "#5B7EE5",
      gradient: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    },
    {
      title: "Google Forms Export",
      description: "Export Google Forms responses to Excel instantly",
      icon: <FormsIcon sx={{ fontSize: 48 }} />,
      path: "/google-forms-export",
      color: "#EC4899",
      gradient: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
    },
    {
      title: "Form Builder",
      description: "Create and manage custom forms with ease",
      icon: <BuildIcon sx={{ fontSize: 48 }} />,
      path: "/form-builder-admin",
      color: "#3B82F6",
      gradient: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
    },
    {
      title: "Report Templates",
      description: "Browse and customize professional templates",
      icon: <ExportIcon sx={{ fontSize: 48 }} />,
      path: "/report-templates",
      color: "#F59E0B",
      gradient: "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    },
  ];

  const handleSearch = async (event: React.FormEvent) => {
    event.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const formsActivePercentage = metrics
    ? Math.round((metrics.formsActive / metrics.formsMaximum) * 100)
    : 0;

  return (
    <Box
      sx={{
        minHeight: "100vh",
        bgcolor: "#F7F9FA",
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Card
          sx={{
            mb: 4,
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            color: "white",
            borderRadius: "16px",
            boxShadow: "0 8px 32px rgba(102, 126, 234, 0.25)",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <Box
            sx={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              opacity: 0.1,
              backgroundImage: `radial-gradient(circle at 20% 50%, white 1px, transparent 1px),
                               radial-gradient(circle at 80% 80%, white 1px, transparent 1px),
                               radial-gradient(circle at 40% 20%, white 1px, transparent 1px)`,
              backgroundSize: "50px 50px, 80px 80px, 60px 60px",
            }}
          />

          <CardContent sx={{ p: 4, position: "relative", zIndex: 1 }}>
            <Typography
              variant="h3"
              component="h1"
              gutterBottom
              sx={{
                fontWeight: 800,
                fontFamily: "'Inter', sans-serif",
                mb: 1,
                letterSpacing: "-0.02em",
              }}
            >
              Welcome to StratoSys
            </Typography>
            <Typography
              variant="h6"
              sx={{
                fontWeight: 400,
                opacity: 0.95,
                mb: 3,
                maxWidth: "600px",
              }}
            >
              Your comprehensive report and form management platform
            </Typography>

            <Box component="form" onSubmit={handleSearch} sx={{ maxWidth: "600px" }}>
              <TextField
                fullWidth
                placeholder="Search reports, forms, or templates..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon sx={{ color: "rgba(255, 255, 255, 0.7)" }} />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  "& .MuiOutlinedInput-root": {
                    bgcolor: "rgba(255, 255, 255, 0.15)",
                    backdropFilter: "blur(10px)",
                    borderRadius: "12px",
                    color: "white",
                    "& fieldset": {
                      borderColor: "rgba(255, 255, 255, 0.3)",
                    },
                    "&:hover fieldset": {
                      borderColor: "rgba(255, 255, 255, 0.5)",
                    },
                    "&.Mui-focused fieldset": {
                      borderColor: "white",
                    },
                    "& input::placeholder": {
                      color: "rgba(255, 255, 255, 0.7)",
                      opacity: 1,
                    },
                  },
                }}
              />
            </Box>
          </CardContent>
        </Card>

        <Grid container spacing={3} sx={{ mb: 4 }}>
          {quickActions.map((action, index) => (
            <Grid item xs={12} sm={6} md={3} key={index}>
              <Card
                sx={{
                  height: "100%",
                  cursor: "pointer",
                  transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
                  borderRadius: "16px",
                  bgcolor: "white",
                  boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08)",
                  border: "1px solid transparent",
                  position: "relative",
                  "&:hover": {
                    transform: "translateY(-4px)",
                    boxShadow: `0 12px 28px ${alpha(action.color, 0.25)}`,
                    borderColor: action.color,
                  },
                }}
                onClick={() => navigate(action.path)}
              >
                <CardContent
                  sx={{
                    p: 3,
                    textAlign: "center",
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "center",
                  }}
                >
                  <Box
                    sx={{
                      width: 80,
                      height: 80,
                      borderRadius: "20px",
                      background: action.gradient,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      mb: 2.5,
                      color: "white",
                      boxShadow: `0 4px 16px ${alpha(action.color, 0.3)}`,
                    }}
                  >
                    {action.icon}
                  </Box>
                  <Typography
                    variant="h6"
                    gutterBottom
                    sx={{
                      fontWeight: 700,
                      color: "#1F2937",
                      fontFamily: "'Inter', sans-serif",
                      mb: 1,
                    }}
                  >
                    {action.title}
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{
                      color: "#6B7280",
                      lineHeight: 1.6,
                      fontFamily: "'Inter', sans-serif",
                    }}
                  >
                    {action.description}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {!loading && metrics && (
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card
                sx={{
                  background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                  color: "white",
                  borderRadius: "16px",
                  boxShadow: "0 8px 24px rgba(102, 126, 234, 0.25)",
                  overflow: "hidden",
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                    <Box>
                      <Typography
                        variant="body2"
                        sx={{
                          opacity: 0.9,
                          fontWeight: 500,
                          mb: 1,
                          fontFamily: "'Inter', sans-serif",
                        }}
                      >
                        Reports Created
                      </Typography>
                      <Typography
                        variant="h3"
                        sx={{
                          fontWeight: 800,
                          fontFamily: "'Inter', sans-serif",
                          letterSpacing: "-0.02em",
                        }}
                      >
                        {metrics.reportsCreated}
                      </Typography>
                      <Chip
                        icon={<TrendingUp sx={{ fontSize: 14 }} />}
                        label="Last 30 days"
                        size="small"
                        sx={{
                          mt: 1,
                          bgcolor: "rgba(255, 255, 255, 0.2)",
                          color: "white",
                          fontWeight: 600,
                          fontSize: "0.7rem",
                        }}
                      />
                    </Box>
                    <ReportIcon sx={{ fontSize: 48, opacity: 0.3 }} />
                  </Box>
                  <Box sx={{ color: "white", mt: 2 }}>
                    <MiniSparkline data={metrics.reportsData} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card
                sx={{
                  background: "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                  color: "white",
                  borderRadius: "16px",
                  boxShadow: "0 8px 24px rgba(240, 147, 251, 0.25)",
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography
                        variant="body2"
                        sx={{
                          opacity: 0.9,
                          fontWeight: 500,
                          mb: 1,
                          fontFamily: "'Inter', sans-serif",
                        }}
                      >
                        Forms Active
                      </Typography>
                      <Typography
                        variant="h3"
                        sx={{
                          fontWeight: 800,
                          fontFamily: "'Inter', sans-serif",
                          letterSpacing: "-0.02em",
                          mb: 1,
                        }}
                      >
                        {metrics.formsActive}
                      </Typography>
                      <Typography
                        variant="caption"
                        sx={{
                          opacity: 0.85,
                          fontFamily: "'Inter', sans-serif",
                        }}
                      >
                        of {metrics.formsMaximum} maximum
                      </Typography>
                    </Box>
                    <CircularProgressRing percentage={formsActivePercentage} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card
                sx={{
                  background: "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
                  color: "white",
                  borderRadius: "16px",
                  boxShadow: "0 8px 24px rgba(79, 172, 254, 0.25)",
                }}
              >
                <CardContent sx={{ p: 3 }}>
                  <Box display="flex" alignItems="center" justifyContent="space-between">
                    <Box>
                      <Typography
                        variant="body2"
                        sx={{
                          opacity: 0.9,
                          fontWeight: 500,
                          mb: 1,
                          fontFamily: "'Inter', sans-serif",
                        }}
                      >
                        Platform Usage
                      </Typography>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <Typography
                          variant="h3"
                          sx={{
                            fontWeight: 800,
                            fontFamily: "'Inter', sans-serif",
                            letterSpacing: "-0.02em",
                          }}
                        >
                          {metrics.platformUsageChange > 0 ? "+" : ""}
                          {metrics.platformUsageChange}%
                        </Typography>
                        <ArrowUpward sx={{ fontSize: 32, fontWeight: 700 }} />
                      </Box>
                      <Typography
                        variant="caption"
                        sx={{
                          opacity: 0.85,
                          fontFamily: "'Inter', sans-serif",
                        }}
                      >
                        vs last month
                      </Typography>
                    </Box>
                    <TimelineIcon sx={{ fontSize: 56, opacity: 0.3 }} />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        <Card
          sx={{
            borderRadius: "16px",
            boxShadow: "0 2px 12px rgba(0, 0, 0, 0.08)",
            bgcolor: "white",
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Box display="flex" alignItems="center" gap={2} mb={3}>
              <PlayArrow
                sx={{
                  color: theme.palette.primary.main,
                  fontSize: 32,
                }}
              />
              <Typography
                variant="h5"
                sx={{
                  fontWeight: 700,
                  fontFamily: "'Inter', sans-serif",
                  color: "#1F2937",
                }}
              >
                Jump In – Your Next Steps
              </Typography>
            </Box>

            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Card
                  variant="outlined"
                  sx={{
                    height: "100%",
                    borderRadius: "12px",
                    border: "2px solid #E5E7EB",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      borderColor: theme.palette.primary.main,
                      boxShadow: `0 4px 20px ${alpha(
                        theme.palette.primary.main,
                        0.1
                      )}`,
                    },
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                      <ReportIcon sx={{ color: theme.palette.primary.main }} />
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 700,
                          fontFamily: "'Inter', sans-serif",
                          color: "#1F2937",
                        }}
                      >
                        Report Builder
                      </Typography>
                    </Box>
                    <Typography
                      variant="body2"
                      sx={{
                        color: "#6B7280",
                        mb: 3,
                        lineHeight: 1.6,
                        fontFamily: "'Inter', sans-serif",
                      }}
                    >
                      Create reports with advanced AI-powered features and customizable templates
                    </Typography>
                    <Button
                      variant="contained"
                      fullWidth
                      onClick={() => navigate("/next-gen-report-builder")}
                      sx={{
                        bgcolor: "#667eea",
                        color: "white",
                        borderRadius: "10px",
                        textTransform: "none",
                        fontWeight: 600,
                        fontSize: "1rem",
                        py: 1.5,
                        fontFamily: "'Inter', sans-serif",
                        boxShadow: "0 4px 14px rgba(102, 126, 234, 0.3)",
                        "&:hover": {
                          bgcolor: "#5568d3",
                          boxShadow: "0 6px 20px rgba(102, 126, 234, 0.4)",
                        },
                      }}
                    >
                      Get Started
                    </Button>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card
                  variant="outlined"
                  sx={{
                    height: "100%",
                    borderRadius: "12px",
                    border: "2px solid #E5E7EB",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      borderColor: theme.palette.primary.main,
                      boxShadow: `0 4px 20px ${alpha(
                        theme.palette.primary.main,
                        0.1
                      )}`,
                    },
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                      <FormsIcon sx={{ color: "#EC4899" }} />
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 700,
                          fontFamily: "'Inter', sans-serif",
                          color: "#1F2937",
                        }}
                      >
                        Google Forms
                      </Typography>
                    </Box>
                    <Typography
                      variant="body2"
                      sx={{
                        color: "#6B7280",
                        mb: 3,
                        lineHeight: 1.6,
                        fontFamily: "'Inter', sans-serif",
                      }}
                    >
                      Export your Google Forms responses to Excel with comprehensive analytics
                    </Typography>
                    <Button
                      variant="contained"
                      fullWidth
                      onClick={() => navigate("/google-forms-export")}
                      sx={{
                        bgcolor: "#667eea",
                        color: "white",
                        borderRadius: "10px",
                        textTransform: "none",
                        fontWeight: 600,
                        fontSize: "1rem",
                        py: 1.5,
                        fontFamily: "'Inter', sans-serif",
                        boxShadow: "0 4px 14px rgba(102, 126, 234, 0.3)",
                        "&:hover": {
                          bgcolor: "#5568d3",
                          boxShadow: "0 6px 20px rgba(102, 126, 234, 0.4)",
                        },
                      }}
                    >
                      Export Now
                    </Button>
                  </CardContent>
                </Card>
              </Grid>

              <Grid item xs={12} md={4}>
                <Card
                  variant="outlined"
                  sx={{
                    height: "100%",
                    borderRadius: "12px",
                    border: "2px solid #E5E7EB",
                    transition: "all 0.3s ease",
                    "&:hover": {
                      borderColor: theme.palette.primary.main,
                      boxShadow: `0 4px 20px ${alpha(
                        theme.palette.primary.main,
                        0.1
                      )}`,
                    },
                  }}
                >
                  <CardContent sx={{ p: 3 }}>
                    <Box display="flex" alignItems="center" gap={1} mb={2}>
                      <BuildIcon sx={{ color: "#3B82F6" }} />
                      <Typography
                        variant="h6"
                        sx={{
                          fontWeight: 700,
                          fontFamily: "'Inter', sans-serif",
                          color: "#1F2937",
                        }}
                      >
                        Form Builder
                      </Typography>
                    </Box>
                    <Typography
                      variant="body2"
                      sx={{
                        color: "#6B7280",
                        mb: 3,
                        lineHeight: 1.6,
                        fontFamily: "'Inter', sans-serif",
                      }}
                    >
                      Design custom forms easily with drag-and-drop interface and validation
                    </Typography>
                    <Button
                      variant="contained"
                      fullWidth
                      onClick={() => navigate("/form-builder-admin")}
                      sx={{
                        bgcolor: "#667eea",
                        color: "white",
                        borderRadius: "10px",
                        textTransform: "none",
                        fontWeight: 600,
                        fontSize: "1rem",
                        py: 1.5,
                        fontFamily: "'Inter', sans-serif",
                        boxShadow: "0 4px 14px rgba(102, 126, 234, 0.3)",
                        "&:hover": {
                          bgcolor: "#5568d3",
                          boxShadow: "0 6px 20px rgba(102, 126, 234, 0.4)",
                        },
                      }}
                    >
                      Create Form
                    </Button>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default Dashboard;
