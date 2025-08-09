import React from "react";
import { useState } from "react";
import {
  Box,
  Typography,
  TextField,
  Button,
  Card,
  CardContent,
  Grid,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Paper,
  Alert,
  CircularProgress,
} from "@mui/material";
import {
  Save,
  Cancel,
  Add,
  Delete,
  Edit,
  TrendingUp,
  Recommend,
  Assessment,
} from "@mui/icons-material";
import { useMutation } from "@tanstack/react-query";
import { reportService } from "../services/reportService";
import type { Report, ReportUpdateRequest } from "../types/reports";

interface ReportEditorProps {
  report: Report;
  onSave: (updatedReport: Report) => void;
  onCancel?: () => void;
}

const ReportEditor: React.FC<ReportEditorProps> = ({
  report,
  onSave,
  onCancel,
}) => {
  const [editedReport, setEditedReport] = useState<Report>({ ...report });
  const [editingTrend, setEditingTrend] = useState<number | null>(null);
  const [editingRecommendation, setEditingRecommendation] = useState<
    number | null
  >(null);
  const [newTrend, setNewTrend] = useState("");
  const [newRecommendation, setNewRecommendation] = useState("");

  const updateMutation = useMutation({
    mutationFn: (update: ReportUpdateRequest) =>
      reportService.updateReport(report.id, update),
    onSuccess: (updatedReport: any) => {
      onSave(updatedReport);
    },
  });

  const handleSave = () => {
    const update: ReportUpdateRequest = {
      title: editedReport.title,
      aiInsights: editedReport.aiInsights,
    };
    updateMutation.mutate(update);
  };

  const handleTitleChange = (value: string) => {
    setEditedReport((prev: any) => ({ ...prev, title: value }));
  };

  const handleSummaryChange = (value: string) => {
    setEditedReport((prev: any) => ({
      ...prev,
      aiInsights: prev.aiInsights
        ? {
            ...prev.aiInsights,
            summary: value,
          }
        : {
            summary: value,
            trends: [],
            recommendations: [],
            keyMetrics: {},
          },
    }));
  };

  const handleAddTrend = () => {
    if (newTrend.trim()) {
      setEditedReport((prev: any) => ({
        ...prev,
        aiInsights: prev.aiInsights
          ? {
              ...prev.aiInsights,
              trends: [...prev.aiInsights.trends, newTrend.trim()],
            }
          : {
              summary: "",
              trends: [newTrend.trim()],
              recommendations: [],
              keyMetrics: {},
            },
      }));
      setNewTrend("");
    }
  };

  const handleEditTrend = (index: number, value: string) => {
    if (!editedReport.aiInsights) return;

    const updatedTrends = [...editedReport.aiInsights.trends];
    updatedTrends[index] = value;

    setEditedReport((prev: any) => ({
      ...prev,
      aiInsights: prev.aiInsights
        ? {
            ...prev.aiInsights,
            trends: updatedTrends,
          }
        : {
            summary: "",
            trends: updatedTrends,
            recommendations: [],
            keyMetrics: {},
          },
    }));
  };

  const handleDeleteTrend = (index: number) => {
    if (!editedReport.aiInsights) return;

    const updatedTrends = editedReport.aiInsights.trends.filter(
      (_, i) => i !== index
    );

    setEditedReport((prev: any) => ({
      ...prev,
      aiInsights: prev.aiInsights
        ? {
            ...prev.aiInsights,
            trends: updatedTrends,
          }
        : {
            summary: "",
            trends: updatedTrends,
            recommendations: [],
            keyMetrics: {},
          },
    }));
  };

  const handleAddRecommendation = () => {
    if (newRecommendation.trim()) {
      setEditedReport((prev: any) => ({
        ...prev,
        aiInsights: prev.aiInsights
          ? {
              ...prev.aiInsights,
              recommendations: [
                ...prev.aiInsights.recommendations,
                newRecommendation.trim(),
              ],
            }
          : {
              summary: "",
              trends: [],
              recommendations: [newRecommendation.trim()],
              keyMetrics: {},
            },
      }));
      setNewRecommendation("");
    }
  };

  const handleEditRecommendation = (index: number, value: string) => {
    if (!editedReport.aiInsights) return;

    const updatedRecommendations = [...editedReport.aiInsights.recommendations];
    updatedRecommendations[index] = value;

    setEditedReport((prev: any) => ({
      ...prev,
      aiInsights: prev.aiInsights
        ? {
            ...prev.aiInsights,
            recommendations: updatedRecommendations,
          }
        : {
            summary: "",
            trends: [],
            recommendations: updatedRecommendations,
            keyMetrics: {},
          },
    }));
  };

  const handleDeleteRecommendation = (index: number) => {
    if (!editedReport.aiInsights) return;

    const updatedRecommendations =
      editedReport.aiInsights.recommendations.filter((_, i) => i !== index);

    setEditedReport((prev: any) => ({
      ...prev,
      aiInsights: prev.aiInsights
        ? {
            ...prev.aiInsights,
            recommendations: updatedRecommendations,
          }
        : {
            summary: "",
            trends: [],
            recommendations: updatedRecommendations,
            keyMetrics: {},
          },
    }));
  };

  return (
    <Box sx={{ p: 2 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Edit Report
        </Typography>
        <Box sx={{ display: "flex", gap: 1, mb: 2 }}>
          <Chip label={`Form: ${report.formTitle}`} variant="outlined" />
          <Chip
            label={`${report.submissionCount} submissions`}
            variant="outlined"
          />
        </Box>
      </Box>

      {/* Report Title */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Report Title
          </Typography>
          <TextField
            fullWidth
            value={editedReport.title}
            onChange={(e: any) => handleTitleChange(e.target.value)}
            placeholder="Enter report title"
            variant="outlined"
          />
        </CardContent>
      </Card>

      {/* AI Insights Editing */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography
            variant="h6"
            gutterBottom
            sx={{ display: "flex", alignItems: "center", gap: 1 }}
          >
            <Assessment color="primary" />
            AI Analysis
          </Typography>

          {/* Summary */}
          <Box sx={{ mb: 3 }}>
            <Typography variant="subtitle1" gutterBottom>
              Summary
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              value={editedReport.aiInsights?.summary || ""}
              onChange={(e: any) => handleSummaryChange(e.target.value)}
              placeholder="Enter analysis summary"
              variant="outlined"
            />
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Trends */}
          <Box sx={{ mb: 3 }}>
            <Typography
              variant="subtitle1"
              gutterBottom
              sx={{ display: "flex", alignItems: "center", gap: 1 }}
            >
              <TrendingUp color="success" />
              Trends
            </Typography>

            <List>
              {editedReport.aiInsights?.trends.map((trend, index) => (
                <ListItem key={index} sx={{ px: 0 }}>
                  {editingTrend === index ? (
                    <Box sx={{ display: "flex", width: "100%", gap: 1 }}>
                      <TextField
                        fullWidth
                        value={trend}
                        onChange={(e: any) => handleEditTrend(index, e.target.value)}
                        onBlur={() => setEditingTrend(null)}
                        onKeyPress={(e: any) => {
                          if (e.key === "Enter") {
                            setEditingTrend(null);
                          }
                        }}
                        autoFocus
                      />
                    </Box>
                  ) : (
                    <>
                      <ListItemIcon>
                        <TrendingUp fontSize="small" color="success" />
                      </ListItemIcon>
                      <ListItemText primary={trend} />
                      <IconButton
                        onClick={() => setEditingTrend(index)}
                        size="small"
                      >
                        <Edit fontSize="small" />
                      </IconButton>
                      <IconButton
                        onClick={() => handleDeleteTrend(index)}
                        size="small"
                        color="error"
                      >
                        <Delete fontSize="small" />
                      </IconButton>
                    </>
                  )}
                </ListItem>
              ))}
            </List>

            <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
              <TextField
                fullWidth
                size="small"
                value={newTrend}
                onChange={(e: any) => setNewTrend(e.target.value)}
                placeholder="Add new trend"
                onKeyPress={(e: any) => {
                  if (e.key === "Enter") {
                    handleAddTrend();
                  }
                }}
              />
              <Button
                variant="outlined"
                onClick={handleAddTrend}
                startIcon={<Add />}
                disabled={!newTrend.trim()}
              >
                Add
              </Button>
            </Box>
          </Box>

          <Divider sx={{ my: 2 }} />

          {/* Recommendations */}
          <Box>
            <Typography
              variant="subtitle1"
              gutterBottom
              sx={{ display: "flex", alignItems: "center", gap: 1 }}
            >
              <Recommend color="info" />
              Recommendations
            </Typography>

            <List>
              {editedReport.aiInsights?.recommendations.map(
                (recommendation, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    {editingRecommendation === index ? (
                      <Box sx={{ display: "flex", width: "100%", gap: 1 }}>
                        <TextField
                          fullWidth
                          value={recommendation}
                          onChange={(e: any) =>
                            handleEditRecommendation(index, e.target.value)
                          }
                          onBlur={() => setEditingRecommendation(null)}
                          onKeyPress={(e: any) => {
                            if (e.key === "Enter") {
                              setEditingRecommendation(null);
                            }
                          }}
                          autoFocus
                        />
                      </Box>
                    ) : (
                      <>
                        <ListItemIcon>
                          <Recommend fontSize="small" color="info" />
                        </ListItemIcon>
                        <ListItemText primary={recommendation} />
                        <IconButton
                          onClick={() => setEditingRecommendation(index)}
                          size="small"
                        >
                          <Edit fontSize="small" />
                        </IconButton>
                        <IconButton
                          onClick={() => handleDeleteRecommendation(index)}
                          size="small"
                          color="error"
                        >
                          <Delete fontSize="small" />
                        </IconButton>
                      </>
                    )}
                  </ListItem>
                )
              )}
            </List>

            <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
              <TextField
                fullWidth
                size="small"
                value={newRecommendation}
                onChange={(e: any) => setNewRecommendation(e.target.value)}
                placeholder="Add new recommendation"
                onKeyPress={(e: any) => {
                  if (e.key === "Enter") {
                    handleAddRecommendation();
                  }
                }}
              />
              <Button
                variant="outlined"
                onClick={handleAddRecommendation}
                startIcon={<Add />}
                disabled={!newRecommendation.trim()}
              >
                Add
              </Button>
            </Box>
          </Box>
        </CardContent>
      </Card>

      {/* Error Display */}
      {updateMutation.isError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to save changes. Please try again.
        </Alert>
      )}

      {/* Action Buttons */}
      <Box sx={{ display: "flex", gap: 2, justifyContent: "flex-end" }}>
        {onCancel && (
          <Button
            variant="outlined"
            startIcon={<Cancel />}
            onClick={onCancel}
            disabled={updateMutation.isPending}
          >
            Cancel
          </Button>
        )}
        <Button
          variant="contained"
          startIcon={
            updateMutation.isPending ? <CircularProgress size={20} /> : <Save />
          }
          onClick={handleSave}
          disabled={updateMutation.isPending}
        >
          {updateMutation.isPending ? "Saving..." : "Save Changes"}
        </Button>
      </Box>
    </Box>
  );
};

export default ReportEditor;
