import React, { useState, useCallback } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Grid,
  Alert,
  CircularProgress,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Tab,
  Tabs,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
} from "@mui/material";
import {
  CloudUpload,
  TableChart,
  Description,
  AutoFixHigh,
  GetApp,
  Launch,
  QrCode,
  Analytics,
  CheckCircle,
  Schedule,
  Warning,
  Refresh,
} from "@mui/icons-material";
import { useDropzone } from "react-dropzone";
import { useMutation, useQuery } from "@tanstack/react-query";
import axios from "axios";

interface WorkflowStep {
  step: number;
  name: string;
  status: "completed" | "in_progress" | "ready" | "waiting" | "pending";
  description: string;
  action?: string;
  completion_date?: string;
  submissions_count?: number;
  last_submission?: string;
  action_url?: string;
}

interface WorkflowStatus {
  form_id: number;
  form_title: string;
  created_at: string;
  is_active: boolean;
  total_submissions: number;
  steps: WorkflowStep[];
  next_actions: Array<{
    action: string;
    url: string;
    description: string;
  }>;
}

interface AutomationResult {
  success: boolean;
  workflow_name?: string;
  form_id?: number;
  form_url?: string;
  form_schema?: any;
  detected_fields?: number;
  automation_steps?: WorkflowStep[];
  error?: string;
}

export default function FormAutomationDashboard() {
  const [activeTab, setActiveTab] = useState(0);
  const [uploadedTemplate, setUploadedTemplate] = useState<File | null>(null);
  const [workflowName, setWorkflowName] = useState("");
  const [selectedWorkflow, setSelectedWorkflow] = useState<number | null>(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // File upload handling
  const onDropTemplate = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        setUploadedTemplate(acceptedFiles[0]);
        if (!workflowName) {
          const name = acceptedFiles[0].name.replace(/\.[^/.]+$/, "");
          setWorkflowName(`Workflow - ${name}`);
        }
      }
    },
    [workflowName]
  );

  const {
    getRootProps: getTemplateRootProps,
    getInputProps: getTemplateInputProps,
    isDragActive: isTemplateDragActive,
  } = useDropzone({
    onDrop: onDropTemplate,
    accept: {
      "text/plain": [".tex"],
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        [".docx"],
    },
    multiple: false,
  });

  // API calls
  const createWorkflowMutation = useMutation({
    mutationFn: async (data: {
      template_file: File;
      workflow_name: string;
    }) => {
      const formData = new FormData();
      formData.append("template_file", data.template_file);
      formData.append("workflow_name", data.workflow_name);

      const response = await axios.post(
        "/api/forms/automation/create-workflow",
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
        }
      );
      return response.data;
    },
    onSuccess: (data: AutomationResult) => {
      if (data.success && data.form_id) {
        setSelectedWorkflow(data.form_id);
        setShowCreateDialog(false);
        setUploadedTemplate(null);
        setWorkflowName("");
      }
    },
  });

  const { data: workflowStatus, refetch: refetchWorkflowStatus } = useQuery({
    queryKey: ["workflow-status", selectedWorkflow],
    queryFn: async () => {
      if (!selectedWorkflow) return null;
      const response = await axios.get(
        `/api/forms/automation/workflow-status/${selectedWorkflow}`
      );
      return response.data as WorkflowStatus;
    },
    enabled: !!selectedWorkflow,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const exportToExcelMutation = useMutation({
    mutationFn: async (formId: number) => {
      const response = await axios.post(
        `/api/forms/automation/export-to-excel/${formId}`,
        {
          include_analytics: true,
        }
      );
      return response.data;
    },
    onSuccess: (data) => {
      if (data.success && data.download_url) {
        // Download the file
        window.open(data.download_url, "_blank");
        refetchWorkflowStatus();
      }
    },
  });

  const handleCreateWorkflow = () => {
    if (uploadedTemplate && workflowName) {
      createWorkflowMutation.mutate({
        template_file: uploadedTemplate,
        workflow_name: workflowName,
      });
    }
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case "completed":
        return <CheckCircle color="success" />;
      case "in_progress":
        return <CircularProgress size={24} />;
      case "ready":
        return <Schedule color="primary" />;
      case "waiting":
      case "pending":
        return <Warning color="warning" />;
      default:
        return <Schedule />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "success";
      case "in_progress":
        return "info";
      case "ready":
        return "primary";
      case "waiting":
      case "pending":
        return "warning";
      default:
        return "default";
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Form Automation Dashboard
      </Typography>
      <Typography variant="subtitle1" color="text.secondary" gutterBottom>
        Complete workflow: Template → Dynamic Form → Excel Export → Report
        Generation
      </Typography>

      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
        >
          <Tab label="Create Workflow" />
          <Tab label="Manage Workflows" />
          <Tab label="Analytics" />
        </Tabs>
      </Paper>

      {/* Tab 1: Create Workflow */}
      {activeTab === 0 && (
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Step 1: Upload Template
                </Typography>
                <Box
                  {...getTemplateRootProps()}
                  sx={{
                    border: "2px dashed #ccc",
                    borderRadius: 2,
                    p: 3,
                    textAlign: "center",
                    cursor: "pointer",
                    backgroundColor: isTemplateDragActive
                      ? "#f5f5f5"
                      : "transparent",
                    "&:hover": {
                      backgroundColor: "#f5f5f5",
                    },
                  }}
                >
                  <input {...getTemplateInputProps()} />
                  <CloudUpload sx={{ fontSize: 48, color: "#ccc", mb: 2 }} />
                  <Typography variant="body1" gutterBottom>
                    {uploadedTemplate
                      ? uploadedTemplate.name
                      : "Drop your template file here"}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Supports .tex and .docx files
                  </Typography>
                </Box>

                {uploadedTemplate && (
                  <Box sx={{ mt: 2 }}>
                    <TextField
                      fullWidth
                      label="Workflow Name"
                      value={workflowName}
                      onChange={(e) => setWorkflowName(e.target.value)}
                      placeholder="Enter a name for your automated workflow"
                    />
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Automation Process
                </Typography>
                <Stepper orientation="vertical">
                  <Step>
                    <StepLabel icon={<AutoFixHigh />}>
                      Template Analysis
                    </StepLabel>
                    <StepContent>
                      <Typography variant="body2">
                        Automatically detect form fields from template
                        placeholders
                      </Typography>
                    </StepContent>
                  </Step>
                  <Step>
                    <StepLabel icon={<Description />}>
                      Dynamic Form Creation
                    </StepLabel>
                    <StepContent>
                      <Typography variant="body2">
                        Generate smart form with appropriate field types
                      </Typography>
                    </StepContent>
                  </Step>
                  <Step>
                    <StepLabel icon={<TableChart />}>Excel Export</StepLabel>
                    <StepContent>
                      <Typography variant="body2">
                        Export collected data to formatted Excel with analytics
                      </Typography>
                    </StepContent>
                  </Step>
                  <Step>
                    <StepLabel icon={<GetApp />}>Report Generation</StepLabel>
                    <StepContent>
                      <Typography variant="body2">
                        Generate final report using template and collected data
                      </Typography>
                    </StepContent>
                  </Step>
                </Stepper>

                <Box sx={{ mt: 3 }}>
                  <Button
                    variant="contained"
                    size="large"
                    fullWidth
                    disabled={
                      !uploadedTemplate ||
                      !workflowName ||
                      createWorkflowMutation.isPending
                    }
                    onClick={handleCreateWorkflow}
                    startIcon={
                      createWorkflowMutation.isPending ? (
                        <CircularProgress size={20} />
                      ) : (
                        <AutoFixHigh />
                      )
                    }
                  >
                    {createWorkflowMutation.isPending
                      ? "Creating Workflow..."
                      : "Create Automated Workflow"}
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {createWorkflowMutation.data &&
            createWorkflowMutation.data.success && (
              <Grid item xs={12}>
                <Alert severity="success">
                  <Typography variant="h6">
                    Workflow Created Successfully!
                  </Typography>
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    Form "{createWorkflowMutation.data.workflow_name}" has been
                    created with {createWorkflowMutation.data.detected_fields}{" "}
                    detected fields.
                  </Typography>
                  <Box sx={{ mt: 2, display: "flex", gap: 1 }}>
                    <Button
                      size="small"
                      variant="outlined"
                      onClick={() =>
                        setSelectedWorkflow(
                          createWorkflowMutation.data.form_id!
                        )
                      }
                    >
                      View Workflow
                    </Button>
                    {createWorkflowMutation.data.form_url && (
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<Launch />}
                        onClick={() =>
                          window.open(
                            createWorkflowMutation.data.form_url,
                            "_blank"
                          )
                        }
                      >
                        Open Form
                      </Button>
                    )}
                  </Box>
                </Alert>
              </Grid>
            )}
        </Grid>
      )}

      {/* Tab 2: Manage Workflows */}
      {activeTab === 1 && (
        <Grid container spacing={3}>
          {selectedWorkflow && workflowStatus && (
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box
                    sx={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      mb: 2,
                    }}
                  >
                    <Typography variant="h6">
                      {workflowStatus.form_title}
                    </Typography>
                    <Box sx={{ display: "flex", gap: 1 }}>
                      <IconButton onClick={() => refetchWorkflowStatus()}>
                        <Refresh />
                      </IconButton>
                      <Chip
                        label={workflowStatus.is_active ? "Active" : "Inactive"}
                        color={workflowStatus.is_active ? "success" : "default"}
                        size="small"
                      />
                    </Box>
                  </Box>

                  <Typography
                    variant="body2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Created:{" "}
                    {new Date(workflowStatus.created_at).toLocaleDateString()} •
                    Total Submissions: {workflowStatus.total_submissions}
                  </Typography>

                  <Divider sx={{ my: 2 }} />

                  <Typography variant="h6" gutterBottom>
                    Workflow Progress
                  </Typography>

                  <Stepper orientation="vertical">
                    {workflowStatus.steps.map((step) => (
                      <Step
                        key={step.step}
                        active={true}
                        completed={step.status === "completed"}
                      >
                        <StepLabel icon={getStepIcon(step.status)}>
                          <Box
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              gap: 1,
                            }}
                          >
                            {step.name}
                            <Chip
                              label={step.status.replace("_", " ")}
                              size="small"
                              color={getStatusColor(step.status) as any}
                              variant="outlined"
                            />
                          </Box>
                        </StepLabel>
                        <StepContent>
                          <Typography variant="body2" gutterBottom>
                            {step.description}
                          </Typography>
                          {step.submissions_count !== undefined && (
                            <Typography variant="body2" color="text.secondary">
                              Submissions: {step.submissions_count}
                            </Typography>
                          )}
                          {step.last_submission && (
                            <Typography variant="body2" color="text.secondary">
                              Last submission:{" "}
                              {new Date(step.last_submission).toLocaleString()}
                            </Typography>
                          )}
                          {step.action_url && step.status === "ready" && (
                            <Box sx={{ mt: 1 }}>
                              {step.step === 3 && (
                                <Button
                                  size="small"
                                  variant="contained"
                                  startIcon={<TableChart />}
                                  onClick={() =>
                                    exportToExcelMutation.mutate(
                                      workflowStatus.form_id
                                    )
                                  }
                                  disabled={exportToExcelMutation.isPending}
                                >
                                  {exportToExcelMutation.isPending
                                    ? "Exporting..."
                                    : "Export to Excel"}
                                </Button>
                              )}
                            </Box>
                          )}
                        </StepContent>
                      </Step>
                    ))}
                  </Stepper>

                  {workflowStatus.next_actions.length > 0 && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="h6" gutterBottom>
                        Next Actions
                      </Typography>
                      <List>
                        {workflowStatus.next_actions.map((action, index) => (
                          <ListItem key={index}>
                            <ListItemIcon>
                              {action.action.includes("Share") ? (
                                <QrCode />
                              ) : (
                                <Analytics />
                              )}
                            </ListItemIcon>
                            <ListItemText
                              primary={action.action}
                              secondary={action.description}
                            />
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={() => window.open(action.url, "_blank")}
                              startIcon={<Launch />}
                            >
                              Open
                            </Button>
                          </ListItem>
                        ))}
                      </List>
                    </>
                  )}
                </CardContent>
              </Card>
            </Grid>
          )}

          {!selectedWorkflow && (
            <Grid item xs={12}>
              <Card>
                <CardContent sx={{ textAlign: "center", py: 6 }}>
                  <AutoFixHigh sx={{ fontSize: 64, color: "#ccc", mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    No Workflow Selected
                  </Typography>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Create a new workflow or select an existing one to view
                    progress
                  </Typography>
                  <Button
                    variant="contained"
                    onClick={() => setActiveTab(0)}
                    sx={{ mt: 2 }}
                  >
                    Create New Workflow
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          )}
        </Grid>
      )}

      {/* Tab 3: Analytics */}
      {activeTab === 2 && (
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Card>
              <CardContent sx={{ textAlign: "center", py: 6 }}>
                <Analytics sx={{ fontSize: 64, color: "#ccc", mb: 2 }} />
                <Typography variant="h6" gutterBottom>
                  Analytics Dashboard
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Detailed analytics and insights will be displayed here
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Error display */}
      {createWorkflowMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {createWorkflowMutation.error?.message || "Failed to create workflow"}
        </Alert>
      )}

      {exportToExcelMutation.isError && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {exportToExcelMutation.error?.message || "Failed to export to Excel"}
        </Alert>
      )}
    </Box>
  );
}
