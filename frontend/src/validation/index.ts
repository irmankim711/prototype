// Export all validation schemas
export * from "./schemas";

// Export validation hooks
export * from "./hooks";

// Export validation components
export * from "./components";

// Re-export commonly used types from zod
export { z } from "zod";

// Validation utilities and constants
export const VALIDATION_MESSAGES = {
  REQUIRED: "This field is required",
  EMAIL_INVALID: "Please enter a valid email address",
  PASSWORD_TOO_SHORT: "Password must be at least 8 characters",
  PASSWORD_WEAK:
    "Password must contain uppercase, lowercase, number, and special character",
  PASSWORDS_DONT_MATCH: "Passwords don't match",
  PHONE_INVALID: "Please enter a valid phone number",
  URL_INVALID: "Please enter a valid URL",
  MIN_LENGTH: (min: number) => `Must be at least ${min} characters`,
  MAX_LENGTH: (max: number) => `Cannot exceed ${max} characters`,
  MIN_VALUE: (min: number) => `Must be at least ${min}`,
  MAX_VALUE: (max: number) => `Cannot exceed ${max}`,
  FIELD_ID_INVALID:
    "Field ID must start with a letter and contain only letters, numbers, and underscores",
  UNIQUE_FIELD_IDS: "Field IDs must be unique",
  FORM_MUST_HAVE_FIELDS: "Form must have at least one field",
  EXPIRATION_FUTURE: "Expiration date must be in the future",
  SELECT_RADIO_NEEDS_OPTIONS:
    "Select and radio fields must have at least one option",
} as const;

export const FIELD_TYPES = [
  "text",
  "textarea",
  "email",
  "number",
  "tel",
  "url",
  "password",
  "date",
  "time",
  "datetime-local",
  "checkbox",
  "radio",
  "select",
  "file",
  "hidden",
  "range",
  "color",
] as const;

export const SUPPORTED_LANGUAGES = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "it", label: "Italian" },
] as const;

export const THEME_OPTIONS = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
] as const;

export const REPORT_TEMPLATES = [
  { value: "form_analysis", label: "Form Analysis Report" },
  { value: "generic", label: "Generic Report" },
  { value: "custom", label: "Custom Report" },
] as const;
