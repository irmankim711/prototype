import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  Button,
  Typography,
  Paper,
  CircularProgress,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
} from '@mui/material';
import { useForm, Controller } from 'react-hook-form';
import {
  fetchReportTemplates,
  createReport,
  analyzeData,
} from '../../services/api';
import type { ReportTemplate } from '../../services/api';

const steps = ['Select Template', 'Enter Data', 'Review & Generate'];

export default function ReportBuilder() {
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [reportData, setReportData] = useState<any>({});
  const [analysis, setAnalysis] = useState<any>(null);

  const { control, handleSubmit, watch } = useForm();
  const selectedTemplateId = watch('templateId');

  const { data: templates, isLoading: templatesLoading } = useQuery({
    queryKey: ['reportTemplates'],
    queryFn: fetchReportTemplates,
  });

  const createReportMutation = useMutation({
    mutationFn: createReport,
    onSuccess: (data) => {
      navigate(`/reports/${data.id}`);
    },
  });

  const analyzeDataMutation = useMutation({
    mutationFn: analyzeData,
    onSuccess: (data) => {
      setAnalysis(data);
    },
  });

  const handleNext = async (formData: any) => {
    if (activeStep === 0) {
      setReportData({ ...reportData, templateId: formData.templateId });
    } else if (activeStep === 1) {
      setReportData({ ...reportData, ...formData });
      // Analyze data before moving to review step
      await analyzeDataMutation.mutateAsync(formData);
    }
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleGenerate = async () => {
    await createReportMutation.mutateAsync({
      ...reportData,
      analysis,
    });
  };

  const getStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <FormControl fullWidth>
            <InputLabel>Select Template</InputLabel>
            <Controller
              name="templateId"
              control={control}
              rules={{ required: 'Please select a template' }}
              render={({ field, fieldState }) => (
                <Select {...field} error={!!fieldState.error}>
                  {templates?.map((template: ReportTemplate) => (
                    <MenuItem key={template.id} value={template.id}>
                      {template.name}
                    </MenuItem>
                  ))}
                </Select>
              )}
            />
          </FormControl>
        );

      case 1:
        const selectedTemplate = templates?.find(
          (t: ReportTemplate) => t.id === selectedTemplateId
        );
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              {selectedTemplate?.name}
            </Typography>
            {selectedTemplate?.schema.fields.map((field: any) => (
              <Controller
                key={field.name}
                name={field.name}
                control={control}
                rules={{ required: field.required }}
                render={({ field: { onChange, value }, fieldState }) => (
                  <TextField
                    fullWidth
                    label={field.label}
                    type={field.type}
                    value={value || ''}
                    onChange={onChange}
                    error={!!fieldState.error}
                    helperText={fieldState.error?.message}
                    margin="normal"
                  />
                )}
              />
            ))}
          </Box>
        );

      case 2:
        return (
          <Box>
            <Typography variant="h6" gutterBottom>
              Review Report Data
            </Typography>
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Template: {templates?.find((t: ReportTemplate) => t.id === reportData.templateId)?.name}
              </Typography>
              {Object.entries(reportData).map(([key, value]) => (
                key !== 'templateId' && (
                  <Typography key={key} variant="body1">
                    {key}: {value as string}
                  </Typography>
                )
              ))}
            </Paper>
            {analysis && (
              <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>
                  AI Analysis
                </Typography>
                <Typography variant="body1">{analysis.summary}</Typography>
                {analysis.suggestions && (
                  <Alert severity="info" sx={{ mt: 2 }}>
                    {analysis.suggestions}
                  </Alert>
                )}
              </Paper>
            )}
          </Box>
        );

      default:
        return 'Unknown step';
    }
  };

  if (templatesLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Create New Report
      </Typography>

      <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>

      <Paper sx={{ p: 3 }}>
        <form onSubmit={handleSubmit(handleNext)}>
          {getStepContent(activeStep)}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
            <Button
              disabled={activeStep === 0}
              onClick={handleBack}
              sx={{ mr: 1 }}
            >
              Back
            </Button>
            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={handleGenerate}
                disabled={createReportMutation.isLoading}
              >
                {createReportMutation.isLoading ? (
                  <CircularProgress size={24} />
                ) : (
                  'Generate Report'
                )}
              </Button>
            ) : (
              <Button variant="contained" type="submit">
                Next
              </Button>
            )}
          </Box>
        </form>
      </Paper>
    </Box>
  );
}
