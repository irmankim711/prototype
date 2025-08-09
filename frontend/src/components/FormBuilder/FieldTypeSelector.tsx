/**
 * Field Type Selector Component
 * Provides a visual selector for different form field types
 */

import React from "react";
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Tooltip,
} from "@mui/material";
import {
  TextFields as TextIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Numbers as NumberIcon,
  CalendarToday as DateIcon,
  Schedule as TimeIcon,
  CheckBox as CheckboxIcon,
  RadioButtonChecked as RadioIcon,
  ArrowDropDown as SelectIcon,
  CloudUpload as FileIcon,
  Description as TextareaIcon,
  Link as UrlIcon,
  Password as PasswordIcon,
  ColorLens as ColorIcon,
} from "@mui/icons-material";

interface FieldTypeSelectorProps {
  onSelect: (fieldType: string) => void;
}

interface FieldType {
  type: string;
  label: string;
  description: string;
  icon: React.ComponentType<{ sx?: Record<string, any> }>;
  color: string;
}

const fieldTypes: FieldType[] = [
  {
    type: "text",
    label: "Text Input",
    description: "Single line text input",
    icon: TextIcon,
    color: "#1976d2",
  },
  {
    type: "textarea",
    label: "Text Area",
    description: "Multi-line text input",
    icon: TextareaIcon,
    color: "#388e3c",
  },
  {
    type: "email",
    label: "Email",
    description: "Email address input",
    icon: EmailIcon,
    color: "#f57c00",
  },
  {
    type: "phone",
    label: "Phone",
    description: "Phone number input",
    icon: PhoneIcon,
    color: "#7b1fa2",
  },
  {
    type: "number",
    label: "Number",
    description: "Numeric input",
    icon: NumberIcon,
    color: "#c62828",
  },
  {
    type: "date",
    label: "Date",
    description: "Date picker",
    icon: DateIcon,
    color: "#00796b",
  },
  {
    type: "time",
    label: "Time",
    description: "Time picker",
    icon: TimeIcon,
    color: "#5e35b1",
  },
  {
    type: "checkbox",
    label: "Checkbox",
    description: "Multiple choice checkboxes",
    icon: CheckboxIcon,
    color: "#2e7d32",
  },
  {
    type: "radio",
    label: "Radio Button",
    description: "Single choice radio buttons",
    icon: RadioIcon,
    color: "#d32f2f",
  },
  {
    type: "select",
    label: "Dropdown",
    description: "Dropdown selection",
    icon: SelectIcon,
    color: "#1565c0",
  },
  {
    type: "file",
    label: "File Upload",
    description: "File upload field",
    icon: FileIcon,
    color: "#ef6c00",
  },
  {
    type: "url",
    label: "URL",
    description: "Website URL input",
    icon: UrlIcon,
    color: "#00695c",
  },
  {
    type: "password",
    label: "Password",
    description: "Password input field",
    icon: PasswordIcon,
    color: "#8e24aa",
  },
  {
    type: "color",
    label: "Color Picker",
    description: "Color selection field",
    icon: ColorIcon,
    color: "#d84315",
  },
];

export const FieldTypeSelector: React.FC<FieldTypeSelectorProps> = ({
  onSelect,
}) => {
  return (
    <Grid container spacing={2}>
      {fieldTypes.map((fieldType) => {
        const IconComponent = fieldType.icon;

        return (
          <Grid item xs={12} sm={6} key={fieldType.type}>
            <Tooltip title={fieldType.description} placement="top">
              <Card
                sx={{
                  cursor: "pointer",
                  transition: "all 0.2s",
                  "&:hover": {
                    transform: "translateY(-2px)",
                    boxShadow: 4,
                    bgcolor: `${fieldType.color}08`,
                  },
                }}
                onClick={() => onSelect(fieldType.type)}
              >
                <CardContent sx={{ p: 2, "&:last-child": { pb: 2 } }}>
                  <Box display="flex" alignItems="center" gap={2}>
                    <Box
                      sx={{
                        p: 1,
                        borderRadius: 1,
                        bgcolor: `${fieldType.color}15`,
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                      }}
                    >
                      <IconComponent
                        sx={{ color: fieldType.color, fontSize: 20 }}
                      />
                    </Box>

                    <Box flex={1}>
                      <Typography variant="subtitle2" fontWeight={600}>
                        {fieldType.label}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {fieldType.description}
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Tooltip>
          </Grid>
        );
      })}
    </Grid>
  );
};
