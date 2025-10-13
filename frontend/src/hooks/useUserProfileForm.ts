import { useState, useCallback, useEffect } from "react";
import {
  validateField,
  validateUserProfile,
  sanitizeFormData,
  hasFormChanges,
} from "../utils/userProfileValidation";
import type { EnhancedUserProfileData } from "../utils/userProfileValidation";

interface UseUserProfileFormOptions {
  initialData?: Partial<EnhancedUserProfileData>;
  onSubmit?: (data: EnhancedUserProfileData) => Promise<void>;
  onCancel?: () => void;
  validateOnChange?: boolean;
}

export interface UserProfileFormState {
  data: EnhancedUserProfileData;
  errors: Record<string, string>;
  isLoading: boolean;
  isValid: boolean;
  isDirty: boolean;
  touchedFields: Set<string>;
}

export interface UserProfileFormActions {
  updateField: (field: keyof EnhancedUserProfileData, value: unknown) => void;
  updateMultipleFields: (updates: Partial<EnhancedUserProfileData>) => void;
  validateSingleField: (field: keyof EnhancedUserProfileData) => string | null;
  validateAllFields: () => Record<string, string>;
  handleSubmit: () => Promise<void>;
  handleCancel: () => void;
  reset: (newData?: Partial<EnhancedUserProfileData>) => void;
  clearErrors: () => void;
  clearFieldError: (field: keyof EnhancedUserProfileData) => void;
  markFieldTouched: (field: keyof EnhancedUserProfileData) => void;
  setLoading: (loading: boolean) => void;
}

const defaultFormData: EnhancedUserProfileData = {
  first_name: "",
  last_name: "",
  username: "",
  phone: "",
  company: "",
  job_title: "",
  bio: "",
  timezone: "UTC",
  language: "en",
  theme: "light",
  email_notifications: true,
  push_notifications: false,
};

export const useUserProfileForm = (
  options: UseUserProfileFormOptions = {}
): [UserProfileFormState, UserProfileFormActions] => {
  const {
    initialData = {},
    onSubmit,
    onCancel,
    validateOnChange = true,
  } = options;

  const [originalData] = useState<EnhancedUserProfileData>(() => ({
    ...defaultFormData,
    ...initialData,
  }));

  const [formState, setFormState] = useState<UserProfileFormState>(() => ({
    data: { ...defaultFormData, ...initialData },
    errors: {},
    isLoading: false,
    isValid: true,
    isDirty: false,
    touchedFields: new Set<string>(),
  }));

  // Validate form whenever data changes
  useEffect(() => {
    if (validateOnChange) {
      const errors = validateUserProfile(formState.data);
      const isValid = Object.keys(errors).length === 0;
      const isDirty = hasFormChanges(originalData, formState.data);

      setFormState((prev) => ({
        ...prev,
        errors,
        isValid,
        isDirty,
      }));
    }
  }, [formState.data, validateOnChange, originalData]);

  const updateField = useCallback(
    (field: keyof EnhancedUserProfileData, value: unknown) => {
      setFormState((prev) => {
        const newData = { ...prev.data, [field]: value };
        const fieldError = validateOnChange
          ? validateField(field, value)
          : null;
        const newErrors = { ...prev.errors };

        if (fieldError) {
          newErrors[field] = fieldError;
        } else {
          delete newErrors[field];
        }

        return {
          ...prev,
          data: newData,
          errors: newErrors,
          touchedFields: new Set([...prev.touchedFields, field]),
        };
      });
    },
    [validateOnChange]
  );

  const updateMultipleFields = useCallback(
    (updates: Partial<EnhancedUserProfileData>) => {
      setFormState((prev) => {
        const newData = { ...prev.data, ...updates };
        const errors = validateOnChange
          ? validateUserProfile(newData)
          : prev.errors;
        const newTouchedFields = new Set([
          ...prev.touchedFields,
          ...(Object.keys(updates) as (keyof EnhancedUserProfileData)[]),
        ]);

        return {
          ...prev,
          data: newData,
          errors,
          touchedFields: newTouchedFields,
        };
      });
    },
    [validateOnChange]
  );

  const validateSingleField = useCallback(
    (field: keyof EnhancedUserProfileData): string | null => {
      const value = formState.data[field];
      return validateField(field, value);
    },
    [formState.data]
  );

  const validateAllFields = useCallback((): Record<string, string> => {
    const errors = validateUserProfile(formState.data);
    setFormState((prev) => ({ ...prev, errors }));
    return errors;
  }, [formState.data]);

  const handleSubmit = useCallback(async (): Promise<void> => {
    if (!onSubmit) return;

    // Mark all fields as touched
    setFormState((prev) => ({
      ...prev,
      touchedFields: new Set(
        Object.keys(prev.data) as (keyof EnhancedUserProfileData)[]
      ),
    }));

    // Validate all fields
    const errors = validateAllFields();

    if (Object.keys(errors).length > 0) {
      throw new Error("Please fix validation errors before submitting");
    }

    setFormState((prev) => ({ ...prev, isLoading: true }));

    try {
      const sanitizedData = sanitizeFormData(formState.data);
      await onSubmit(sanitizedData);
    } finally {
      setFormState((prev) => ({ ...prev, isLoading: false }));
    }
  }, [onSubmit, formState.data, validateAllFields]);

  const handleCancel = useCallback(() => {
    setFormState((prev) => ({
      ...prev,
      data: { ...originalData },
      errors: {},
      touchedFields: new Set(),
    }));
    onCancel?.();
  }, [originalData, onCancel]);

  const reset = useCallback((newData?: Partial<EnhancedUserProfileData>) => {
    const resetData = { ...defaultFormData, ...newData };
    setFormState({
      data: resetData,
      errors: {},
      isLoading: false,
      isValid: true,
      isDirty: false,
      touchedFields: new Set(),
    });
  }, []);

  const clearErrors = useCallback(() => {
    setFormState((prev) => ({ ...prev, errors: {} }));
  }, []);

  const clearFieldError = useCallback(
    (field: keyof EnhancedUserProfileData) => {
      setFormState((prev) => {
        const newErrors = { ...prev.errors };
        delete newErrors[field];
        return { ...prev, errors: newErrors };
      });
    },
    []
  );

  const markFieldTouched = useCallback(
    (field: keyof EnhancedUserProfileData) => {
      setFormState((prev) => ({
        ...prev,
        touchedFields: new Set([...prev.touchedFields, field]),
      }));
    },
    []
  );

  const setLoading = useCallback((loading: boolean) => {
    setFormState((prev) => ({ ...prev, isLoading: loading }));
  }, []);

  return [
    formState,
    {
      updateField,
      updateMultipleFields,
      validateSingleField,
      validateAllFields,
      handleSubmit,
      handleCancel,
      reset,
      clearErrors,
      clearFieldError,
      markFieldTouched,
      setLoading,
    },
  ];
};

// Additional helper hook for field-specific validation
export const useFieldValidation = (
  field: keyof EnhancedUserProfileData,
  value: unknown,
  touched: boolean = false
) => {
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (touched) {
      const validationError = validateField(field, value);
      setError(validationError);
    }
  }, [field, value, touched]);

  return error;
};
