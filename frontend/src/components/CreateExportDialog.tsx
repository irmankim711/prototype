/**
 * Create Export Dialog Component
 */

import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Box,
  Alert,
  Typography,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  Chip,
} from "@mui/material";
import { ExpandMore as ExpandMoreIcon } from "@mui/icons-material";
import { useMutation } from "@tanstack/react-query";
import {
  formPipelineApi,
  type CreateExportRequest,
  type DataSource,
} from "../services/formPipelineApi";

interface TemplateConfig {
  use_advanced_template?: boolean;
  include_charts?: boolean;
}

interface FilterConfig {
  exclude_duplicates?: boolean;
}

interface CreateExportDialogProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  dataSources: DataSource[];
}

export const CreateExportDialog: React.FC<CreateExportDialogProps> = ({
  open,
  onClose,
  onSuccess,
  dataSources,
}) => {
  const [formData, setFormData] = useState<CreateExportRequest>({
    name: "",
    description: "",
    data_sources: [],
    date_range_start: "",
    date_range_end: "",
    filters: {},
    template_config: {},
    is_auto_generated: false,
    auto_schedule: "",
  });

  const createMutation = useMutation({
    mutationFn: (data: CreateExportRequest) =>
      formPipelineApi.createExcelExport(data),
    onSuccess: () => {
      onSuccess();
      handleClose();
    },
  });

  const handleClose = () => {
    setFormData({
      name: "",
      description: "",
      data_sources: [],
      date_range_start: "",
      date_range_end: "",
      filters: {},
      template_config: {},
      is_auto_generated: false,
      auto_schedule: "",
    });
    onClose();
  };

  const handleSubmit = () => {
    createMutation.mutate(formData);
  };

  const handleDataSourceChange = (dataSourceId: number, checked: boolean) => {
    setFormData((prev) => ({
      ...prev,
      data_sources: checked
        ? [...prev.data_sources, dataSourceId]
        : prev.data_sources.filter((id) => id !== dataSourceId),
    }));
  };

  const updateFormData = (
    field: keyof CreateExportRequest,
    value: string | number | boolean | number[] | Record<string, unknown>
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const isValid = formData.name && formData.data_sources.length > 0;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Create Excel Export</DialogTitle>

      <DialogContent>
        {createMutation.isError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            Failed to create export. Please try again.
          </Alert>
        )}

        <TextField
          fullWidth
          label="Export Name"
          value={formData.name}
          onChange={(e) => updateFormData("name", e.target.value)}
          margin="normal"
          required
          helperText="A descriptive name for this export"
        />

        <TextField
          fullWidth
          label="Description (Optional)"
          value={formData.description}
          onChange={(e) => updateFormData("description", e.target.value)}
          margin="normal"
          multiline
          rows={2}
          helperText="Additional details about this export"
        />

        {/* Data Sources Selection */}
        <Box sx={{ mt: 2 }}>
          <FormControl component="fieldset">
            <FormLabel component="legend" required>
              Select Data Sources
            </FormLabel>
            <FormGroup>
              {dataSources.map((source) => (
                <FormControlLabel
                  key={source.id}
                  control={
                    <Checkbox
                      checked={formData.data_sources.includes(source.id)}
                      onChange={(e) =>
                        handleDataSourceChange(source.id, e.target.checked)
                      }
                    />
                  }
                  label={
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                      <Typography>{source.name}</Typography>
                      <Chip
                        size="small"
                        label={`${source.submission_count} submissions`}
                        variant="outlined"
                      />
                      <Chip
                        size="small"
                        label={source.source_type.replace("_", " ")}
                        color="primary"
                        variant="outlined"
                      />
                    </Box>
                  }
                />
              ))}
            </FormGroup>
          </FormControl>
        </Box>

        {/* Advanced Options */}
        <Accordion sx={{ mt: 2 }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography>Advanced Options</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {/* Date Range Filter */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Date Range Filter (Optional)
              </Typography>
              <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap" }}>
                <TextField
                  type="datetime-local"
                  label="Start Date"
                  value={formData.date_range_start?.slice(0, 16) || ""}
                  onChange={(e) =>
                    updateFormData(
                      "date_range_start",
                      e.target.value
                        ? new Date(e.target.value).toISOString()
                        : ""
                    )
                  }
                  sx={{ flex: 1, minWidth: 200 }}
                  InputLabelProps={{ shrink: true }}
                />
                <TextField
                  type="datetime-local"
                  label="End Date"
                  value={formData.date_range_end?.slice(0, 16) || ""}
                  onChange={(e) =>
                    updateFormData(
                      "date_range_end",
                      e.target.value
                        ? new Date(e.target.value).toISOString()
                        : ""
                    )
                  }
                  sx={{ flex: 1, minWidth: 200 }}
                  InputLabelProps={{ shrink: true }}
                />
              </Box>
            </Box>

            {/* Export Options */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Export Options
              </Typography>

              <FormControlLabel
                control={
                  <Switch
                    checked={Boolean(
                      (formData.template_config as TemplateConfig)
                        ?.use_advanced_template
                    )}
                    onChange={(e) =>
                      updateFormData("template_config", {
                        ...formData.template_config,
                        use_advanced_template: e.target.checked,
                      })
                    }
                  />
                }
                label="Use Advanced Template (with charts and formatting)"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={Boolean(
                      (formData.template_config as TemplateConfig)
                        ?.include_charts
                    )}
                    onChange={(e) =>
                      updateFormData("template_config", {
                        ...formData.template_config,
                        include_charts: e.target.checked,
                      })
                    }
                  />
                }
                label="Include Data Visualization Charts"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={Boolean(
                      (formData.filters as FilterConfig)?.exclude_duplicates
                    )}
                    onChange={(e) =>
                      updateFormData("filters", {
                        ...formData.filters,
                        exclude_duplicates: e.target.checked,
                      })
                    }
                  />
                }
                label="Exclude Previously Exported Submissions"
              />
            </Box>

            {/* Auto Generation */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Automatic Generation
              </Typography>

              <FormControlLabel
                control={
                  <Switch
                    checked={formData.is_auto_generated || false}
                    onChange={(e) =>
                      updateFormData("is_auto_generated", e.target.checked)
                    }
                  />
                }
                label="Enable Automatic Export Generation"
              />

              {formData.is_auto_generated && (
                <Alert severity="info" sx={{ mt: 1 }}>
                  This export will be automatically generated when new
                  submissions are received from the selected data sources.
                </Alert>
              )}
            </Box>
          </AccordionDetails>
        </Accordion>

        {/* Export Preview */}
        {formData.data_sources.length > 0 && (
          <Alert severity="info" sx={{ mt: 2 }}>
            <Typography variant="body2">
              <strong>Export Preview:</strong>
              <br />• {formData.data_sources.length} data source
              {formData.data_sources.length !== 1 ? "s" : ""} selected
              <br />• Total submissions:{" "}
              {dataSources
                .filter((ds) => formData.data_sources.includes(ds.id))
                .reduce((sum, ds) => sum + ds.submission_count, 0)}
              <br />• Date range:{" "}
              {formData.date_range_start ? "Filtered" : "All available data"}
            </Typography>
          </Alert>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose}>Cancel</Button>

        <Button
          variant="contained"
          onClick={handleSubmit}
          disabled={!isValid || createMutation.isPending}
        >
          {createMutation.isPending ? "Creating Export..." : "Create Export"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
