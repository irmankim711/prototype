import React from "react";
import { useState } from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Chip,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Tooltip,
  Divider,
} from "@mui/material";
import {
  Download,
  Preview,
  Email,
  Refresh,
  Schedule,
  Assessment,
  CheckCircle,
  Error,
  Pending,
} from "@mui/icons-material";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { reportService } from "../services/reportService";
import type {
  Report,
  ReportStatus,
  ReportGenerationRequest,
} from "../types/reports";
import ReportPreview from "./ReportPreview";
import ReportEditor from "./ReportEditor";

interface ReportDashboardProps {
  formId?: string;
}

const ReportDashboard: React.FC<ReportDashboardProps> = ({ formId }) => {
  const [selectedReport, setSelectedReport] = useState<Report | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch reports
  const {
    data: reports,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["reports", formId],
    queryFn: () =>
      formId
        ? reportService.getFormReports(formId)
        : reportService.getAllReports(),
    refetchInterval: 5000, // Poll every 5 seconds for status updates
  });

  // Generate report mutation
  const generateReportMutation = useMutation({
    mutationFn: (request: ReportGenerationRequest) =>
      reportService.generateReport(request),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
    },
  });

  // Download report mutation
  const downloadMutation = useMutation({
    mutationFn: (reportId: string) => reportService.downloadReport(reportId),
    onSuccess: (blob: Blob, reportId: string) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.style.display = "none";
      a.href = url;
      a.download = `report-${reportId}.docx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    },
  });

  // Email report mutation
  const emailMutation = useMutation({
    mutationFn: ({
      reportId,
      emails,
    }: {
      reportId: string;
      emails: string[];
    }) => reportService.emailReport(reportId, emails),
    onSuccess: () => {
      alert("Report sent successfully!");
    },
  });

  const getStatusIcon = (status: ReportStatus) => {
    switch (status) {
      case "completed":
        return <CheckCircle color="success" />;
      case "failed":
        return <Error color="error" />;
      case "generating":
        return <Pending color="warning" />;
      default:
        return <Schedule color="info" />;
    }
  };

  const getStatusColor = (status: ReportStatus) => {
    switch (status) {
      case "completed":
        return "success";
      case "failed":
        return "error";
      case "generating":
        return "warning";
      default:
        return "info";
    }
  };

  const handleGenerateReport = (formId: string) => {
    generateReportMutation.mutate({ formId, title: `Report for ${formId}` });
  };

  const handlePreviewReport = (report: Report) => {
    setSelectedReport(report);
    setPreviewOpen(true);
  };

  const handleEditReport = (report: Report) => {
    setSelectedReport(report);
    setEditorOpen(true);
  };

  const handleDownload = (reportId: string) => {
    downloadMutation.mutate(reportId);
  };

  const handleEmail = (reportId: string) => {
    const emails = prompt("Enter email addresses (comma-separated):");
    if (emails) {
      const emailList = emails.split(",").map((email: any) => email.trim());
      emailMutation.mutate({ reportId, emails: emailList });
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" gutterBottom>
          <Assessment sx={{ mr: 1, verticalAlign: "middle" }} />
          Report Dashboard
        </Typography>
        <LinearProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Failed to load reports. Please try again.
        </Alert>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Box
        sx={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          mb: 3,
        }}
      >
        <Typography variant="h4">
          <Assessment sx={{ mr: 1, verticalAlign: "middle" }} />
          Report Dashboard
        </Typography>
        <Button
          variant="contained"
          startIcon={<Refresh />}
          onClick={() =>
            queryClient.invalidateQueries({ queryKey: ["reports"] })
          }
        >
          Refresh
        </Button>
      </Box>

      {reports && reports.length === 0 ? (
        <Card>
          <CardContent sx={{ textAlign: "center", py: 6 }}>
            <Assessment sx={{ fontSize: 64, color: "text.secondary", mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No reports available
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Reports will be automatically generated when forms receive
              submissions.
            </Typography>
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={3}>
          {reports?.map((report: Report) => (
            <Grid item xs={12} md={6} lg={4} key={report.id}>
              <Card
                sx={{
                  height: "100%",
                  display: "flex",
                  flexDirection: "column",
                  position: "relative",
                }}
              >
                <CardContent sx={{ flex: 1 }}>
                  <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                    {getStatusIcon(report.status)}
                    <Typography variant="h6" sx={{ ml: 1, flex: 1 }}>
                      {report.title}
                    </Typography>
                    <Chip
                      label={report.status}
                      color={getStatusColor(report.status)}
                      size="small"
                    />
                  </Box>

                  <Typography
                    variant="body2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Form: {report.formTitle}
                  </Typography>

                  <Typography
                    variant="body2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Submissions: {report.submissionCount}
                  </Typography>

                  <Typography
                    variant="body2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Generated: {new Date(report.createdAt).toLocaleDateString()}
                  </Typography>

                  {report.status === "generating" && (
                    <Box sx={{ mt: 2 }}>
                      <LinearProgress />
                      <Typography
                        variant="caption"
                        color="text.secondary"
                        sx={{ mt: 1 }}
                      >
                        Generating report...
                      </Typography>
                    </Box>
                  )}

                  {report.aiInsights && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        AI Insights Preview:
                      </Typography>
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          display: "-webkit-box",
                          WebkitLineClamp: 3,
                          WebkitBoxOrient: "vertical",
                        }}
                      >
                        {report.aiInsights.summary}
                      </Typography>
                    </>
                  )}
                </CardContent>

                <Box sx={{ p: 2, pt: 0 }}>
                  <Grid container spacing={1}>
                    {report.status === "completed" && (
                      <>
                        <Grid item xs={6}>
                          <Tooltip title="Preview Report">
                            <IconButton
                              size="small"
                              onClick={() => handlePreviewReport(report)}
                              color="primary"
                            >
                              <Preview />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Edit Report">
                            <IconButton
                              size="small"
                              onClick={() => handleEditReport(report)}
                              color="primary"
                            >
                              <Assessment />
                            </IconButton>
                          </Tooltip>
                        </Grid>
                        <Grid item xs={6} sx={{ textAlign: "right" }}>
                          <Tooltip title="Download Report">
                            <IconButton
                              size="small"
                              onClick={() => handleDownload(report.id)}
                              color="success"
                              disabled={downloadMutation.isPending}
                            >
                              <Download />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Email Report">
                            <IconButton
                              size="small"
                              onClick={() => handleEmail(report.id)}
                              color="info"
                              disabled={emailMutation.isPending}
                            >
                              <Email />
                            </IconButton>
                          </Tooltip>
                        </Grid>
                      </>
                    )}
                    {report.status === "failed" && (
                      <Grid item xs={12}>
                        <Button
                          size="small"
                          variant="outlined"
                          startIcon={<Refresh />}
                          onClick={() => handleGenerateReport(report.formId)}
                          disabled={generateReportMutation.isPending}
                          fullWidth
                        >
                          Retry Generation
                        </Button>
                      </Grid>
                    )}
                  </Grid>
                </Box>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Report Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogTitle>
          Report Preview
          <IconButton
            onClick={() => setPreviewOpen(false)}
            sx={{ position: "absolute", right: 8, top: 8 }}
          >
            ×
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedReport && <ReportPreview report={selectedReport} />}
        </DialogContent>
      </Dialog>

      {/* Report Editor Dialog */}
      <Dialog
        open={editorOpen}
        onClose={() => setEditorOpen(false)}
        maxWidth="xl"
        fullWidth
      >
        <DialogTitle>
          Edit Report
          <IconButton
            onClick={() => setEditorOpen(false)}
            sx={{ position: "absolute", right: 8, top: 8 }}
          >
            ×
          </IconButton>
        </DialogTitle>
        <DialogContent>
          {selectedReport && (
            <ReportEditor
              report={selectedReport}
              onSave={(updatedReport: Report) => {
                queryClient.setQueryData(
                  ["reports"],
                  (old: Report[] | undefined) =>
                    old?.map((r: any) =>
                      r.id === updatedReport.id ? updatedReport : r
                    )
                );
                setEditorOpen(false);
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </Box>
  );
};

export default ReportDashboard;
