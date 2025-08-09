import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import {
  userRegistrationSchema,
  userLoginSchema,
  userUpdateSchema,
  formCreationSchema,
  formUpdateSchema,
  reportCreationSchema,
  createFormSubmissionSchema,
  type UserRegistrationData,
  type UserLoginData,
  type UserUpdateData,
  type FormCreationData,
  type FormUpdateData,
  type ReportCreationData,
  type FormFieldData,
} from "./schemas";

// User registration form hook
export function useUserRegistrationForm(
  defaultValues?: Partial<UserRegistrationData>
) {
  return useForm<UserRegistrationData>({
    resolver: zodResolver(userRegistrationSchema),
    defaultValues: {
      email: "",
      password: "",
      confirmPassword: "",
      firstName: "",
      lastName: "",
      username: "",
      phone: "",
      company: "",
      jobTitle: "",
      ...defaultValues,
    },
    mode: "onChange",
  });
}

// User login form hook
export function useUserLoginForm(defaultValues?: Partial<UserLoginData>) {
  return useForm<UserLoginData>({
    resolver: zodResolver(userLoginSchema),
    defaultValues: {
      email: "",
      password: "",
      ...defaultValues,
    },
    mode: "onChange",
  });
}

// User profile update form hook
export function useUserUpdateForm(defaultValues?: Partial<UserUpdateData>) {
  return useForm<UserUpdateData>({
    resolver: zodResolver(userUpdateSchema),
    defaultValues: {
      firstName: "",
      lastName: "",
      phone: "",
      company: "",
      jobTitle: "",
      bio: "",
      timezone: "",
      language: "en",
      theme: "light",
      emailNotifications: true,
      pushNotifications: true,
      ...defaultValues,
    },
    mode: "onChange",
  });
}

// Form creation form hook (simplified to avoid TypeScript issues)
export function useFormCreationForm(defaultValues?: Partial<FormCreationData>) {
  return useForm({
    resolver: zodResolver(formCreationSchema),
    defaultValues: {
      title: "",
      description: "",
      isPublic: false,
      isActive: true,
      schema: {
        fields: [
          {
            id: "name",
            type: "text" as const,
            label: "Full Name",
            required: true,
            placeholder: "Enter your full name",
          },
        ],
      },
      formSettings: {
        theme: "default",
        submitButtonText: "Submit",
        successMessage: "Thank you for your submission!",
        allowMultipleSubmissions: false,
        showProgressBar: false,
        requireAuth: false,
      },
      ...defaultValues,
    },
    mode: "onChange" as const,
  });
}

// Form update form hook (simplified to avoid TypeScript issues)
export function useFormUpdateForm(defaultValues?: Partial<FormUpdateData>) {
  return useForm({
    resolver: zodResolver(formUpdateSchema),
    defaultValues,
    mode: "onChange" as const,
  });
}

// Dynamic form submission hook
export function useFormSubmissionForm(formSchema: { fields: FormFieldData[] }) {
  const schema = createFormSubmissionSchema(formSchema);
  type SubmissionData = z.infer<typeof schema>;

  // Create default values based on form fields
  const defaultValues: Partial<SubmissionData> = {
    data: formSchema.fields.reduce((acc, field) => {
      if (field.defaultValue !== undefined) {
        acc[field.id] = field.defaultValue;
      } else {
        switch (field.type) {
          case "checkbox":
            acc[field.id] = false;
            break;
          case "number":
            acc[field.id] = field.validation?.min || 0;
            break;
          default:
            acc[field.id] = "";
        }
      }
      return acc;
    }, {} as Record<string, unknown>),
  };

  return useForm<SubmissionData>({
    resolver: zodResolver(schema),
    defaultValues,
    mode: "onChange",
  });
}

// Report creation form hook
export function useReportCreationForm(
  defaultValues?: Partial<ReportCreationData>
) {
  return useForm<ReportCreationData>({
    resolver: zodResolver(reportCreationSchema),
    defaultValues: {
      title: "",
      description: "",
      templateId: "generic",
      data: {},
      ...defaultValues,
    },
    mode: "onChange",
  });
}

// Validation utilities
export const ValidationUtils = {
  // Check if field has errors
  hasFieldError: (
    errors: Record<string, unknown>,
    fieldName: string
  ): boolean => {
    return !!errors[fieldName];
  },

  // Get field error message
  getFieldError: (
    errors: Record<string, unknown>,
    fieldName: string
  ): string | undefined => {
    const error = errors[fieldName] as { message?: string } | undefined;
    return error?.message;
  },

  // Check if nested field has errors
  hasNestedFieldError: (
    errors: Record<string, unknown>,
    path: string[]
  ): boolean => {
    let current = errors;
    for (const key of path) {
      if (!current[key]) return false;
      current = current[key] as Record<string, unknown>;
    }
    return true;
  },

  // Get nested field error message
  getNestedFieldError: (
    errors: Record<string, unknown>,
    path: string[]
  ): string | undefined => {
    let current = errors;
    for (const key of path) {
      if (!current[key]) return undefined;
      current = current[key] as Record<string, unknown>;
    }
    return (current as { message?: string })?.message;
  },

  // Format error messages for display
  formatErrorMessage: (error: string): string => {
    // Capitalize first letter and ensure proper punctuation
    const formatted = error.charAt(0).toUpperCase() + error.slice(1);
    return formatted.endsWith(".") ||
      formatted.endsWith("!") ||
      formatted.endsWith("?")
      ? formatted
      : formatted + ".";
  },

  // Validate single field manually
  validateField: async (
    schema: z.ZodTypeAny,
    value: unknown
  ): Promise<{ isValid: boolean; error?: string }> => {
    try {
      await schema.parseAsync(value);
      return { isValid: true };
    } catch (error) {
      if (error instanceof z.ZodError) {
        return {
          isValid: false,
          error: error.issues[0]?.message || "Validation failed",
        };
      }
      return { isValid: false, error: "Validation failed" };
    }
  },

  // Check if form data is valid without submitting
  checkFormValidity: async (
    schema: z.ZodTypeAny,
    data: unknown
  ): Promise<{ isValid: boolean; errors?: Record<string, string> }> => {
    try {
      await schema.parseAsync(data);
      return { isValid: true };
    } catch (error) {
      if (error instanceof z.ZodError) {
        const errors = error.issues.reduce(
          (acc: Record<string, string>, err) => {
            const path = err.path.join(".");
            acc[path] = err.message;
            return acc;
          },
          {}
        );
        return { isValid: false, errors };
      }
      return { isValid: false, errors: { general: "Validation failed" } };
    }
  },
};

// Field validation status type
export type FieldValidationStatus = {
  isValid: boolean;
  error?: string;
  isValidating?: boolean;
};

// Form validation context type
export type FormValidationContext = {
  validateField: (
    fieldName: string,
    value: unknown
  ) => Promise<FieldValidationStatus>;
  validateForm: (
    data: unknown
  ) => Promise<{ isValid: boolean; errors?: Record<string, string> }>;
  clearFieldError: (fieldName: string) => void;
  clearAllErrors: () => void;
  hasErrors: boolean;
  isValidating: boolean;
};
