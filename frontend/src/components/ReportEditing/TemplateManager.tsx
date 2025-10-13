/**
 * Template Management Component for Report Builder
 * Allows creation, selection, and application of report templates
 */

import React from "react";
import { useState, useEffect } from "react";
import {
  Box,
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Grid,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  FormControlLabel,
  Switch,
  Avatar,
  Tooltip,
  Menu,
  MenuItem,
} from "@mui/material";
import {
  Add,
  Palette,
  Visibility,
  MoreVert,
  Star,
  StarBorder,
  Download,
  Share,
  Edit,
  Delete,
  Public,
  Lock,
} from "@mui/icons-material";
import enhancedReportService from "../../services/enhancedReportService";
import type { ReportTemplate } from "../../services/enhancedReportService";

interface TemplateManagerProps {
  onTemplateSelect?: (template: ReportTemplate) => void;
  onTemplateApply?: (template: ReportTemplate) => void;
  showCreateTemplate?: boolean;
  reportId?: number;
}

interface TemplateFormData {
  name: string;
  description: string;
  layoutConfig: any;
  styleConfig: any;
  isPublic: boolean;
}

const defaultLayoutConfig = {
  header: {
    enabled: true,
    height: "80px",
    backgroundColor: "#f5f5f5",
    alignment: "center",
  },
  body: {
    margins: "20px",
    columnCount: 1,
    spacing: "16px",
  },
  footer: {
    enabled: true,
    height: "60px",
    content: "Generated on {date}",
  },
};

const defaultStyleConfig = {
  fonts: {
    primary: "Arial, sans-serif",
    heading: "Arial, sans-serif",
    body: "Arial, sans-serif",
  },
  colors: {
    primary: "#1976d2",
    secondary: "#757575",
    text: "#333333",
    background: "#ffffff",
  },
  spacing: {
    small: "8px",
    medium: "16px",
    large: "24px",
  },
};

const TemplateManager: React.FC<TemplateManagerProps> = ({
  onTemplateSelect,
  onTemplateApply,
  showCreateTemplate = true,
  reportId,
}) => {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTemplate, setSelectedTemplate] =
    useState<ReportTemplate | null>(null);

  // Create template dialog
  const [createDialog, setCreateDialog] = useState(false);
  const [templateForm, setTemplateForm] = useState<TemplateFormData>({
    name: "",
    description: "",
    layoutConfig: defaultLayoutConfig,
    styleConfig: defaultStyleConfig,
    isPublic: false,
  });
  const [creating, setCreating] = useState(false);

  // Template actions menu
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [menuTemplate, setMenuTemplate] = useState<ReportTemplate | null>(null);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedTemplates = await enhancedReportService.getTemplates();
      setTemplates(fetchedTemplates);
    } catch (err) {
      console.error("Failed to fetch templates:", err);
      setError("Failed to load templates");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = async () => {
    if (!templateForm.name.trim()) {
      setError("Template name is required");
      return;
    }

    setCreating(true);
    try {
      const newTemplate = await enhancedReportService.createTemplate(
        templateForm.name,
        templateForm.layoutConfig,
        templateForm.description,
        templateForm.styleConfig,
        templateForm.isPublic
      );

      setTemplates((prev: any) => [newTemplate, ...prev]);
      setCreateDialog(false);
      setTemplateForm({
        name: "",
        description: "",
        layoutConfig: defaultLayoutConfig,
        styleConfig: defaultStyleConfig,
        isPublic: false,
      });
      setError(null);
    } catch (err) {
      console.error("Failed to create template:", err);
      setError("Failed to create template");
    } finally {
      setCreating(false);
    }
  };

  const handleApplyTemplate = async (template: ReportTemplate) => {
    if (!reportId) {
      onTemplateSelect?.(template);
      return;
    }

    try {
      await enhancedReportService.applyTemplate(reportId, template.id);
      onTemplateApply?.(template);
    } catch (err) {
      console.error("Failed to apply template:", err);
      setError("Failed to apply template");
    }
  };

  const handleMenuOpen = (
    event: React.MouseEvent<HTMLElement>,
    template: ReportTemplate
  ) => {
    setAnchorEl(event.currentTarget);
    setMenuTemplate(template);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    setMenuTemplate(null);
  };

  const getTemplatePreviewStyle = (template: ReportTemplate) => {
    const style = template.style_config || defaultStyleConfig;
    return {
      backgroundColor: style.colors?.background || "#ffffff",
      borderColor: style.colors?.primary || "#1976d2",
      color: style.colors?.text || "#333333",
    };
  };

  if (loading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        minHeight="200px"
      >
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box
        sx={{
          mb: 3,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography
          variant="h6"
          component="h2"
          sx={{ display: "flex", alignItems: "center", gap: 1 }}
        >
          <Palette />
          Report Templates ({templates.length})
        </Typography>

        {showCreateTemplate && (
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => setCreateDialog(true)}
          >
            Create Template
          </Button>
        )}
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Templates Grid */}
      <Grid container spacing={3}>
        {templates.map((template: any) => (
          <Grid item xs={12} sm={6} md={4} key={template.id}>
            <Card
              sx={{
                height: "100%",
                display: "flex",
                flexDirection: "column",
                border: selectedTemplate?.id === template.id ? 2 : 1,
                borderColor:
                  selectedTemplate?.id === template.id
                    ? "primary.main"
                    : "grey.300",
                cursor: "pointer",
                transition: "all 0.2s",
                "&:hover": {
                  elevation: 4,
                  transform: "translateY(-2px)",
                },
                ...getTemplatePreviewStyle(template),
              }}
              onClick={() => setSelectedTemplate(template)}
            >
              {/* Template Preview */}
              <Box
                sx={{
                  height: 120,
                  background: `linear-gradient(135deg, ${
                    template.style_config?.colors?.primary || "#1976d2"
                  } 0%, ${
                    template.style_config?.colors?.secondary || "#757575"
                  } 100%)`,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "white",
                  position: "relative",
                }}
              >
                <Typography variant="h6" sx={{ textAlign: "center" }}>
                  {template.name}
                </Typography>

                {/* Template Actions Menu */}
                <IconButton
                  size="small"
                  sx={{
                    position: "absolute",
                    top: 8,
                    right: 8,
                    color: "white",
                  }}
                  onClick={(e: any) => {
                    e.stopPropagation();
                    handleMenuOpen(e, template);
                  }}
                >
                  <MoreVert />
                </IconButton>
              </Box>

              <CardContent sx={{ flexGrow: 1 }}>
                <Box
                  sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}
                >
                  <Typography variant="h6" component="h3" noWrap>
                    {template.name}
                  </Typography>

                  {template.is_public ? (
                    <Tooltip title="Public template">
                      <Public fontSize="small" color="action" />
                    </Tooltip>
                  ) : (
                    <Tooltip title="Private template">
                      <Lock fontSize="small" color="action" />
                    </Tooltip>
                  )}
                </Box>

                {template.description && (
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    sx={{
                      display: "-webkit-box",
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: "vertical",
                      overflow: "hidden",
                      mb: 2,
                    }}
                  >
                    {template.description}
                  </Typography>
                )}

                <Box
                  sx={{
                    display: "flex",
                    alignItems: "center",
                    gap: 1,
                    flexWrap: "wrap",
                  }}
                >
                  <Chip
                    label={`Used ${template.usage_count} times`}
                    size="small"
                    variant="outlined"
                  />

                  {template.creator_name && (
                    <Chip
                      avatar={
                        <Avatar sx={{ width: 20, height: 20 }}>
                          {template.creator_name[0]}
                        </Avatar>
                      }
                      label={template.creator_name}
                      size="small"
                      variant="outlined"
                    />
                  )}
                </Box>
              </CardContent>

              <CardActions>
                <Button
                  size="small"
                  startIcon={<Visibility />}
                  onClick={(e: any) => {
                    e.stopPropagation();
                    onTemplateSelect?.(template);
                  }}
                >
                  Preview
                </Button>

                <Button
                  size="small"
                  variant="contained"
                  onClick={(e: any) => {
                    e.stopPropagation();
                    handleApplyTemplate(template);
                  }}
                >
                  {reportId ? "Apply" : "Use"}
                </Button>
              </CardActions>
            </Card>
          </Grid>
        ))}

        {/* Empty State */}
        {templates.length === 0 && (
          <Grid item xs={12}>
            <Card sx={{ textAlign: "center", py: 4 }}>
              <CardContent>
                <Palette
                  sx={{ fontSize: 48, color: "text.secondary", mb: 2 }}
                />
                <Typography variant="h6" gutterBottom>
                  No Templates Available
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2 }}
                >
                  Create your first template to get started with consistent
                  report formatting.
                </Typography>
                {showCreateTemplate && (
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setCreateDialog(true)}
                  >
                    Create Your First Template
                  </Button>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Template Actions Menu */}
      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem onClick={handleMenuClose}>
          <Visibility sx={{ mr: 1 }} />
          Preview
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Star sx={{ mr: 1 }} />
          Add to Favorites
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Share sx={{ mr: 1 }} />
          Share Template
        </MenuItem>
        <MenuItem onClick={handleMenuClose}>
          <Download sx={{ mr: 1 }} />
          Export Template
        </MenuItem>
        {menuTemplate?.created_by && (
          <>
            <MenuItem onClick={handleMenuClose}>
              <Edit sx={{ mr: 1 }} />
              Edit Template
            </MenuItem>
            <MenuItem onClick={handleMenuClose} sx={{ color: "error.main" }}>
              <Delete sx={{ mr: 1 }} />
              Delete Template
            </MenuItem>
          </>
        )}
      </Menu>

      {/* Create Template Dialog */}
      <Dialog
        open={createDialog}
        onClose={() => setCreateDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Create New Template</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              autoFocus
              margin="dense"
              label="Template Name"
              fullWidth
              variant="outlined"
              value={templateForm.name}
              onChange={(e: any) =>
                setTemplateForm((prev: any) => ({ ...prev, name: e.target.value }))
              }
              sx={{ mb: 2 }}
            />

            <TextField
              margin="dense"
              label="Description (Optional)"
              fullWidth
              multiline
              rows={3}
              variant="outlined"
              value={templateForm.description}
              onChange={(e: any) =>
                setTemplateForm((prev: any) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
              sx={{ mb: 2 }}
            />

            <FormControlLabel
              control={
                <Switch
                  checked={templateForm.isPublic}
                  onChange={(e: any) =>
                    setTemplateForm((prev: any) => ({
                      ...prev,
                      isPublic: e.target.checked,
                    }))
                  }
                />
              }
              label="Make this template public"
            />

            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Public templates can be used by other users in your organization.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialog(false)}>Cancel</Button>
          <Button
            onClick={handleCreateTemplate}
            variant="contained"
            disabled={creating || !templateForm.name.trim()}
            startIcon={creating ? <CircularProgress size={16} /> : <Add />}
          >
            Create Template
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TemplateManager;
