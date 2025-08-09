import React from "react";
import {
  FormField,
  TextInput,
  SubmitButton,
  ErrorMessage,
  SuccessMessage,
} from "../validation/components";
import { useUserRegistrationForm } from "../validation/hooks";

const UserRegistrationForm: React.FC = () => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    clearErrors,
  } = useUserRegistrationForm();

  const [submitError, setSubmitError] = React.useState<string>("");
  const [submitSuccess, setSubmitSuccess] = React.useState<string>("");

  const onSubmit = async (data: Record<string, unknown>) => {
    try {
      setSubmitError("");
      setSubmitSuccess("");
      clearErrors();

      // Simulate API call
      console.log("Submitting user registration:", data);

      // Mock API response
      await new Promise((resolve: any) => setTimeout(resolve, 1000));

      // Simulate random success/error for demo
      if (Math.random() > 0.3) {
        setSubmitSuccess(
          "Registration successful! Please check your email to verify your account."
        );
      } else {
        throw Error("Registration failed. Please try again.");
      }
    } catch (error) {
      setSubmitError(
        error instanceof Error ? error.message : "An unexpected error occurred"
      );
    }
  };

  // Helper function to display form errors
  const hasErrors = Object.keys(errors).length > 0;

  return (
    <div className="max-w-md mx-auto bg-white shadow-lg rounded-lg p-6">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Create Account</h2>

      <ErrorMessage message={submitError} />
      <SuccessMessage message={submitSuccess} />

      {hasErrors && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
          <p className="text-sm font-medium">
            Please fix the following errors:
          </p>
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate>
        <FormField
          label="Email Address"
          error={errors.email}
          required
          description="We'll use this to send you important updates"
        >
          <TextInput
            {...register("email")}
            type="email"
            placeholder="Enter your email address"
            error={errors.email}
            autoComplete="email"
          />
        </FormField>

        <FormField
          label="Password"
          error={errors.password}
          required
          description="Must be at least 8 characters with uppercase, lowercase, number, and special character"
        >
          <TextInput
            {...register("password")}
            type="password"
            placeholder="Create a strong password"
            error={errors.password}
            autoComplete="new-password"
          />
        </FormField>

        <FormField
          label="Confirm Password"
          error={errors.confirmPassword}
          required
        >
          <TextInput
            {...register("confirmPassword")}
            type="password"
            placeholder="Confirm your password"
            error={errors.confirmPassword}
            autoComplete="new-password"
          />
        </FormField>

        <div className="grid grid-cols-2 gap-4">
          <FormField label="First Name" error={errors.firstName}>
            <TextInput
              {...register("firstName")}
              placeholder="First name"
              error={errors.firstName}
              autoComplete="given-name"
            />
          </FormField>

          <FormField label="Last Name" error={errors.lastName}>
            <TextInput
              {...register("lastName")}
              placeholder="Last name"
              error={errors.lastName}
              autoComplete="family-name"
            />
          </FormField>
        </div>

        <FormField
          label="Username"
          error={errors.username}
          description="Optional - used for personalized URL"
        >
          <TextInput
            {...register("username")}
            placeholder="Choose a username"
            error={errors.username}
            autoComplete="username"
          />
        </FormField>

        <FormField
          label="Phone Number"
          error={errors.phone}
          description="Optional - for account recovery"
        >
          <TextInput
            {...register("phone")}
            type="tel"
            placeholder="+1 (555) 123-4567"
            error={errors.phone}
            autoComplete="tel"
          />
        </FormField>

        <FormField
          label="Company"
          error={errors.company}
          description="Optional"
        >
          <TextInput
            {...register("company")}
            placeholder="Your company name"
            error={errors.company}
            autoComplete="organization"
          />
        </FormField>

        <FormField
          label="Job Title"
          error={errors.jobTitle}
          description="Optional"
        >
          <TextInput
            {...register("jobTitle")}
            placeholder="Your job title"
            error={errors.jobTitle}
            autoComplete="organization-title"
          />
        </FormField>

        <div className="mt-6">
          <SubmitButton
            loading={isSubmitting}
            loadingText="Creating Account..."
          >
            Create Account
          </SubmitButton>
        </div>

        <div className="mt-4 text-center">
          <p className="text-sm text-gray-600">
            Already have an account?{" "}
            <a
              href="/login"
              className="text-blue-600 hover:text-blue-500 font-medium"
            >
              Sign in
            </a>
          </p>
        </div>
      </form>
    </div>
  );
};

export default UserRegistrationForm;
