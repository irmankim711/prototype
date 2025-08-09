import { z } from "zod";

// Common validation patterns
export const ValidationPatterns = {
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  phone: /^\+?[\d\s\-()]+$/,
  url: /^https?:\/\/.+/,
  password: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/,
  username: /^[a-zA-Z][a-zA-Z0-9_]*$/,
  fieldId: /^[a-zA-Z][a-zA-Z0-9_]*$/,
};

// User registration schema
export const userRegistrationSchema = z
  .object({
    email: z
      .string()
      .min(1, "Email is required")
      .email("Please enter a valid email address")
      .max(120, "Email cannot exceed 120 characters"),

    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .max(128, "Password cannot exceed 128 characters")
      .regex(
        ValidationPatterns.password,
        "Password must contain uppercase, lowercase, number, and special character"
      ),

    confirmPassword: z.string(),

    firstName: z
      .string()
      .max(50, "First name cannot exceed 50 characters")
      .optional(),

    lastName: z
      .string()
      .max(50, "Last name cannot exceed 50 characters")
      .optional(),

    username: z
      .string()
      .min(3, "Username must be at least 3 characters")
      .max(50, "Username cannot exceed 50 characters")
      .regex(
        ValidationPatterns.username,
        "Username must start with a letter and contain only letters, numbers, and underscores"
      )
      .optional(),

    phone: z
      .string()
      .regex(ValidationPatterns.phone, "Please enter a valid phone number")
      .max(20, "Phone number cannot exceed 20 characters")
      .optional(),

    company: z
      .string()
      .max(100, "Company name cannot exceed 100 characters")
      .optional(),

    jobTitle: z
      .string()
      .max(100, "Job title cannot exceed 100 characters")
      .optional(),
  })
  .refine((data: any) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
  });

// User login schema
export const userLoginSchema = z.object({
  email: z
    .string()
    .min(1, "Email is required")
    .email("Please enter a valid email address"),

  password: z.string().min(1, "Password is required"),
});

// User profile update schema
export const userUpdateSchema = z.object({
  firstName: z
    .string()
    .max(50, "First name cannot exceed 50 characters")
    .optional(),

  lastName: z
    .string()
    .max(50, "Last name cannot exceed 50 characters")
    .optional(),

  phone: z
    .string()
    .regex(ValidationPatterns.phone, "Please enter a valid phone number")
    .max(20, "Phone number cannot exceed 20 characters")
    .optional()
    .or(z.literal("")),

  company: z
    .string()
    .max(100, "Company name cannot exceed 100 characters")
    .optional()
    .or(z.literal("")),

  jobTitle: z
    .string()
    .max(100, "Job title cannot exceed 100 characters")
    .optional()
    .or(z.literal("")),

  bio: z
    .string()
    .max(500, "Bio cannot exceed 500 characters")
    .optional()
    .or(z.literal("")),

  timezone: z
    .string()
    .max(50, "Timezone cannot exceed 50 characters")
    .optional(),

  language: z.enum(["en", "es", "fr", "de", "it"]).optional(),

  theme: z.enum(["light", "dark"]).optional(),

  emailNotifications: z.boolean().optional(),
  pushNotifications: z.boolean().optional(),
});

// Form field schema
export const formFieldSchema = z
  .object({
    id: z
      .string()
      .min(1, "Field ID is required")
      .regex(
        ValidationPatterns.fieldId,
        "Field ID must start with a letter and contain only letters, numbers, and underscores"
      ),

    type: z.enum([
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
    ]),

    label: z
      .string()
      .min(1, "Field label is required")
      .max(200, "Field label cannot exceed 200 characters"),

    placeholder: z
      .string()
      .max(200, "Placeholder cannot exceed 200 characters")
      .optional(),

    required: z.boolean().default(false),

    options: z
      .array(
        z.object({
          value: z.string(),
          label: z.string(),
        })
      )
      .optional(),

    validation: z
      .object({
        minLength: z.number().min(0).optional(),
        maxLength: z.number().min(1).optional(),
        min: z.number().optional(),
        max: z.number().optional(),
        pattern: z.string().optional(),
      })
      .optional(),

    defaultValue: z.any().optional(),

    description: z
      .string()
      .max(500, "Description cannot exceed 500 characters")
      .optional(),
  })
  .refine(
    (data: any) => {
      // Validate that select/radio fields have options
      if (
        ["select", "radio"].includes(data.type) &&
        (!data.options || data.options.length === 0)
      ) {
        return false;
      }
      return true;
    },
    {
      message: "Select and radio fields must have at least one option",
      path: ["options"],
    }
  )
  .refine(
    (data: any) => {
      // Validate minLength <= maxLength
      if (data.validation?.minLength && data.validation?.maxLength) {
        return data.validation.minLength <= data.validation.maxLength;
      }
      return true;
    },
    {
      message: "Minimum length cannot be greater than maximum length",
      path: ["validation", "minLength"],
    }
  );

// Form creation schema
export const formCreationSchema = z.object({
  title: z
    .string()
    .min(3, "Form title must be at least 3 characters")
    .max(200, "Form title cannot exceed 200 characters"),

  description: z
    .string()
    .max(1000, "Description cannot exceed 1000 characters")
    .optional()
    .or(z.literal("")),

  isPublic: z.boolean().default(false),
  isActive: z.boolean().default(true),

  schema: z.object({
    fields: z
      .array(formFieldSchema)
      .min(1, "Form must have at least one field")
      .refine(
        (fields: any) => {
          // Check for unique field IDs
          const ids = fields.map((field: any) => field.id);
          const uniqueIds = new Set(ids);
          return ids.length === uniqueIds.size;
        },
        {
          message: "Field IDs must be unique",
        }
      ),
  }),

  formSettings: z
    .object({
      theme: z.string().optional(),
      submitButtonText: z.string().optional(),
      successMessage: z.string().optional(),
      allowMultipleSubmissions: z.boolean().optional(),
      showProgressBar: z.boolean().optional(),
      requireAuth: z.boolean().optional(),
    })
    .optional(),

  submissionLimit: z
    .number()
    .min(1, "Submission limit must be at least 1")
    .optional(),

  expiresAt: z
    .string()
    .datetime()
    .refine((date: any) => new Date(date) > new Date(), {
      message: "Expiration date must be in the future",
    })
    .optional(),
});

// Form update schema (same as creation but all fields optional except schema validation)
export const formUpdateSchema = formCreationSchema.partial().extend({
  schema: z
    .object({
      fields: z
        .array(formFieldSchema)
        .min(1, "Form must have at least one field")
        .refine(
          (fields: any) => {
            const ids = fields.map((field: any) => field.id);
            const uniqueIds = new Set(ids);
            return ids.length === uniqueIds.size;
          },
          {
            message: "Field IDs must be unique",
          }
        ),
    })
    .optional(),
});

// Dynamic form submission schema generator
export const createFormSubmissionSchema = (formSchema: {
  fields: FormFieldData[];
}) => {
  if (!formSchema || !formSchema.fields) {
    return z.object({
      data: z.record(z.string(), z.any()),
    });
  }

  const dataSchema: { [key: string]: z.ZodTypeAny } = {};

  formSchema.fields.forEach((field: FormFieldData) => {
    let fieldSchema: z.ZodTypeAny;

    switch (field.type) {
      case "email":
        fieldSchema = z.string().email("Please enter a valid email address");
        break;

      case "number":
        fieldSchema = z.coerce.number();
        if (field.validation?.min !== undefined) {
          fieldSchema = (fieldSchema as z.ZodNumber).min(field.validation.min);
        }
        if (field.validation?.max !== undefined) {
          fieldSchema = (fieldSchema as z.ZodNumber).max(field.validation.max);
        }
        break;

      case "tel":
        fieldSchema = z
          .string()
          .regex(ValidationPatterns.phone, "Please enter a valid phone number");
        break;

      case "url":
        fieldSchema = z.string().url("Please enter a valid URL");
        break;

      case "date":
        fieldSchema = z
          .string()
          .regex(/^\d{4}-\d{2}-\d{2}$/, "Please enter a valid date");
        break;

      case "checkbox":
        fieldSchema = z.boolean();
        break;

      case "select":
      case "radio":
        if (field.options && field.options.length > 0) {
          const validValues = field.options.map(
            (opt: { value: string; label: string }) => opt.value
          );
          fieldSchema = z.enum(validValues as [string, ...string[]]);
        } else {
          fieldSchema = z.string();
        }
        break;

      default:
        fieldSchema = z.string();

        // Apply string validations
        if (field.validation?.minLength) {
          fieldSchema = (fieldSchema as z.ZodString).min(
            field.validation.minLength,
            `${field.label} must be at least ${field.validation.minLength} characters`
          );
        }
        if (field.validation?.maxLength) {
          fieldSchema = (fieldSchema as z.ZodString).max(
            field.validation.maxLength,
            `${field.label} cannot exceed ${field.validation.maxLength} characters`
          );
        }
        if (field.validation?.pattern) {
          fieldSchema = (fieldSchema as z.ZodString).regex(
            new RegExp(field.validation.pattern),
            `${field.label} format is invalid`
          );
        }
    }

    // Handle required fields
    if (field.required) {
      if (field.type === "checkbox") {
        fieldSchema = (fieldSchema as z.ZodBoolean).refine(
          (val: any) => val === true,
          {
            message: `${field.label} is required`,
          }
        );
      } else {
        fieldSchema = fieldSchema.refine(
          (val: any) => val !== undefined && val !== null && val !== "",
          {
            message: `${field.label} is required`,
          }
        );
      }
    } else {
      fieldSchema = fieldSchema.optional();
    }

    dataSchema[field.id] = fieldSchema;
  });

  return z.object({
    data: z.object(dataSchema),
    submitterEmail: z.string().email().optional(),
  });
};

// Report creation schema
export const reportCreationSchema = z.object({
  title: z
    .string()
    .min(3, "Report title must be at least 3 characters")
    .max(120, "Report title cannot exceed 120 characters"),

  description: z
    .string()
    .max(500, "Description cannot exceed 500 characters")
    .optional()
    .or(z.literal("")),

  templateId: z.enum(["form_analysis", "generic", "custom"]).optional(),

  data: z.record(z.string(), z.any()).optional(),
});

// Pagination schema
export const paginationSchema = z.object({
  page: z.coerce.number().min(1, "Page must be greater than 0").default(1),
  perPage: z.coerce
    .number()
    .min(1)
    .max(100, "Per page must be between 1 and 100")
    .default(20),
  sortBy: z.string().optional(),
  sortOrder: z.enum(["asc", "desc"]).default("asc"),
});

// Export types for TypeScript
export type UserRegistrationData = z.infer<typeof userRegistrationSchema>;
export type UserLoginData = z.infer<typeof userLoginSchema>;
export type UserUpdateData = z.infer<typeof userUpdateSchema>;
export type FormFieldData = z.infer<typeof formFieldSchema>;
export type FormCreationData = z.infer<typeof formCreationSchema>;
export type FormUpdateData = z.infer<typeof formUpdateSchema>;
export type ReportCreationData = z.infer<typeof reportCreationSchema>;
export type PaginationData = z.infer<typeof paginationSchema>;
