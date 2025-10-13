// cypress/e2e/02-form-creation.cy.js
describe("Form Creation and Management", () => {
  beforeEach(() => {
    cy.login();
    cy.visit("/dashboard");
  });

  it("should create a new form successfully", () => {
    cy.get('[data-testid="create-form-button"]').click();
    cy.url().should("include", "/forms/create");

    // Fill form details
    cy.get('[data-testid="form-title-input"]').type("Employee Feedback Form");
    cy.get('[data-testid="form-description-input"]').type(
      "Quarterly employee feedback survey"
    );

    // Add form fields
    cy.get('[data-testid="add-field-button"]').click();
    cy.get('[data-testid="field-type-select"]').select("text");
    cy.get('[data-testid="field-label-input"]').type("Employee Name");
    cy.get('[data-testid="field-required-checkbox"]').check();
    cy.get('[data-testid="save-field-button"]').click();

    // Add rating field
    cy.get('[data-testid="add-field-button"]').click();
    cy.get('[data-testid="field-type-select"]').select("rating");
    cy.get('[data-testid="field-label-input"]').type("Overall Satisfaction");
    cy.get('[data-testid="rating-scale-input"]').type("5");
    cy.get('[data-testid="save-field-button"]').click();

    // Add text area field
    cy.get('[data-testid="add-field-button"]').click();
    cy.get('[data-testid="field-type-select"]').select("textarea");
    cy.get('[data-testid="field-label-input"]').type("Additional Comments");
    cy.get('[data-testid="save-field-button"]').click();

    // Save form
    cy.get('[data-testid="save-form-button"]').click();
    cy.get('[data-testid="success-message"]').should("be.visible");
    cy.get('[data-testid="success-message"]').should(
      "contain",
      "Form created successfully"
    );

    // Verify form appears in list
    cy.visit("/forms");
    cy.get('[data-testid="forms-list"]').should(
      "contain",
      "Employee Feedback Form"
    );
  });

  it("should edit existing form", () => {
    // First create a form
    const formData = {
      title: "Test Form for Editing",
      description: "Test description",
      fields: [{ type: "text", label: "Name", required: true }],
    };

    cy.createForm(formData).then((form) => {
      cy.visit(`/forms/${form.id}/edit`);

      // Edit form title
      cy.get('[data-testid="form-title-input"]')
        .clear()
        .type("Updated Test Form");

      // Add new field
      cy.get('[data-testid="add-field-button"]').click();
      cy.get('[data-testid="field-type-select"]').select("email");
      cy.get('[data-testid="field-label-input"]').type("Email Address");
      cy.get('[data-testid="field-required-checkbox"]').check();
      cy.get('[data-testid="save-field-button"]').click();

      // Save changes
      cy.get('[data-testid="save-form-button"]').click();
      cy.get('[data-testid="success-message"]').should("be.visible");

      // Verify changes
      cy.visit("/forms");
      cy.get('[data-testid="forms-list"]').should(
        "contain",
        "Updated Test Form"
      );
    });
  });

  it("should preview form correctly", () => {
    const formData = {
      title: "Preview Test Form",
      description: "Form for testing preview functionality",
      fields: [
        { type: "text", label: "Full Name", required: true },
        { type: "email", label: "Email", required: true },
        { type: "textarea", label: "Message", required: false },
      ],
    };

    cy.createForm(formData).then((form) => {
      cy.visit(`/forms/${form.id}/preview`);

      // Check form elements are present
      cy.get('[data-testid="form-preview"]').should("be.visible");
      cy.get('[data-testid="field-full-name"]').should("be.visible");
      cy.get('[data-testid="field-email"]').should("be.visible");
      cy.get('[data-testid="field-message"]').should("be.visible");

      // Test form validation
      cy.get('[data-testid="submit-preview-form"]').click();
      cy.get('[data-testid="validation-error"]').should("be.visible");

      // Fill form and submit
      cy.get('[data-testid="field-full-name"] input').type("John Doe");
      cy.get('[data-testid="field-email"] input').type("john@example.com");
      cy.get('[data-testid="field-message"] textarea').type(
        "This is a test message"
      );
      cy.get('[data-testid="submit-preview-form"]').click();

      cy.get('[data-testid="preview-success"]').should("be.visible");
    });
  });

  it("should delete form with confirmation", () => {
    const formData = {
      title: "Form to Delete",
      description: "This form will be deleted",
      fields: [{ type: "text", label: "Test Field", required: false }],
    };

    cy.createForm(formData).then((form) => {
      cy.visit("/forms");
      cy.get(
        `[data-testid="form-${form.id}"] [data-testid="delete-button"]`
      ).click();

      // Confirm deletion
      cy.get('[data-testid="confirm-delete-modal"]').should("be.visible");
      cy.get('[data-testid="confirm-delete-button"]').click();

      // Verify form is deleted
      cy.get('[data-testid="success-message"]').should(
        "contain",
        "Form deleted"
      );
      cy.get(`[data-testid="form-${form.id}"]`).should("not.exist");
    });
  });

  it("should validate form fields correctly", () => {
    cy.get('[data-testid="create-form-button"]').click();

    // Try to save without title
    cy.get('[data-testid="save-form-button"]').click();
    cy.get('[data-testid="validation-error"]').should(
      "contain",
      "Title is required"
    );

    // Fill title and try to save without fields
    cy.get('[data-testid="form-title-input"]').type("Test Form");
    cy.get('[data-testid="save-form-button"]').click();
    cy.get('[data-testid="validation-error"]').should(
      "contain",
      "At least one field is required"
    );

    // Add field and save successfully
    cy.get('[data-testid="add-field-button"]').click();
    cy.get('[data-testid="field-type-select"]').select("text");
    cy.get('[data-testid="field-label-input"]').type("Test Field");
    cy.get('[data-testid="save-field-button"]').click();
    cy.get('[data-testid="save-form-button"]').click();

    cy.get('[data-testid="success-message"]').should("be.visible");
  });
});
