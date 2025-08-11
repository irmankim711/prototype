import { z } from "zod";

// Enhanced validation patterns for user profile
export const UserProfileValidationPatterns = {
  phone: /^(\+\d{1,3}[- ]?)?\d{10}$/,
  username: /^[a-zA-Z][a-zA-Z0-9_]{2,29}$/,
  name: /^[a-zA-Z\s'-]{1,50}$/,
  company: /^[a-zA-Z0-9\s.,'&-]{1,100}$/,
  jobTitle: /^[a-zA-Z0-9\s.,'&-]{1,100}$/,
};

// Enhanced user profile validation schema
export const enhancedUserProfileSchema = z
  .object({
    first_name: z
      .string()
      .refine(
        (val) =>
          val.trim().length === 0 ||
          (val.trim().length >= 1 && val.trim().length <= 50),
        "First name must be between 1 and 50 characters"
      )
      .refine(
        (val) =>
          val.trim().length === 0 ||
          UserProfileValidationPatterns.name.test(val.trim()),
        "First name can only contain letters, spaces, apostrophes, and hyphens"
      ),

    last_name: z
      .string()
      .refine(
        (val) =>
          val.trim().length === 0 ||
          (val.trim().length >= 1 && val.trim().length <= 50),
        "Last name must be between 1 and 50 characters"
      )
      .refine(
        (val) =>
          val.trim().length === 0 ||
          UserProfileValidationPatterns.name.test(val.trim()),
        "Last name can only contain letters, spaces, apostrophes, and hyphens"
      ),

    username: z
      .string()
      .min(3, "Username must be at least 3 characters")
      .max(30, "Username cannot exceed 30 characters")
      .regex(
        UserProfileValidationPatterns.username,
        "Username must start with a letter and contain only letters, numbers, and underscores"
      ),

    phone: z
      .string()
      .refine(
        (val) =>
          val.trim().length === 0 ||
          UserProfileValidationPatterns.phone.test(val.replace(/\s/g, "")),
        "Please enter a valid phone number (e.g., +1234567890 or 1234567890)"
      ),

    company: z
      .string()
      .refine(
        (val) =>
          val.trim().length === 0 ||
          (val.trim().length >= 1 && val.trim().length <= 100),
        "Company name must be between 1 and 100 characters"
      )
      .refine(
        (val) =>
          val.trim().length === 0 ||
          UserProfileValidationPatterns.company.test(val.trim()),
        "Company name contains invalid characters"
      ),

    job_title: z
      .string()
      .refine(
        (val) =>
          val.trim().length === 0 ||
          (val.trim().length >= 1 && val.trim().length <= 100),
        "Job title must be between 1 and 100 characters"
      )
      .refine(
        (val) =>
          val.trim().length === 0 ||
          UserProfileValidationPatterns.jobTitle.test(val.trim()),
        "Job title contains invalid characters"
      ),

    bio: z
      .string()
      .refine(
        (val) => val.trim().length <= 500,
        "Bio cannot exceed 500 characters"
      ),

    timezone: z.string().min(1, "Please select a timezone"),

    language: z.string().min(1, "Please select a language"),

    theme: z.string().min(1, "Please select a theme"),

    email_notifications: z.boolean(),

    push_notifications: z.boolean(),
  })
  .refine((data) => data.first_name.trim() || data.last_name.trim(), {
    message: "Please provide at least a first name or last name",
    path: ["first_name"],
  });

export type EnhancedUserProfileData = z.infer<typeof enhancedUserProfileSchema>;

// Field-specific validation functions
export const validateField = (
  fieldName: string,
  value: unknown
): string | null => {
  try {
    const fieldSchema =
      enhancedUserProfileSchema.shape[
        fieldName as keyof typeof enhancedUserProfileSchema.shape
      ];
    if (fieldSchema) {
      fieldSchema.parse(value);
      return null;
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      return error.issues[0]?.message || "Invalid value";
    }
  }
  return null;
};

// Real-time validation helper
export const validateUserProfile = (data: Partial<EnhancedUserProfileData>) => {
  const errors: Record<string, string> = {};

  try {
    enhancedUserProfileSchema.parse(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      error.issues.forEach((err) => {
        const field = err.path[0];
        if (field && typeof field === "string") {
          errors[field] = err.message;
        }
      });
    }
  }

  return errors;
};

// Helper functions for form validation
export const sanitizeFormData = (
  data: Record<string, unknown>
): EnhancedUserProfileData => {
  return {
    first_name: (data.first_name as string)?.trim() || "",
    last_name: (data.last_name as string)?.trim() || "",
    username: (data.username as string)?.trim() || "",
    phone: (data.phone as string)?.trim() || "",
    company: (data.company as string)?.trim() || "",
    job_title: (data.job_title as string)?.trim() || "",
    bio: (data.bio as string)?.trim() || "",
    timezone: (data.timezone as string) || "UTC",
    language: (data.language as string) || "en",
    theme: (data.theme as string) || "light",
    email_notifications: Boolean(data.email_notifications),
    push_notifications: Boolean(data.push_notifications),
  };
};

export const hasFormChanges = (
  original: Record<string, unknown>,
  current: Record<string, unknown>
): boolean => {
  const fields = [
    "first_name",
    "last_name",
    "username",
    "phone",
    "company",
    "job_title",
    "bio",
    "timezone",
    "language",
    "theme",
    "email_notifications",
    "push_notifications",
  ];

  return fields.some((field) => {
    const originalValue = original[field]?.toString().trim() || "";
    const currentValue = current[field]?.toString().trim() || "";
    return originalValue !== currentValue;
  });
};
