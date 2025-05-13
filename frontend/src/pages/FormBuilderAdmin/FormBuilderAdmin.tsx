import { useState } from 'react';
import {
  Box,
  Typography,
  Button,
  IconButton,
  Paper,
  TextField,
  Switch,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Divider,
  Tooltip,
  Stack,
} from '@mui/material';

interface FormField {
  label: string;
  type: string;
  required: boolean;
  options: string[];
}


import type { DraggableProvided, DroppableProvided, DropResult, DraggableStateSnapshot } from '@hello-pangea/dnd';
import { DragDropContext, Droppable, Draggable } from '@hello-pangea/dnd';
import { Delete, Edit, DragIndicator } from '@mui/icons-material';


const FIELD_TYPES = [
  { value: 'text', label: 'Text' },
  { value: 'number', label: 'Number' },
  { value: 'email', label: 'Email' },
  { value: 'select', label: 'Select' },
  { value: 'checkbox', label: 'Checkbox' },
  { value: 'radio', label: 'Radio' },
  { value: 'date', label: 'Date' },
  { value: 'file', label: 'File Upload' },
];

const defaultField = {
  label: '',
  type: 'text',
  required: false,
  options: [],
};

export default function FormBuilderAdmin() {
  const [fields, setFields] = useState<FormField[]>([]);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [field, setField] = useState<FormField>(defaultField);
  const [previewMode, setPreviewMode] = useState(false);

  const handleAddField = () => {
    setFields([...fields, { ...field, options: field.options || [] }]);
    setField(defaultField);
    setEditingIndex(null);
  };

  const handleEditField = (index: number) => {
    setField(fields[index]);
    setEditingIndex(index);
  };

  const handleSaveField = () => {
    if (editingIndex !== null) {
      const updated = [...fields];
      updated[editingIndex] = field;
      setFields(updated);
      setEditingIndex(null);
    } else {
      handleAddField();
    }
    setField(defaultField);
  };

  const handleDeleteField = (index: number) => {
    setFields(fields.filter((_, i) => i !== index));
  };

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) return;
    const reordered = Array.from(fields);
    const [removed] = reordered.splice(result.source.index, 1);
    reordered.splice(result.destination.index, 0, removed);
    setFields(reordered);
  };

  const handleFieldChange = (key: keyof FormField, value: any) => {
    setField((prev: FormField) => ({ ...prev, [key]: value }));
  };

  const handleOptionChange = (idx: number, value: string) => {
    const newOptions = [...field.options];
    newOptions[idx] = value;
    setField((prev: FormField) => ({ ...prev, options: newOptions }));
  };

  const addOption = () => {
    setField((prev: FormField) => ({ ...prev, options: [...prev.options, ''] }));
  };

  const removeOption = (idx: number) => {
    setField((prev: FormField) => ({ ...prev, options: prev.options.filter((_, i: number) => i !== idx) }));
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Form Builder
      </Typography>
      <Box mb={2}>
        <Button variant={previewMode ? 'outlined' : 'contained'} onClick={() => setPreviewMode(false)} sx={{ mr: 1 }}>
          Edit Mode
        </Button>
        <Button variant={previewMode ? 'contained' : 'outlined'} onClick={() => setPreviewMode(true)}>
          Preview
        </Button>
      </Box>
      <Divider sx={{ mb: 3 }} />

      {!previewMode && (
        <Stack direction="row" spacing={2}>
          <Box flex={1} maxWidth="500px">
            <Paper sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                {editingIndex !== null ? 'Edit Field' : 'Add Field'}
              </Typography>
              <TextField
                label="Label"
                value={field.label}
                onChange={e => handleFieldChange('label', e.target.value)}
                fullWidth
                margin="normal"
              />
              <FormControl fullWidth margin="normal">
                <InputLabel>Type</InputLabel>
                <Select
                  value={field.type}
                  label="Type"
                  onChange={e => handleFieldChange('type', e.target.value)}
                >
                  {FIELD_TYPES.map(opt => (
                    <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
                  ))}
                </Select>
              </FormControl>
              {(field.type === 'select' || field.type === 'radio') && (
                <Box>
                  <Typography variant="subtitle2" sx={{ mt: 2 }}>
                    Options
                  </Typography>
                  {(field.options || []).map((opt: string, idx: number) => (
                    <Box key={idx} display="flex" alignItems="center" mb={1}>
                      <TextField
                        value={opt}
                        onChange={e => handleOptionChange(idx, e.target.value)}
                        size="small"
                        sx={{ flex: 1, mr: 1 }}
                      />
                      <IconButton size="small" onClick={() => removeOption(idx)}>
                        <Delete fontSize="small" />
                      </IconButton>
                    </Box>
                  ))}
                  <Button size="small" onClick={addOption} sx={{ mt: 1 }}>
                    Add Option
                  </Button>
                </Box>
              )}
              <FormControl fullWidth margin="normal">
                <Box display="flex" alignItems="center">
                  <Switch
                    checked={field.required}
                    onChange={e => handleFieldChange('required', e.target.checked)}
                  />
                  <Typography>Required</Typography>
                </Box>
              </FormControl>
              <Button
                variant="contained"
                color="primary"
                onClick={handleSaveField}
                sx={{ mt: 2 }}
                fullWidth
              >
                {editingIndex !== null ? 'Save Changes' : 'Add Field'}
              </Button>
            </Paper>
          </Box>
          <Box flex={2}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>
                Form Fields
              </Typography>
              <DragDropContext onDragEnd={handleDragEnd}>
                <Droppable droppableId="fields-droppable">
                  {(provided: DroppableProvided) => (
                    <Box ref={provided.innerRef} {...provided.droppableProps}>
                      {fields.map((f, idx) => (
                        <Draggable key={idx} draggableId={`field-${idx}`} index={idx}>
                          {(provided: DraggableProvided, snapshot: DraggableStateSnapshot) => (
                            <Box
                              ref={provided.innerRef}
                              {...provided.draggableProps}
                              sx={{
                                p: 2,
                                mb: 2,
                                display: 'flex',
                                alignItems: 'center',
                                bgcolor: snapshot.isDragging ? 'action.hover' : 'background.paper',
                                borderRadius: 1,
                                boxShadow: 1,
                              }}
                            >
                              <Box {...provided.dragHandleProps} sx={{ mr: 2, cursor: 'grab' }}>
                                <DragIndicator />
                              </Box>
                              <Box sx={{ flex: 1 }}>
                                <Typography>{f.label} ({f.type}) {f.required && '*'}</Typography>
                              </Box>
                              <Tooltip title="Edit">
                                <IconButton onClick={() => handleEditField(idx)} size="small">
                                  <Edit fontSize="small" />
                                </IconButton>
                              </Tooltip>
                              <Tooltip title="Delete">
                                <IconButton onClick={() => handleDeleteField(idx)} size="small" color="error">
                                  <Delete fontSize="small" />
                                </IconButton>
                              </Tooltip>
                            </Box>
                          )}
                        </Draggable>
                      ))}
                      {provided.placeholder}
                    </Box>
                  )}
                </Droppable>
              </DragDropContext>
            </Paper>
          </Box>
        </Stack>
      )}

      {previewMode && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Form Preview
          </Typography>
          <form>
            {fields.map((f, idx) => {
              switch (f.type) {
                case 'text':
                case 'email':
                case 'number':
                case 'date':
                  return (
                    <TextField
                      key={idx}
                      label={f.label}
                      type={f.type}
                      required={f.required}
                      fullWidth
                      margin="normal"
                    />
                  );
                case 'select':
                  return (
                    <FormControl fullWidth margin="normal" key={idx}>
                      <InputLabel>{f.label}</InputLabel>
                      <Select label={f.label} required={f.required} defaultValue="">
                        {f.options?.map((opt: string, i: number) => (
                          <MenuItem key={i} value={opt}>{opt}</MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  );
                case 'checkbox':
                  return (
                    <FormControl key={idx} margin="normal">
                      <Box display="flex" alignItems="center">
                        <Switch required={f.required} />
                        <Typography>{f.label}</Typography>
                      </Box>
                    </FormControl>
                  );
                case 'radio':
                  return (
                    <FormControl component="fieldset" key={idx} margin="normal">
                      <Typography>{f.label}</Typography>
                      {f.options?.map((opt: string, i: number) => (
                        <Box key={i} display="flex" alignItems="center">
                          <Switch />
                          <Typography>{opt}</Typography>
                        </Box>
                      ))}
                    </FormControl>
                  );
                case 'file':
                  return (
                    <Box key={idx} marginY={2}>
                      <Typography>{f.label}</Typography>
                      <input type="file" required={f.required} />
                    </Box>
                  );
                default:
                  return null;
              }
            })}
          </form>
        </Paper>
      )}

      <Box mt={4} display="flex" justifyContent="flex-end">
        <Button variant="contained" color="primary" size="large">
          Publish Form
        </Button>
      </Box>
    </Box>
  );
}
