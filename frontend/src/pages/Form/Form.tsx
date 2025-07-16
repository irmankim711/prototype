import { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Paper,
  Grid,
  styled,
  Card,
  CardContent,
} from '@mui/material';
import type { SelectChangeEvent } from '@mui/material';
import { createForm } from '../../services/api'; // <-- Add this import

// Styled components
const PageTitle = styled(Typography)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 600,
  fontSize: '1.5rem',
  color: '#333',
  marginBottom: '1rem',
  borderBottom: '2px solid #1e3a8a',
  paddingBottom: '0.5rem',
  display: 'inline-block',
}));

const FormSection = styled(Box)(() => ({
  marginBottom: '2rem',
}));

const SectionTitle = styled(Typography)(() => ({
  fontFamily: '"Poppins", sans-serif',
  fontWeight: 600,
  fontSize: '1.1rem',
  color: '#1e3a8a',
  marginBottom: '1rem',
}));

const FormPaper = styled(Paper)(() => ({
  padding: '1.5rem',
  borderRadius: '4px',
  boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
  border: '1px solid #eaeaea',
}));

const StyledFormControl = styled(FormControl)(() => ({
  marginBottom: '1rem',
  width: '100%',
}));

const StyledButton = styled(Button)(() => ({
  backgroundColor: '#3f51b5',
  borderRadius: '4px',
  textTransform: 'none',
  fontWeight: 500,
  padding: '0.5rem 1.5rem',
  '&:hover': {
    backgroundColor: '#303f9f',
  },
}));

const StyledTextField = styled(TextField)(() => ({
  marginBottom: '1rem',
  '& .MuiOutlinedInput-root': {
    '& fieldset': {
      borderColor: '#ccc',
    },
    '&:hover fieldset': {
      borderColor: '#999',
    },
    '&.Mui-focused fieldset': {
      borderColor: '#3f51b5',
    },
  },
}));

const StyledSelect = styled(Select)(() => ({
  textAlign: 'left',
  '.MuiOutlinedInput-notchedOutline': {
    borderColor: '#ccc',
  },
  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
    borderColor: '#3f51b5',
  },
}));

export default function FormPage() {
  const [formType, setFormType] = useState<string>('standard');
  const [formData, setFormData] = useState({
    title: '',
    department: '',
    dueDate: '',
    responseType: 'text',
    isRequired: true,
  });

  // Add a description and is_public for backend compatibility
  const [description, setDescription] = useState('');
  const [isPublic, setIsPublic] = useState(false);

  const handleFormTypeChange = (event: SelectChangeEvent<string>) => {
    setFormType(event.target.value as string);
  };

  const handleInputChange = (name: string, value: string | boolean) => {
    setFormData({ ...formData, [name]: value });
  };

  // Submit handler: call backend
  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!formData.title.trim()) {
      // setSnackbar({ open: true, message: 'Form title is required.', severity: 'error' }); // Original code had snackbar, but not defined.
      alert('Form title is required.');
      return;
    }
    if (formData.responseType === 'multiple_choice' || formData.responseType === 'checkbox') {
      // setSnackbar({ open: true, message: 'Add at least one field.', severity: 'error' }); // Original code had snackbar, but not defined.
      alert('Add at least one field for multiple choice or checkbox.');
      return;
    }
    try {
      // Map fields to backend format (no id, use label/type/required)
      const backendFields = [{
        label: formData.title, // Assuming the first field is the title
        type: formData.responseType,
        required: formData.isRequired,
      }];
      await createForm({
        title: formData.title,
        description,
        fields: backendFields,
        is_public: isPublic,
      });
      alert('Form created successfully!');
      // Optionally reset form or redirect
    } catch (err: any) {
      alert(err?.response?.data?.error || 'Failed to create form');
    }
  };

  return (
    <Box>
      <PageTitle>Form Builder</PageTitle>

      <form onSubmit={handleSubmit}>
        {/* Form Settings Section */}
        <FormSection>
          <FormPaper>
            <SectionTitle>Form Settings</SectionTitle>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <StyledTextField
                  fullWidth
                  label="Form Title"
                  variant="outlined"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <StyledFormControl>
                  <InputLabel id="department-label">Department</InputLabel>
                  <StyledSelect
                    labelId="department-label"
                    label="Department"
                    value={formData.department}
                    onChange={(e) => handleInputChange('department', e.target.value as string)}
                  >
                    <MenuItem value="HR">Human Resources</MenuItem>
                    <MenuItem value="IT">IT Department</MenuItem>
                    <MenuItem value="Finance">Finance</MenuItem>
                    <MenuItem value="Marketing">Marketing</MenuItem>
                  </StyledSelect>
                </StyledFormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <StyledTextField
                  fullWidth
                  label="Due Date"
                  type="date"
                  InputLabelProps={{ shrink: true }}
                  value={formData.dueDate}
                  onChange={(e) => handleInputChange('dueDate', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <StyledFormControl>
                  <InputLabel id="form-type-label">Form Type</InputLabel>
                  <StyledSelect
                    labelId="form-type-label"
                    label="Form Type"
                    value={formType}
                    onChange={handleFormTypeChange as any}
                  >
                    <MenuItem value="standard">Standard Form</MenuItem>
                    <MenuItem value="survey">Survey</MenuItem>
                    <MenuItem value="assessment">Assessment</MenuItem>
                    <MenuItem value="feedback">Feedback</MenuItem>
                  </StyledSelect>
                </StyledFormControl>
              </Grid>
              <Grid item xs={12}>
                <StyledTextField
                  fullWidth
                  label="Description"
                  value={description}
                  onChange={e => setDescription(e.target.value)}
                  multiline
                  minRows={2}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={isPublic}
                      onChange={e => setIsPublic(e.target.checked)}
                    />
                  }
                  label="Make form public"
                />
              </Grid>
            </Grid>
          </FormPaper>
        </FormSection>

        <FormSection>
          <FormPaper>
            <SectionTitle>Form Fields</SectionTitle>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <Card sx={{ mb: 2, border: '1px dashed #ccc' }}>
                  <CardContent>
                    <Grid container spacing={2}>
                      <Grid item xs={12} md={6}>
                        <StyledTextField
                          fullWidth
                          label="Question/Field Label"
                          variant="outlined"
                          placeholder="Enter your question here"
                        />
                      </Grid>
                      <Grid item xs={12} md={6}>
                        <StyledFormControl>
                          <InputLabel id="response-type-label">Response Type</InputLabel>
                          <StyledSelect
                            labelId="response-type-label"
                            label="Response Type"
                            value={formData.responseType}
                            onChange={(e) => handleInputChange('responseType', e.target.value as string)}
                          >
                            <MenuItem value="text">Text</MenuItem>
                            <MenuItem value="number">Number</MenuItem>
                            <MenuItem value="date">Date</MenuItem>
                            <MenuItem value="multiple_choice">Multiple Choice</MenuItem>
                            <MenuItem value="checkbox">Checkbox</MenuItem>
                          </StyledSelect>
                        </StyledFormControl>
                      </Grid>
                      <Grid item xs={12}>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={formData.isRequired}
                              onChange={(e) => handleInputChange('isRequired', e.target.checked)}
                              color="primary"
                            />
                          }
                          label="Required Field"
                        />
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                  <Button
                    variant="outlined"
                    startIcon={<i className="fas fa-plus"></i>}
                    sx={{ 
                      borderRadius: '4px', 
                      textTransform: 'none',
                      borderColor: '#3f51b5',
                      color: '#3f51b5',
                    }}
                  >
                    Add Field
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </FormPaper>
        </FormSection>

        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 3 }}>
          <Button
            variant="outlined"
            sx={{ 
              mr: 2, 
              borderRadius: '4px', 
              textTransform: 'none',
              borderColor: '#999',
              color: '#666',
            }}
          >
            Save as Draft
          </Button>
          <StyledButton
            type="submit"
            variant="contained"
          >
            Create Form
          </StyledButton>
        </Box>
      </form>
    </Box>
  );
}
