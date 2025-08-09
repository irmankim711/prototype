// cypress/e2e/03-report-generation.cy.js
describe("Report Generation Workflow", () => {
  let testFormId;

  beforeEach(() => {
    cy.login();

    // Create test form with sample data
    const formData = {
      title: "Report Test Form",
      description: "Form for testing report generation",
      fields: [
        { type: "text", label: "Name", required: true },
        { type: "email", label: "Email", required: true },
        { type: "rating", label: "Satisfaction", required: true, scale: 5 },
        { type: "textarea", label: "Feedback", required: false },
      ],
    };

    cy.createForm(formData).then((form) => {
      testFormId = form.id;

      // Add some test submissions
      for (let i = 1; i <= 5; i++) {
        cy.request({
          method: "POST",
          url: `${Cypress.env("backend_url")}/api/forms/${testFormId}/submit`,
          body: {
            name: `Test User ${i}`,
            email: `user${i}@example.com`,
            satisfaction: Math.floor(Math.random() * 5) + 1,
            feedback: `This is test feedback from user ${i}`,
          },
        });
      }
    });

    cy.visit("/dashboard");
  });

  it("should generate basic report successfully", () => {
    cy.visit("/reports/create");

    // Select form
    cy.get('[data-testid="form-select"]').select(testFormId);

    // Configure report settings
    cy.get('[data-testid="report-title-input"]').type("Test Report");
    cy.get('[data-testid="report-type-select"]').select("summary");
    cy.get('[data-testid="include-charts-checkbox"]').check();
    cy.get('[data-testid="include-analytics-checkbox"]').check();

    // Generate report
    cy.get('[data-testid="generate-report-button"]').click();

    // Wait for generation to complete
    cy.get('[data-testid="generation-progress"]').should("be.visible");
    cy.get('[data-testid="generation-complete"]', { timeout: 30000 }).should(
      "be.visible"
    );

    // Verify report content
    cy.get('[data-testid="report-preview"]').should("be.visible");
    cy.get('[data-testid="report-title"]').should("contain", "Test Report");
    cy.get('[data-testid="submissions-chart"]').should("be.visible");
    cy.get('[data-testid="satisfaction-analytics"]').should("be.visible");
  });

  it("should download report in multiple formats", () => {
    cy.visit("/reports");

    // Assume we have a report from previous test
    cy.get(
      '[data-testid="reports-list"] [data-testid="report-item"]:first'
    ).within(() => {
      // Download as PDF
      cy.get('[data-testid="download-pdf-button"]').click();
      cy.readFile("cypress/downloads/Test Report.pdf", {
        timeout: 10000,
      }).should("exist");

      // Download as Word
      cy.get('[data-testid="download-word-button"]').click();
      cy.readFile("cypress/downloads/Test Report.docx", {
        timeout: 10000,
      }).should("exist");

      // Download as Excel
      cy.get('[data-testid="download-excel-button"]').click();
      cy.readFile("cypress/downloads/Test Report.xlsx", {
        timeout: 10000,
      }).should("exist");
    });
  });

  it("should customize report template", () => {
    cy.visit("/reports/create");

    // Select form and basic settings
    cy.get('[data-testid="form-select"]').select(testFormId);
    cy.get('[data-testid="report-title-input"]').type("Custom Template Report");

    // Go to template customization
    cy.get('[data-testid="customize-template-button"]').click();

    // Customize logo
    cy.get('[data-testid="logo-upload"]').selectFile(
      "cypress/fixtures/test-logo.png"
    );
    cy.get('[data-testid="logo-preview"]').should("be.visible");

    // Customize colors
    cy.get('[data-testid="primary-color-picker"]').clear().type("#007bff");
    cy.get('[data-testid="secondary-color-picker"]').clear().type("#6c757d");

    // Customize sections
    cy.get('[data-testid="include-executive-summary"]').check();
    cy.get('[data-testid="include-detailed-analysis"]').check();
    cy.get('[data-testid="include-recommendations"]').check();

    // Save template customization
    cy.get('[data-testid="save-template-button"]').click();
    cy.get('[data-testid="template-saved-message"]').should("be.visible");

    // Generate report with custom template
    cy.get('[data-testid="generate-report-button"]').click();
    cy.get('[data-testid="generation-complete"]', { timeout: 30000 }).should(
      "be.visible"
    );

    // Verify customizations are applied
    cy.get('[data-testid="report-preview"]').within(() => {
      cy.get('[data-testid="custom-logo"]').should("be.visible");
      cy.get('[data-testid="executive-summary-section"]').should("be.visible");
      cy.get('[data-testid="detailed-analysis-section"]').should("be.visible");
      cy.get('[data-testid="recommendations-section"]').should("be.visible");
    });
  });

  it("should handle report generation errors gracefully", () => {
    cy.visit("/reports/create");

    // Try to generate report without selecting form
    cy.get('[data-testid="generate-report-button"]').click();
    cy.get('[data-testid="validation-error"]').should(
      "contain",
      "Please select a form"
    );

    // Select form but with no submissions
    cy.createForm({
      title: "Empty Form",
      fields: [{ type: "text", label: "Test", required: true }],
    }).then((emptyForm) => {
      cy.get('[data-testid="form-select"]').select(emptyForm.id);
      cy.get('[data-testid="generate-report-button"]').click();

      cy.get('[data-testid="no-data-warning"]').should("be.visible");
      cy.get('[data-testid="no-data-warning"]').should(
        "contain",
        "No submissions found"
      );
    });
  });

  it("should schedule automated reports", () => {
    cy.visit("/reports/schedule");

    // Create new scheduled report
    cy.get('[data-testid="create-schedule-button"]').click();

    // Configure schedule
    cy.get('[data-testid="schedule-name-input"]').type(
      "Weekly Feedback Report"
    );
    cy.get('[data-testid="form-select"]').select(testFormId);
    cy.get('[data-testid="frequency-select"]').select("weekly");
    cy.get('[data-testid="day-of-week-select"]').select("monday");
    cy.get('[data-testid="time-input"]').type("09:00");

    // Configure recipients
    cy.get('[data-testid="add-recipient-button"]').click();
    cy.get('[data-testid="recipient-email-input"]').type("manager@example.com");
    cy.get('[data-testid="save-recipient-button"]').click();

    // Save schedule
    cy.get('[data-testid="save-schedule-button"]').click();
    cy.get('[data-testid="schedule-success-message"]').should("be.visible");

    // Verify schedule appears in list
    cy.get('[data-testid="schedules-list"]').should(
      "contain",
      "Weekly Feedback Report"
    );
    cy.get('[data-testid="schedules-list"]').should("contain", "Active");
  });

  it("should edit and preview reports", () => {
    cy.visit("/reports");

    // Click edit on first report
    cy.get(
      '[data-testid="reports-list"] [data-testid="report-item"]:first'
    ).within(() => {
      cy.get('[data-testid="edit-button"]').click();
    });

    // Edit report title
    cy.get('[data-testid="report-title-input"]')
      .clear()
      .type("Edited Report Title");

    // Edit report content
    cy.get('[data-testid="report-editor"]').should("be.visible");
    cy.get('[data-testid="add-section-button"]').click();
    cy.get('[data-testid="section-type-select"]').select("text");
    cy.get('[data-testid="section-content-input"]').type(
      "This is additional content added during editing."
    );
    cy.get('[data-testid="save-section-button"]').click();

    // Save changes
    cy.get('[data-testid="save-report-button"]').click();
    cy.get('[data-testid="save-success-message"]').should("be.visible");

    // Preview edited report
    cy.get('[data-testid="preview-report-button"]').click();
    cy.get('[data-testid="report-preview-modal"]').should("be.visible");
    cy.get('[data-testid="report-preview"]').should(
      "contain",
      "Edited Report Title"
    );
    cy.get('[data-testid="report-preview"]').should(
      "contain",
      "This is additional content added during editing."
    );
  });
});
