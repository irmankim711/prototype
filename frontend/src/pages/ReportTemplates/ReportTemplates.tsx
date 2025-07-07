import { useState } from 'react';
import {
  Box,
  Typography,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Switch,
  FormControlLabel,
  CircularProgress,
  IconButton,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import { Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchReportTemplates, updateReportTemplate } from '../../services/api';
import type { ReportTemplate } from '../../services/api';

export default function ReportTemplates() {
  const [editTemplate, setEditTemplate] = useState<ReportTemplate | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const { data: templates, isLoading } = useQuery({
    queryKey: ['reportTemplates'],
    queryFn: fetchReportTemplates,
  });

  const updateTemplateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<ReportTemplate> }) =>
      updateReportTemplate(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reportTemplates'] });
      handleCloseDialog();
    },
  });

  const handleOpenDialog = (template: ReportTemplate) => {
    setEditTemplate(template);
    setIsDialogOpen(true);
  };

  const handleCloseDialog = () => {
    setEditTemplate(null);
    setIsDialogOpen(false);
  };

  const handleSaveTemplate = (event: React.FormEvent) => {
    event.preventDefault();
    if (!editTemplate) return;

    const formData = new FormData(event.target as HTMLFormElement);
    const data = {
      name: formData.get('name') as string,
      description: formData.get('description') as string,
      isActive: formData.get('isActive') === 'true',
    };

    updateTemplateMutation.mutate({
      id: editTemplate.id,
      data,
    });
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={4}>
        <Typography variant="h4">Report Templates</Typography>
        <Button variant="contained" color="primary">
          Create Template
        </Button>
      </Box>

      <Grid container spacing={3}>
        {templates?.map((template) => (
          <Grid item xs={12} sm={6} md={4} key={template.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {template.name}
                </Typography>
                <Typography color="textSecondary" gutterBottom>
                  {template.description}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  Fields: {template.schema.fields.length}
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={template.isActive}
                      color="primary"
                      disabled
                    />
                  }
                  label={template.isActive ? 'Active' : 'Inactive'}
                />
              </CardContent>
              <CardActions>
                <IconButton
                  size="small"
                  onClick={() => handleOpenDialog(template)}
                >
                  <EditIcon />
                </IconButton>
                <IconButton size="small" color="error">
                  <DeleteIcon />
                </IconButton>
              </CardActions>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Dialog open={isDialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <form onSubmit={handleSaveTemplate}>
          <DialogTitle>Edit Template</DialogTitle>
          <DialogContent>
            <TextField
              name="name"
              label="Template Name"
              fullWidth
              defaultValue={editTemplate?.name}
              margin="normal"
              required
            />
            <TextField
              name="description"
              label="Description"
              fullWidth
              multiline
              rows={3}
              defaultValue={editTemplate?.description}
              margin="normal"
            />
            <FormControlLabel
              control={
                <Switch
                  name="isActive"
                  defaultChecked={editTemplate?.isActive}
                  color="primary"
                />
              }
              label="Active"
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleCloseDialog}>Cancel</Button>
            <Button
              type="submit"
              variant="contained"
              color="primary"
              disabled={updateTemplateMutation.isLoading}
            >
              {updateTemplateMutation.isLoading ? (
                <CircularProgress size={24} />
              ) : (
                'Save Changes'
              )}
            </Button>
          </DialogActions>
        </form>
      </Dialog>
    </Box>
  );
}
