// cypress/e2e/01-authentication.cy.js
describe("Authentication Flow", () => {
  beforeEach(() => {
    cy.visit("/");
  });

  it("should display landing page correctly", () => {
    cy.get('[data-testid="landing-hero"]').should("be.visible");
    cy.get('[data-testid="login-button"]').should("be.visible");
    cy.get('[data-testid="get-started-button"]').should("be.visible");
    cy.title().should("include", "StratoSys Report");
  });

  it("should login successfully with valid credentials", () => {
    cy.loginUI();
    cy.url().should("include", "/dashboard");
    cy.get('[data-testid="user-menu"]').should("be.visible");
    cy.get('[data-testid="dashboard-welcome"]').should("contain", "Welcome");
  });

  it("should show error for invalid credentials", () => {
    cy.visit("/");
    cy.get('[data-testid="login-button"]').click();
    cy.get('[data-testid="email-input"]').type("invalid@example.com");
    cy.get('[data-testid="password-input"]').type("wrongpassword");
    cy.get('[data-testid="submit-login"]').click();
    cy.get('[data-testid="error-message"]').should("be.visible");
    cy.get('[data-testid="error-message"]').should(
      "contain",
      "Invalid credentials"
    );
  });

  it("should register new user successfully", () => {
    const randomEmail = `test${Date.now()}@example.com`;

    cy.visit("/");
    cy.get('[data-testid="login-button"]').click();
    cy.get('[data-testid="register-tab"]').click();

    cy.get('[data-testid="fullname-input"]').type("Test User");
    cy.get('[data-testid="email-input"]').type(randomEmail);
    cy.get('[data-testid="password-input"]').type("Password123!");
    cy.get('[data-testid="confirm-password-input"]').type("Password123!");
    cy.get('[data-testid="terms-checkbox"]').check();
    cy.get('[data-testid="submit-register"]').click();

    cy.url().should("include", "/dashboard");
    cy.get('[data-testid="user-menu"]').should("be.visible");
  });

  it("should logout successfully", () => {
    cy.loginUI();
    cy.get('[data-testid="user-menu"]').click();
    cy.get('[data-testid="logout-button"]').click();
    cy.url().should("eq", Cypress.config().baseUrl + "/");
    cy.get('[data-testid="login-button"]').should("be.visible");
  });
});
