import React, { useState, useCallback, useMemo } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { formBuilderAPI, type Form } from "../../services/formBuilder";
import {
  Box,
  Typography,
  Button,
  Card,
  CardContent,
  CardActions,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Snackbar,
  Chip,
  IconButton,
  TextField,
  Tabs,
  Tab,
  Paper,
  Divider,
  Badge,
  Tooltip,
  Fade,
  Collapse,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  type SelectChangeEvent,
  useTheme,
  alpha,
  Container,
  Stack,
  Skeleton,
  ToggleButton,
  ToggleButtonGroup,
  Menu,
  MenuItem,
} from "@mui/material";
import {
  Add,
  Delete,
  Edit,
  Share,
  QrCode,
  Visibility,
  Analytics,
  Settings,
  Public,
  Launch,
  MoreVert,
  Dashboard,
  Search,
  Sort,
  ContentCopy,
  Undo,
  Schedule,
  TrendingUp,
  Group,
  Refresh,
  Warning,
  CheckCircle,
  ViewModule,
  ViewStream,
  GridView,
  Close,
} from "@mui/icons-material";
import { Bar, Doughnut } from "react-chartjs-2";
import debounce from "lodash/debounce";

import FormBuilder from "../../components/FormBuilder/FormBuilder";
import QRCodeManager from "../../components/FormBuilder/QRCodeManager";

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
      id={`enhanced-tabpanel-${index}`}
      aria-labelledby={`enhanced-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

interface ExternalForm {
  id: string;
  title: string;
  url: string;
  description?: string;
  createdAt: Date;
  qrCode?: string;
  submissions?: number;
  lastUpdated?: Date;
  favicon?: string;
  isGoogleForm?: boolean;
}

interface FormCardProps {
  form: Form;
  onEdit: (form: Form) => void;
  onDelete: (formId: number) => void;
  onShare: (form: Form) => void;
  onQRCode: (form: Form) => void;
  isHovered: boolean;
  onHover: (formId: number | null) => void;
}

const FormCard: React.FC<FormCardProps> = ({
  form,
  onEdit,
  onDelete,
  onShare,
  onQRCode,
  isHovered,
  onHover,
}) => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  return (
    <Fade in timeout={300}>
      <Card
        onMouseEnter={() => onHover(form.id)}
        onMouseLeave={() => onHover(null)}
        sx={{
          height: "100%",
          display: "flex",
          flexDirection: "column",
          borderRadius: 4,
          transition: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
          cursor: "pointer",
          border: "1px solid",
          borderColor: isHovered ? theme.palette.primary.main : "transparent",
          background: isHovered
            ? `linear-gradient(135deg, ${alpha(
                theme.palette.primary.light,
                0.05
              )} 0%, ${alpha(theme.palette.secondary.light, 0.05)} 100%)`
            : "white",
          boxShadow: isHovered
            ? `0 8px 32px ${alpha(theme.palette.primary.main, 0.2)}`
            : `0 2px 8px ${alpha(theme.palette.grey[500], 0.1)}`,
          transform: isHovered ? "translateY(-4px)" : "translateY(0)",
          "&:hover": {
            "& .form-actions": {
              opacity: 1,
              transform: "translateY(0)",
            },
          },
        }}
      >
        <CardContent sx={{ flexGrow: 1, p: 3 }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              mb: 2,
            }}
          >
            <Typography
              variant="h6"
              component="h2"
              sx={{
                flexGrow: 1,
                mr: 1,
                fontWeight: 600,
                color: theme.palette.text.primary,
                overflow: "hidden",
                textOverflow: "ellipsis",
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
              }}
            >
              {form.title}
            </Typography>
            <Tooltip title="More options">
              <IconButton
                size="small"
                onClick={handleMenuOpen}
                sx={{
                  opacity: isHovered ? 1 : 0.6,
                  transition: "opacity 0.2s",
                }}
              >
                <MoreVert />
              </IconButton>
            </Tooltip>
          </Box>

          {form.description && (
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{
                mb: 2,
                display: "-webkit-box",
                WebkitLineClamp: 3,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
                lineHeight: 1.4,
              }}
            >
              {form.description}
            </Typography>
          )}

          <Stack direction="row" spacing={1} sx={{ mb: 2, flexWrap: "wrap" }}>
            <Chip
              icon={<Visibility />}
              label={`${form.submission_count || 0} submissions`}
              size="small"
              color="primary"
              variant="outlined"
            />
            <Chip
              icon={form.is_public ? <Public /> : <Settings />}
              label={form.is_public ? "Public" : "Private"}
              size="small"
              color={form.is_public ? "success" : "default"}
            />
            <Chip
              label={form.is_active ? "Active" : "Inactive"}
              size="small"
              color={form.is_active ? "primary" : "default"}
              variant={form.is_active ? "filled" : "outlined"}
            />
          </Stack>

          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Typography variant="caption" color="text.secondary">
              Created: {new Date(form.created_at).toLocaleDateString()}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Last updated: {new Date(form.updated_at).toLocaleDateString()}
            </Typography>
          </Box>
        </CardContent>

        <Collapse in={isHovered} timeout={200}>
          <CardActions
            className="form-actions"
            sx={{
              p: 2,
              pt: 0,
              justifyContent: "space-between",
              background: alpha(theme.palette.grey[50], 0.8),
              borderTop: `1px solid ${alpha(theme.palette.grey[300], 0.5)}`,
            }}
          >
            <Stack direction="row" spacing={1}>
              <Tooltip title="Edit form">
                <Button
                  size="small"
                  startIcon={<Edit />}
                  onClick={() => onEdit(form)}
                  variant="outlined"
                  sx={{ borderRadius: 2 }}
                >
                  Edit
                </Button>
              </Tooltip>
              <Tooltip title="Generate QR code">
                <Button
                  size="small"
                  startIcon={<QrCode />}
                  onClick={() => onQRCode(form)}
                  variant="outlined"
                  sx={{ borderRadius: 2 }}
                >
                  QR
                </Button>
              </Tooltip>
            </Stack>
            <Stack direction="row" spacing={1}>
              <Tooltip title="Share form">
                <IconButton
                  size="small"
                  onClick={() => onShare(form)}
                  sx={{
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 1,
                  }}
                >
                  <Share />
                </IconButton>
              </Tooltip>
              <Tooltip title="Delete form">
                <IconButton
                  size="small"
                  onClick={() => onDelete(form.id)}
                  color="error"
                  sx={{
                    border: `1px solid ${theme.palette.error.light}`,
                    borderRadius: 1,
                    opacity: isHovered ? 1 : 0,
                    transition: "opacity 0.2s",
                  }}
                >
                  <Delete />
                </IconButton>
              </Tooltip>
            </Stack>
          </CardActions>
        </Collapse>

        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          transformOrigin={{ horizontal: "right", vertical: "top" }}
          anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
        >
          <MenuItem
            onClick={() => {
              onEdit(form);
              handleMenuClose();
            }}
          >
            <Edit sx={{ mr: 1 }} />
            Edit Form
          </MenuItem>
          <MenuItem
            onClick={() => {
              onShare(form);
              handleMenuClose();
            }}
          >
            <Share sx={{ mr: 1 }} />
            Share Form
          </MenuItem>
          <MenuItem
            onClick={() => {
              onQRCode(form);
              handleMenuClose();
            }}
          >
            <QrCode sx={{ mr: 1 }} />
            QR Code
          </MenuItem>
          <Divider />
          <MenuItem
            onClick={() => {
              onDelete(form.id);
              handleMenuClose();
            }}
            sx={{ color: "error.main" }}
          >
            <Delete sx={{ mr: 1 }} />
            Delete Form
          </MenuItem>
        </Menu>
      </Card>
    </Fade>
  );
};

export default function FormBuilderDashboardEnhanced() {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [editingFormId, setEditingFormId] = useState<number | null>(null);
  const [selectedFormForQR, setSelectedFormForQR] = useState<Form | null>(null);
  const [showFormBuilder, setShowFormBuilder] = useState(false);

  // Search and filter states
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [filterStatus, setFilterStatus] = useState<
    "all" | "active" | "inactive"
  >("all");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  // Dialog states
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [externalFormDialogOpen, setExternalFormDialogOpen] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [selectedForm, setSelectedForm] = useState<Form | null>(null);
  const [hoveredFormId, setHoveredFormId] = useState<number | null>(null);

  // Form data states
  const [shareUrl, setShareUrl] = useState("");
  const [newExternalForm, setNewExternalForm] = useState({
    title: "",
    url: "",
    description: "",
  });

  // External forms stored in localStorage
  const [externalForms, setExternalForms] = useState<ExternalForm[]>(() => {
    const saved = localStorage.getItem("externalForms");
    return saved ? JSON.parse(saved) : [];
  });

  // Notification state
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: "success" | "error" | "warning" | "info";
    action?: React.ReactNode;
  }>({
    open: false,
    message: "",
    severity: "success",
  });

  const [page] = useState(1);

  // Fetch forms data
  const {
    data: formsData,
    isLoading: formsLoading,
    error: formsError,
    refetch,
  } = useQuery({
    queryKey: ["forms", page],
    queryFn: () => formBuilderAPI.getForms({ page, limit: 50 }),
    staleTime: 1000 * 60 * 2, // 2 minutes
  });

  // Memoize forms to avoid dependency warnings
  const forms = useMemo(() => formsData?.forms || [], [formsData?.forms]);

  // Debounced search
  const debouncedSearch = useCallback((query: string) => {
    const handler = debounce((q: string) => {
      setSearchQuery(q);
    }, 300);
    handler(query);
  }, []);

  // Filtered and sorted forms
  const filteredForms = useMemo(() => {
    const filtered = forms.filter((form: Form) => {
      const matchesSearch =
        form.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (form.description &&
          form.description.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesStatus =
        filterStatus === "all" ||
        (filterStatus === "active" && form.is_active) ||
        (filterStatus === "inactive" && !form.is_active);

      return matchesSearch && matchesStatus;
    });

    // Sort forms
    filtered.sort((a: Form, b: Form) => {
      let aValue, bValue;

      switch (sortBy) {
        case "title":
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case "submissions":
          aValue = a.submission_count || 0;
          bValue = b.submission_count || 0;
          break;
        case "updated_at":
          aValue = new Date(a.updated_at).getTime();
          bValue = new Date(b.updated_at).getTime();
          break;
        default:
          aValue = new Date(a.created_at).getTime();
          bValue = new Date(b.created_at).getTime();
      }

      if (sortOrder === "asc") {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    return filtered;
  }, [forms, searchQuery, sortBy, sortOrder, filterStatus]);

  // Analytics data
  const analyticsData = useMemo(() => {
    const totalForms = forms.length;
    const activeForms = forms.filter((f: Form) => f.is_active).length;
    const totalSubmissions = forms.reduce(
      (sum: number, f: Form) => sum + (f.submission_count || 0),
      0
    );
    const avgSubmissions =
      totalForms > 0 ? Math.round(totalSubmissions / totalForms) : 0;

    // Chart data for submissions over time
    const submissionChart = {
      labels: forms
        .slice(0, 10)
        .map((f: Form) => f.title.substring(0, 10) + "..."),
      datasets: [
        {
          label: "Submissions",
          data: forms.slice(0, 10).map((f: Form) => f.submission_count || 0),
          backgroundColor: alpha(theme.palette.primary.main, 0.6),
          borderColor: theme.palette.primary.main,
          borderWidth: 2,
          borderRadius: 8,
        },
      ],
    };

    // Status distribution
    const statusChart = {
      labels: ["Active", "Inactive"],
      datasets: [
        {
          data: [activeForms, totalForms - activeForms],
          backgroundColor: [
            theme.palette.success.main,
            theme.palette.grey[400],
          ],
          borderWidth: 0,
        },
      ],
    };

    return {
      totalForms,
      activeForms,
      totalSubmissions,
      avgSubmissions,
      submissionChart,
      statusChart,
    };
  }, [forms, theme]);

  // Delete form mutation
  const deleteMutation = useMutation({
    mutationFn: formBuilderAPI.deleteForm,
    onSuccess: () => {
      setSnackbar({
        open: true,
        message: "Form deleted successfully!",
        severity: "success",
        action: (
          <Button
            size="small"
            onClick={() => {
              setSnackbar((prev) => ({ ...prev, open: false }));
              // Implement undo functionality here
            }}
            sx={{ color: "white" }}
            startIcon={<Undo />}
          >
            UNDO
          </Button>
        ),
      });
      refetch();
      setDeleteConfirmOpen(false);
    },
    onError: () => {
      setSnackbar({
        open: true,
        message: "Failed to delete form",
        severity: "error",
      });
    },
  });

  // Handlers
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleNewForm = () => {
    setShowFormBuilder(true);
    setEditingFormId(null);
  };

  const handleEditForm = (form: Form) => {
    setShowFormBuilder(true);
    setEditingFormId(form.id);
  };

  const handleDeleteForm = (formId: number) => {
    const form = forms.find((f: Form) => f.id === formId);
    setSelectedForm(form);
    setDeleteConfirmOpen(true);
  };

  const confirmDeleteForm = () => {
    if (selectedForm) {
      deleteMutation.mutate(selectedForm.id);
    }
  };

  const handleShareForm = (form: Form) => {
    const url = `${window.location.origin}/forms/${form.id}`;
    setShareUrl(url);
    setSelectedForm(form);
    setShareDialogOpen(true);
  };

  const handleCopyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setSnackbar({
        open: true,
        message: "Copied to clipboard!",
        severity: "success",
      });
    } catch {
      setSnackbar({
        open: true,
        message: "Failed to copy to clipboard",
        severity: "error",
      });
    }
  };

  const handleQRCodeForm = (form: Form) => {
    setSelectedFormForQR(form);
  };

  const handleAddExternalForm = () => {
    const newForm: ExternalForm = {
      id: Date.now().toString(),
      ...newExternalForm,
      createdAt: new Date(),
      submissions: Math.floor(Math.random() * 100),
      lastUpdated: new Date(),
      isGoogleForm: newExternalForm.url.includes("forms.google.com"),
      favicon: newExternalForm.url.includes("forms.google.com")
        ? "https://ssl.gstatic.com/docs/forms/favicon_forms.ico"
        : undefined,
    };

    const updatedForms = [...externalForms, newForm];
    setExternalForms(updatedForms);
    localStorage.setItem("externalForms", JSON.stringify(updatedForms));

    setNewExternalForm({ title: "", url: "", description: "" });
    setExternalFormDialogOpen(false);
    setSnackbar({
      open: true,
      message: "External form added successfully!",
      severity: "success",
    });
  };

  const handleDeleteExternalForm = (formId: string) => {
    const updatedForms = externalForms.filter((form) => form.id !== formId);
    setExternalForms(updatedForms);
    localStorage.setItem("externalForms", JSON.stringify(updatedForms));
    setSnackbar({
      open: true,
      message: "External form removed!",
      severity: "success",
    });
  };

  const handleFormSaved = () => {
    setShowFormBuilder(false);
    setEditingFormId(null);
    refetch();
    setSnackbar({
      open: true,
      message: "Form saved successfully!",
      severity: "success",
    });
  };

  const handleSortChange = (event: SelectChangeEvent) => {
    setSortBy(event.target.value);
  };

  const handleStatusFilterChange = (event: SelectChangeEvent) => {
    setFilterStatus(event.target.value as "all" | "active" | "inactive");
  };

  if (showFormBuilder) {
    return (
      <FormBuilder
        formId={editingFormId || undefined}
        onSave={handleFormSaved}
        onCancel={() => {
          setShowFormBuilder(false);
          setEditingFormId(null);
        }}
      />
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Enhanced Header with Modern Design */}
      <Box
        sx={{
          background: `linear-gradient(135deg, ${alpha(
            theme.palette.primary.main,
            0.1
          )} 0%, ${alpha(theme.palette.secondary.main, 0.05)} 100%)`,
          borderRadius: 4,
          p: 4,
          mb: 4,
          border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
        }}
      >
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: { xs: "flex-start", md: "center" },
            flexDirection: { xs: "column", md: "row" },
            gap: 2,
          }}
        >
          <Box>
            <Typography
              variant="h3"
              component="h1"
              sx={{
                fontWeight: 700,
                background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                mb: 1,
              }}
            >
              Form Builder Dashboard
            </Typography>
            <Typography
              variant="h6"
              color="text.secondary"
              sx={{ fontWeight: 400 }}
            >
              Create, manage, and analyze your forms with ease
            </Typography>
          </Box>

          <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
            <Tooltip title="Refresh data">
              <IconButton
                onClick={() => refetch()}
                sx={{
                  backgroundColor: alpha(theme.palette.primary.main, 0.1),
                  "&:hover": {
                    backgroundColor: alpha(theme.palette.primary.main, 0.2),
                  },
                }}
              >
                <Refresh />
              </IconButton>
            </Tooltip>
            <Button
              variant="contained"
              size="large"
              startIcon={<Add />}
              onClick={handleNewForm}
              sx={{
                borderRadius: 3,
                textTransform: "none",
                fontWeight: 600,
                px: 3,
                py: 1.5,
                background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                boxShadow: `0 4px 16px ${alpha(
                  theme.palette.primary.main,
                  0.3
                )}`,
                "&:hover": {
                  boxShadow: `0 6px 20px ${alpha(
                    theme.palette.primary.main,
                    0.4
                  )}`,
                },
              }}
            >
              Create New Form
            </Button>
          </Stack>
        </Box>
      </Box>

      {/* Enhanced Navigation Tabs */}
      <Paper
        sx={{
          borderRadius: 3,
          mb: 3,
          overflow: "hidden",
          border: `1px solid ${alpha(theme.palette.grey[300], 0.5)}`,
        }}
      >
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          sx={{
            "& .MuiTab-root": {
              textTransform: "none",
              fontWeight: 600,
              minHeight: 64,
              "&.Mui-selected": {
                color: theme.palette.primary.main,
              },
            },
            "& .MuiTabs-indicator": {
              height: 3,
              borderRadius: "3px 3px 0 0",
            },
          }}
        >
          <Tab
            label={
              <Badge badgeContent={filteredForms.length} color="primary">
                <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                  <ViewModule />
                  <Typography sx={{ fontWeight: "inherit" }}>
                    My Forms
                  </Typography>
                </Box>
              </Badge>
            }
          />
          <Tab
            label={
              <Badge badgeContent={externalForms.length} color="secondary">
                <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                  <Launch />
                  <Typography sx={{ fontWeight: "inherit" }}>
                    External Forms
                  </Typography>
                </Box>
              </Badge>
            }
          />
          <Tab
            label={
              <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
                <TrendingUp />
                <Typography sx={{ fontWeight: "inherit" }}>
                  Analytics
                </Typography>
              </Box>
            }
          />
        </Tabs>
      </Paper>

      {/* My Forms Tab */}
      <TabPanel value={tabValue} index={0}>
        {/* Search and Filter Controls */}
        <Paper
          sx={{
            p: 3,
            mb: 3,
            borderRadius: 3,
            border: `1px solid ${alpha(theme.palette.grey[300], 0.5)}`,
          }}
        >
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                placeholder="Search forms..."
                onChange={(e) => debouncedSearch(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <Search color="action" />
                    </InputAdornment>
                  ),
                  sx: { borderRadius: 2 },
                }}
              />
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>Sort by</InputLabel>
                <Select
                  value={sortBy}
                  label="Sort by"
                  onChange={handleSortChange}
                  sx={{ borderRadius: 2 }}
                >
                  <MenuItem value="created_at">Date Created</MenuItem>
                  <MenuItem value="updated_at">Last Updated</MenuItem>
                  <MenuItem value="title">Title</MenuItem>
                  <MenuItem value="submissions">Submissions</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={6} md={2}>
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={filterStatus}
                  label="Status"
                  onChange={handleStatusFilterChange}
                  sx={{ borderRadius: 2 }}
                >
                  <MenuItem value="all">All Forms</MenuItem>
                  <MenuItem value="active">Active</MenuItem>
                  <MenuItem value="inactive">Inactive</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={4}>
              <Box sx={{ display: "flex", justifyContent: "flex-end", gap: 1 }}>
                <ToggleButtonGroup
                  value={sortOrder}
                  exclusive
                  onChange={(_, value) => value && setSortOrder(value)}
                  size="small"
                >
                  <ToggleButton value="asc" aria-label="ascending">
                    <Sort sx={{ transform: "rotate(180deg)" }} />
                  </ToggleButton>
                  <ToggleButton value="desc" aria-label="descending">
                    <Sort />
                  </ToggleButton>
                </ToggleButtonGroup>

                <ToggleButtonGroup
                  value={viewMode}
                  exclusive
                  onChange={(_, value) => value && setViewMode(value)}
                  size="small"
                >
                  <ToggleButton value="grid" aria-label="grid view">
                    <GridView />
                  </ToggleButton>
                  <ToggleButton value="list" aria-label="list view">
                    <ViewStream />
                  </ToggleButton>
                </ToggleButtonGroup>
              </Box>
            </Grid>
          </Grid>
        </Paper>

        {/* Forms Content */}
        {formsLoading ? (
          <Grid container spacing={3}>
            {[...Array(6)].map((_, index) => (
              <Grid item xs={12} md={6} lg={4} key={index}>
                <Card sx={{ borderRadius: 4 }}>
                  <CardContent>
                    <Skeleton variant="text" width="80%" height={32} />
                    <Skeleton
                      variant="text"
                      width="100%"
                      height={20}
                      sx={{ mt: 1 }}
                    />
                    <Skeleton variant="text" width="60%" height={20} />
                    <Box sx={{ display: "flex", gap: 1, mt: 2 }}>
                      <Skeleton variant="rounded" width={80} height={24} />
                      <Skeleton variant="rounded" width={60} height={24} />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : formsError ? (
          <Alert severity="error" sx={{ borderRadius: 2 }}>
            Failed to load forms. Please try again.
          </Alert>
        ) : filteredForms.length === 0 ? (
          <Paper
            sx={{
              p: 6,
              textAlign: "center",
              borderRadius: 4,
              border: `2px dashed ${alpha(theme.palette.grey[400], 0.5)}`,
            }}
          >
            <Dashboard sx={{ fontSize: 80, color: "grey.400", mb: 2 }} />
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
              {searchQuery ? "No forms found" : "No Forms Created Yet"}
            </Typography>
            <Typography
              color="text.secondary"
              paragraph
              sx={{ maxWidth: 400, mx: "auto" }}
            >
              {searchQuery
                ? "Try adjusting your search terms or filters to find what you're looking for."
                : "Start building your first form to collect data from users. It's quick and easy!"}
            </Typography>
            {!searchQuery && (
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleNewForm}
                size="large"
                sx={{ borderRadius: 3, mt: 2 }}
              >
                Create Your First Form
              </Button>
            )}
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {filteredForms.map((form: Form) => (
              <Grid
                item
                xs={12}
                md={viewMode === "grid" ? 6 : 12}
                lg={viewMode === "grid" ? 4 : 12}
                key={form.id}
              >
                <FormCard
                  form={form}
                  onEdit={handleEditForm}
                  onDelete={handleDeleteForm}
                  onShare={handleShareForm}
                  onQRCode={handleQRCodeForm}
                  isHovered={hoveredFormId === form.id}
                  onHover={setHoveredFormId}
                />
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      {/* External Forms Tab */}
      <TabPanel value={tabValue} index={1}>
        <Box
          sx={{
            mb: 3,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <Typography variant="h5" sx={{ fontWeight: 600 }}>
            External Forms Collection
          </Typography>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setExternalFormDialogOpen(true)}
            sx={{ borderRadius: 3 }}
          >
            Add External Form
          </Button>
        </Box>

        {externalForms.length === 0 ? (
          <Paper
            sx={{
              p: 6,
              textAlign: "center",
              borderRadius: 4,
              border: `2px dashed ${alpha(theme.palette.grey[400], 0.5)}`,
            }}
          >
            <Launch sx={{ fontSize: 80, color: "grey.400", mb: 2 }} />
            <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
              No External Forms Stored
            </Typography>
            <Typography
              color="text.secondary"
              paragraph
              sx={{ maxWidth: 400, mx: "auto" }}
            >
              Store external form URLs with QR codes for easy access and
              sharing. Perfect for Google Forms and other external platforms.
            </Typography>
            <Button
              variant="contained"
              startIcon={<Add />}
              onClick={() => setExternalFormDialogOpen(true)}
              size="large"
              sx={{ borderRadius: 3, mt: 2 }}
            >
              Add Your First External Form
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {externalForms.map((form) => (
              <Grid item xs={12} md={6} lg={4} key={form.id}>
                <Card sx={{ borderRadius: 4, height: "100%" }}>
                  <CardContent>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                      {form.favicon && (
                        <Box
                          component="img"
                          src={form.favicon}
                          alt="favicon"
                          sx={{
                            width: 24,
                            height: 24,
                            marginRight: 1,
                            borderRadius: 1,
                          }}
                        />
                      )}
                      <Typography
                        variant="h6"
                        component="h2"
                        sx={{ flexGrow: 1, fontWeight: 600 }}
                      >
                        {form.title}
                      </Typography>
                      {form.isGoogleForm && (
                        <Chip
                          label="Google Form"
                          size="small"
                          color="primary"
                        />
                      )}
                    </Box>

                    {form.description && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        paragraph
                      >
                        {form.description}
                      </Typography>
                    )}

                    <TextField
                      fullWidth
                      size="small"
                      value={form.url}
                      InputProps={{
                        readOnly: true,
                        sx: { borderRadius: 2 },
                      }}
                      sx={{ mb: 2 }}
                    />

                    <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
                      <Chip
                        icon={<Visibility />}
                        label={`${form.submissions || 0} submissions`}
                        size="small"
                        variant="outlined"
                      />
                      <Chip
                        icon={<Schedule />}
                        label={`Updated ${new Date(
                          form.lastUpdated || form.createdAt
                        ).toLocaleDateString()}`}
                        size="small"
                        variant="outlined"
                      />
                    </Stack>

                    <Typography variant="caption" color="text.secondary">
                      Added: {new Date(form.createdAt).toLocaleDateString()}
                    </Typography>
                  </CardContent>

                  <CardActions sx={{ p: 2 }}>
                    <Button
                      size="small"
                      startIcon={<Launch />}
                      onClick={() => window.open(form.url, "_blank")}
                      sx={{ borderRadius: 2 }}
                    >
                      Open
                    </Button>
                    <Button
                      size="small"
                      startIcon={<QrCode />}
                      onClick={() => handleCopyToClipboard(form.url)}
                      sx={{ borderRadius: 2 }}
                    >
                      QR Code
                    </Button>
                    <Button
                      size="small"
                      startIcon={<ContentCopy />}
                      onClick={() => handleCopyToClipboard(form.url)}
                      sx={{ borderRadius: 2 }}
                    >
                      Copy Link
                    </Button>
                    <IconButton
                      size="small"
                      onClick={() => handleDeleteExternalForm(form.id)}
                      color="error"
                    >
                      <Delete />
                    </IconButton>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </TabPanel>

      {/* Analytics Tab */}
      <TabPanel value={tabValue} index={2}>
        <Typography variant="h5" gutterBottom sx={{ fontWeight: 600, mb: 3 }}>
          Form Analytics & Insights
        </Typography>

        {/* Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                borderRadius: 4,
                background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, ${theme.palette.primary.dark} 100%)`,
                color: "white",
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <Box>
                    <Typography
                      color="inherit"
                      variant="h4"
                      sx={{ fontWeight: 700 }}
                    >
                      {analyticsData.totalForms}
                    </Typography>
                    <Typography color="inherit" variant="body2">
                      Total Forms
                    </Typography>
                  </Box>
                  <ViewModule sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                borderRadius: 4,
                background: `linear-gradient(135deg, ${theme.palette.success.main} 0%, ${theme.palette.success.dark} 100%)`,
                color: "white",
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <Box>
                    <Typography
                      color="inherit"
                      variant="h4"
                      sx={{ fontWeight: 700 }}
                    >
                      {analyticsData.activeForms}
                    </Typography>
                    <Typography color="inherit" variant="body2">
                      Active Forms
                    </Typography>
                  </Box>
                  <CheckCircle sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                borderRadius: 4,
                background: `linear-gradient(135deg, ${theme.palette.secondary.main} 0%, ${theme.palette.secondary.dark} 100%)`,
                color: "white",
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <Box>
                    <Typography
                      color="inherit"
                      variant="h4"
                      sx={{ fontWeight: 700 }}
                    >
                      {analyticsData.totalSubmissions}
                    </Typography>
                    <Typography color="inherit" variant="body2">
                      Total Submissions
                    </Typography>
                  </Box>
                  <Group sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card
              sx={{
                borderRadius: 4,
                background: `linear-gradient(135deg, ${theme.palette.warning.main} 0%, ${theme.palette.warning.dark} 100%)`,
                color: "white",
              }}
            >
              <CardContent>
                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                  }}
                >
                  <Box>
                    <Typography
                      color="inherit"
                      variant="h4"
                      sx={{ fontWeight: 700 }}
                    >
                      {analyticsData.avgSubmissions}
                    </Typography>
                    <Typography color="inherit" variant="body2">
                      Avg. Submissions
                    </Typography>
                  </Box>
                  <TrendingUp sx={{ fontSize: 40, opacity: 0.8 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Charts */}
        {forms.length > 0 ? (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card sx={{ borderRadius: 4, p: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Form Submissions Overview
                </Typography>
                <Box sx={{ height: 300 }}>
                  <Bar
                    data={analyticsData.submissionChart}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          display: false,
                        },
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                        },
                      },
                    }}
                  />
                </Box>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card sx={{ borderRadius: 4, p: 3 }}>
                <Typography variant="h6" gutterBottom sx={{ fontWeight: 600 }}>
                  Form Status Distribution
                </Typography>
                <Box
                  sx={{
                    height: 300,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Doughnut
                    data={analyticsData.statusChart}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      plugins: {
                        legend: {
                          position: "bottom",
                        },
                      },
                    }}
                  />
                </Box>
              </Card>
            </Grid>
          </Grid>
        ) : (
          <Paper
            sx={{
              p: 6,
              textAlign: "center",
              borderRadius: 4,
              border: `2px dashed ${alpha(theme.palette.grey[400], 0.5)}`,
            }}
          >
            <Analytics sx={{ fontSize: 80, color: "grey.400", mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              No Analytics Data Available
            </Typography>
            <Typography color="text.secondary">
              Create some forms and collect submissions to see analytics here.
            </Typography>
          </Paper>
        )}
      </TabPanel>

      {/* QR Code Manager Dialog */}
      <Dialog
        open={!!selectedFormForQR}
        onClose={() => setSelectedFormForQR(null)}
        maxWidth="lg"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Box
            sx={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
            }}
          >
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              QR Code Manager: {selectedFormForQR?.title}
            </Typography>
            <IconButton onClick={() => setSelectedFormForQR(null)}>
              <Close />
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent sx={{ p: 0 }}>
          {selectedFormForQR && (
            <QRCodeManager
              formId={selectedFormForQR.id}
              formTitle={selectedFormForQR.title}
            />
          )}
        </DialogContent>
      </Dialog>

      {/* Share Dialog */}
      <Dialog
        open={shareDialogOpen}
        onClose={() => setShareDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <DialogTitle sx={{ pb: 1 }}>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Share Form: {selectedForm?.title}
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Share this form with others using the link below:
          </Typography>
          <TextField
            fullWidth
            value={shareUrl}
            InputProps={{
              readOnly: true,
              endAdornment: (
                <InputAdornment position="end">
                  <Tooltip title="Copy to clipboard">
                    <IconButton
                      onClick={() => handleCopyToClipboard(shareUrl)}
                      edge="end"
                    >
                      <ContentCopy />
                    </IconButton>
                  </Tooltip>
                </InputAdornment>
              ),
              sx: { borderRadius: 2 },
            }}
          />
        </DialogContent>
        <DialogActions sx={{ p: 3, pt: 1 }}>
          <Button
            onClick={() => setShareDialogOpen(false)}
            sx={{ borderRadius: 2 }}
          >
            Close
          </Button>
          <Button
            variant="contained"
            onClick={() => handleCopyToClipboard(shareUrl)}
            startIcon={<ContentCopy />}
            sx={{ borderRadius: 2 }}
          >
            Copy Link
          </Button>
        </DialogActions>
      </Dialog>

      {/* Add External Form Dialog */}
      <Dialog
        open={externalFormDialogOpen}
        onClose={() => setExternalFormDialogOpen(false)}
        maxWidth="sm"
        fullWidth
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <DialogTitle>
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            Add External Form
          </Typography>
        </DialogTitle>
        <DialogContent>
          <Stack spacing={3} sx={{ mt: 1 }}>
            <TextField
              fullWidth
              label="Form Title"
              value={newExternalForm.title}
              onChange={(e) =>
                setNewExternalForm((prev) => ({
                  ...prev,
                  title: e.target.value,
                }))
              }
              sx={{ "& .MuiOutlinedInput-root": { borderRadius: 2 } }}
            />
            <TextField
              fullWidth
              label="Form URL"
              value={newExternalForm.url}
              onChange={(e) =>
                setNewExternalForm((prev) => ({ ...prev, url: e.target.value }))
              }
              placeholder="https://forms.google.com/..."
              sx={{ "& .MuiOutlinedInput-root": { borderRadius: 2 } }}
            />
            <TextField
              fullWidth
              label="Description (Optional)"
              multiline
              rows={3}
              value={newExternalForm.description}
              onChange={(e) =>
                setNewExternalForm((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
              sx={{ "& .MuiOutlinedInput-root": { borderRadius: 2 } }}
            />
          </Stack>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button
            onClick={() => setExternalFormDialogOpen(false)}
            sx={{ borderRadius: 2 }}
          >
            Cancel
          </Button>
          <Button
            variant="contained"
            onClick={handleAddExternalForm}
            disabled={!newExternalForm.title || !newExternalForm.url}
            sx={{ borderRadius: 2 }}
          >
            Add Form
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmOpen}
        onClose={() => setDeleteConfirmOpen(false)}
        maxWidth="sm"
        PaperProps={{ sx: { borderRadius: 3 } }}
      >
        <DialogTitle>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
            <Warning color="error" />
            <Typography variant="h6" sx={{ fontWeight: 600 }}>
              Confirm Deletion
            </Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to delete "
            <strong>{selectedForm?.title}</strong>"? This action cannot be
            undone and all associated data will be permanently removed.
          </Typography>
        </DialogContent>
        <DialogActions sx={{ p: 3 }}>
          <Button
            onClick={() => setDeleteConfirmOpen(false)}
            variant="outlined"
            sx={{ borderRadius: 2 }}
          >
            Cancel
          </Button>
          <Button
            onClick={confirmDeleteForm}
            variant="contained"
            color="error"
            startIcon={<Delete />}
            sx={{ borderRadius: 2 }}
          >
            Delete Form
          </Button>
        </DialogActions>
      </Dialog>

      {/* Enhanced Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
      >
        <Alert
          onClose={() => setSnackbar((prev) => ({ ...prev, open: false }))}
          severity={snackbar.severity}
          action={snackbar.action}
          sx={{ borderRadius: 2 }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
}
