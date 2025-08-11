import React from "react";
import {
  TextField,
  FormHelperText,
  Box,
  Typography,
  IconButton,
  Tooltip,
  alpha,
  styled,
} from "@mui/material";
import {
  Info as InfoIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from "@mui/icons-material";

// Styled components for enhanced form fields
const EnhancedTextField = styled(TextField)(({ theme, error }) => ({
  "& .MuiOutlinedInput-root": {
    transition: "all 0.2s ease",
    "&:hover": {
      "& .MuiOutlinedInput-notchedOutline": {
        borderColor: error
          ? theme.palette.error.main
          : theme.palette.primary.main,
      },
    },
    "&.Mui-focused": {
      "& .MuiOutlinedInput-notchedOutline": {
        borderWidth: 2,
        borderColor: error
          ? theme.palette.error.main
          : theme.palette.primary.main,
      },
    },
  },
  "& .MuiInputLabel-root": {
    fontWeight: 500,
  },
}));

const FieldContainer = styled(Box)(({ theme }) => ({
  position: "relative",
  marginBottom: theme.spacing(2),
}));

const ValidationIcon = styled(Box)(({ theme }) => ({
  position: "absolute",
  right: theme.spacing(1),
  top: "50%",
  transform: "translateY(-50%)",
  zIndex: 1,
}));

const HiddenCheckbox = styled("input")({
  opacity: 0,
  width: 0,
  height: 0,
  position: "absolute",
});

const HelperTextContainer = styled(Box)(({ theme }) => ({
  display: "flex",
  alignItems: "center",
  marginTop: theme.spacing(0.5),
  gap: theme.spacing(0.5),
}));

export interface EnhancedFormFieldProps {
  name: string;
  label: string;
  value: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  onBlur?: (event: React.FocusEvent<HTMLInputElement>) => void;
  error?: string | null;
  helperText?: string;
  required?: boolean;
  disabled?: boolean;
  multiline?: boolean;
  rows?: number;
  type?: string;
  placeholder?: string;
  maxLength?: number;
  showValidationIcon?: boolean;
  tooltip?: string;
  autoComplete?: string;
  "aria-describedby"?: string;
  "aria-label"?: string;
  fullWidth?: boolean;
}

export const EnhancedFormField: React.FC<EnhancedFormFieldProps> = ({
  name,
  label,
  value,
  onChange,
  onBlur,
  error,
  helperText,
  required = false,
  disabled = false,
  multiline = false,
  rows = 1,
  type = "text",
  placeholder,
  maxLength,
  showValidationIcon = true,
  tooltip,
  autoComplete,
  fullWidth = true,
  ...ariaProps
}) => {
  const hasError = Boolean(error);
  const hasValue = Boolean(value && value.trim());
  const isValid = hasValue && !hasError;

  const helperTextId = `${name}-helper-text`;
  const errorId = `${name}-error`;

  return (
    <FieldContainer>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
        <Typography
          variant="body2"
          component="label"
          htmlFor={name}
          sx={{ fontWeight: 500, color: "text.primary" }}
        >
          {label}
          {required && (
            <Typography component="span" sx={{ color: "error.main", ml: 0.5 }}>
              *
            </Typography>
          )}
        </Typography>
        {tooltip && (
          <Tooltip title={tooltip} arrow>
            <IconButton size="small" sx={{ p: 0.5 }}>
              <InfoIcon sx={{ fontSize: 16, color: "text.secondary" }} />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      <Box sx={{ position: "relative" }}>
        <EnhancedTextField
          id={name}
          name={name}
          value={value}
          onChange={onChange}
          onBlur={onBlur}
          error={hasError}
          disabled={disabled}
          multiline={multiline}
          rows={rows}
          type={type}
          placeholder={placeholder}
          fullWidth={fullWidth}
          autoComplete={autoComplete}
          inputProps={{
            maxLength,
            "aria-describedby": hasError ? errorId : helperTextId,
            "aria-invalid": hasError,
            ...ariaProps,
          }}
          sx={{
            "& .MuiOutlinedInput-root": {
              pr: showValidationIcon && (hasError || isValid) ? 5 : 1.5,
            },
          }}
        />

        {showValidationIcon && (hasError || isValid) && (
          <ValidationIcon>
            {hasError ? (
              <ErrorIcon sx={{ color: "error.main", fontSize: 20 }} />
            ) : (
              <CheckCircleIcon sx={{ color: "success.main", fontSize: 20 }} />
            )}
          </ValidationIcon>
        )}
      </Box>

      {(error || helperText) && (
        <HelperTextContainer>
          <FormHelperText
            id={hasError ? errorId : helperTextId}
            error={hasError}
            sx={{
              fontSize: "0.875rem",
              display: "flex",
              alignItems: "center",
              gap: 0.5,
            }}
          >
            {error || helperText}
          </FormHelperText>
          {maxLength && (
            <Typography
              variant="caption"
              sx={{
                ml: "auto",
                color:
                  value.length > maxLength * 0.9
                    ? "warning.main"
                    : "text.secondary",
              }}
            >
              {value.length}/{maxLength}
            </Typography>
          )}
        </HelperTextContainer>
      )}
    </FieldContainer>
  );
};

export interface EnhancedSelectFieldProps {
  name: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: Array<{ value: string; label: string; disabled?: boolean }>;
  error?: string | null;
  helperText?: string;
  required?: boolean;
  disabled?: boolean;
  tooltip?: string;
  fullWidth?: boolean;
  placeholder?: string;
}

export const EnhancedSelectField: React.FC<EnhancedSelectFieldProps> = ({
  name,
  label,
  value,
  onChange,
  options,
  error,
  helperText,
  required = false,
  disabled = false,
  tooltip,
  fullWidth = true,
  placeholder = "Select an option",
}) => {
  const hasError = Boolean(error);
  const helperTextId = `${name}-helper-text`;
  const errorId = `${name}-error`;

  return (
    <FieldContainer>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
        <Typography
          variant="body2"
          component="label"
          htmlFor={name}
          sx={{ fontWeight: 500, color: "text.primary" }}
        >
          {label}
          {required && (
            <Typography component="span" sx={{ color: "error.main", ml: 0.5 }}>
              *
            </Typography>
          )}
        </Typography>
        {tooltip && (
          <Tooltip title={tooltip} arrow>
            <IconButton size="small" sx={{ p: 0.5 }}>
              <InfoIcon sx={{ fontSize: 16, color: "text.secondary" }} />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      <EnhancedTextField
        id={name}
        name={name}
        select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        error={hasError}
        disabled={disabled}
        fullWidth={fullWidth}
        SelectProps={{
          native: true,
          "aria-describedby": hasError ? errorId : helperTextId,
          "aria-invalid": hasError,
          "aria-label": label,
        }}
      >
        <option value="" disabled>
          {placeholder}
        </option>
        {options.map((option) => (
          <option
            key={option.value}
            value={option.value}
            disabled={option.disabled}
          >
            {option.label}
          </option>
        ))}
      </EnhancedTextField>

      {(error || helperText) && (
        <FormHelperText
          id={hasError ? errorId : helperTextId}
          error={hasError}
          sx={{ fontSize: "0.875rem" }}
        >
          {error || helperText}
        </FormHelperText>
      )}
    </FieldContainer>
  );
};

export interface EnhancedSwitchFieldProps {
  name: string;
  label: string;
  description?: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
  tooltip?: string;
}

export const EnhancedSwitchField: React.FC<EnhancedSwitchFieldProps> = ({
  name,
  label,
  description,
  checked,
  onChange,
  disabled = false,
  tooltip,
}) => {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "flex-start",
        gap: 2,
        p: 2,
        border: 1,
        borderColor: "divider",
        borderRadius: 1,
        bgcolor: disabled ? "action.disabled" : "background.paper",
        transition: "all 0.2s ease",
        "&:hover": disabled
          ? {}
          : {
              borderColor: "primary.main",
              bgcolor: (theme) => alpha(theme.palette.primary.main, 0.04),
            },
      }}
    >
      <Box sx={{ flex: 1 }}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          <Typography variant="body1" sx={{ fontWeight: 500 }}>
            {label}
          </Typography>
          {tooltip && (
            <Tooltip title={tooltip} arrow>
              <IconButton size="small" sx={{ p: 0.5 }}>
                <InfoIcon sx={{ fontSize: 16, color: "text.secondary" }} />
              </IconButton>
            </Tooltip>
          )}
        </Box>
        {description && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {description}
          </Typography>
        )}
      </Box>

      <Box
        component="label"
        sx={{
          position: "relative",
          display: "inline-block",
          width: 48,
          height: 24,
          cursor: disabled ? "not-allowed" : "pointer",
        }}
      >
        <HiddenCheckbox
          type="checkbox"
          name={name}
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          aria-label={label}
        />
        <Box
          sx={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: checked ? "primary.main" : "grey.300",
            borderRadius: 12,
            transition: "0.3s",
            opacity: disabled ? 0.5 : 1,
            "&:before": {
              position: "absolute",
              content: '""',
              height: 18,
              width: 18,
              left: checked ? 26 : 3,
              bottom: 3,
              backgroundColor: "white",
              borderRadius: "50%",
              transition: "0.3s",
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
            },
          }}
        />
      </Box>
    </Box>
  );
};
