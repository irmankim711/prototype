// cypress/e2e/05-accessibility.cy.js
import "cypress-axe";

describe("Accessibility Testing", () => {
  beforeEach(() => {
    cy.login();
    cy.injectAxe();
  });

  it("should meet accessibility standards on landing page", () => {
    cy.visit("/");
    cy.checkA11y();

    // Check keyboard navigation
    cy.get("body").tab();
    cy.focused().should("have.attr", "data-testid", "skip-link");

    cy.tab();
    cy.focused().should("have.attr", "data-testid", "login-button");

    cy.tab();
    cy.focused().should("have.attr", "data-testid", "get-started-button");
  });

  it("should meet accessibility standards on dashboard", () => {
    cy.visit("/dashboard");
    cy.checkA11y();

    // Check heading hierarchy
    cy.get("h1").should("exist");
    cy.get("h1").should("contain", "Dashboard");

    // Check ARIA labels
    cy.get('[data-testid="user-menu"]').should("have.attr", "aria-label");
    cy.get('[data-testid="notifications-button"]').should(
      "have.attr",
      "aria-label"
    );

    // Check color contrast
    cy.get('[data-testid="primary-button"]').should("have.css", "color");
    cy.get('[data-testid="primary-button"]').should(
      "have.css",
      "background-color"
    );
  });

  it("should meet accessibility standards on form creation", () => {
    cy.visit("/forms/create");
    cy.checkA11y();

    // Check form labels
    cy.get('[data-testid="form-title-input"]').should(
      "have.attr",
      "aria-label"
    );
    cy.get('[data-testid="form-description-input"]').should(
      "have.attr",
      "aria-label"
    );

    // Check required field indicators
    cy.get('[data-testid="required-indicator"]').should(
      "have.attr",
      "aria-label",
      "Required field"
    );

    // Check keyboard navigation in form builder
    cy.get('[data-testid="add-field-button"]').focus().should("have.focus");
    cy.get('[data-testid="add-field-button"]').type(" "); // Space to activate
    cy.get('[data-testid="field-type-modal"]').should("be.visible");

    cy.get("body").type("{esc}");
    cy.get('[data-testid="field-type-modal"]').should("not.be.visible");
  });

  it("should support screen reader navigation", () => {
    cy.visit("/dashboard");

    // Check skip links
    cy.get('[data-testid="skip-to-main"]').should("exist");
    cy.get('[data-testid="skip-to-navigation"]').should("exist");

    // Check main landmarks
    cy.get("main").should("have.attr", "role", "main");
    cy.get("nav").should("have.attr", "role", "navigation");

    // Check aria-live regions for dynamic content
    cy.get('[data-testid="status-messages"]').should(
      "have.attr",
      "aria-live",
      "polite"
    );
    cy.get('[data-testid="error-messages"]').should(
      "have.attr",
      "aria-live",
      "assertive"
    );
  });

  it("should handle focus management correctly", () => {
    cy.visit("/forms");

    // Test modal focus trap
    cy.get('[data-testid="create-form-button"]').click();
    cy.get('[data-testid="create-form-modal"]').should("be.visible");

    // Focus should be trapped in modal
    cy.get('[data-testid="modal-close-button"]').focus();
    cy.tab();
    cy.focused().should("be.inside", '[data-testid="create-form-modal"]');

    // Test focus return after modal close
    cy.get('[data-testid="modal-close-button"]').click();
    cy.focused().should("have.attr", "data-testid", "create-form-button");
  });

  it("should provide proper error announcements", () => {
    cy.visit("/forms/create");

    // Submit form without required fields
    cy.get('[data-testid="save-form-button"]').click();

    // Check error message accessibility
    cy.get('[data-testid="error-message"]').should(
      "have.attr",
      "role",
      "alert"
    );
    cy.get('[data-testid="error-message"]').should(
      "have.attr",
      "aria-live",
      "assertive"
    );

    // Check field-specific errors
    cy.get('[data-testid="form-title-error"]').should("have.attr", "id");
    cy.get('[data-testid="form-title-input"]').should(
      "have.attr",
      "aria-describedby"
    );
  });

  it("should support keyboard-only navigation", () => {
    cy.visit("/reports");

    // Navigate through report list using keyboard
    cy.get(
      '[data-testid="reports-list"] [data-testid="report-item"]:first'
    ).focus();
    cy.focused().type("{enter}");
    cy.url().should("include", "/reports/");

    // Test custom components keyboard support
    cy.visit("/forms/create");
    cy.get('[data-testid="field-type-dropdown"]').focus();
    cy.focused().type("{space}"); // Open dropdown
    cy.get('[data-testid="dropdown-options"]').should("be.visible");

    cy.focused().type("{arrowdown}"); // Navigate options
    cy.focused().type("{enter}"); // Select option
    cy.get('[data-testid="dropdown-options"]').should("not.be.visible");
  });

  it("should provide alternative text for images and icons", () => {
    cy.visit("/dashboard");

    // Check all images have alt text
    cy.get("img").each(($img) => {
      cy.wrap($img).should("have.attr", "alt");
    });

    // Check icons have proper labels
    cy.get('[data-testid="icon-button"]').each(($button) => {
      cy.wrap($button).should("satisfy", ($el) => {
        return (
          $el.attr("aria-label") ||
          $el.attr("title") ||
          $el.text().trim().length > 0
        );
      });
    });
  });

  it("should support high contrast mode", () => {
    cy.visit("/dashboard");

    // Simulate high contrast mode
    cy.get("body").then(($body) => {
      $body.addClass("high-contrast-mode");
    });

    // Check that elements are still visible and usable
    cy.get('[data-testid="primary-button"]').should("be.visible");
    cy.get('[data-testid="form-card"]').should("have.css", "border-width");
    cy.get('[data-testid="text-input"]').should("have.css", "border-color");
  });

  it("should support reduced motion preferences", () => {
    cy.visit("/");

    // Simulate reduced motion preference
    cy.window().then((win) => {
      cy.stub(win, "matchMedia").returns({
        matches: true,
        addListener: () => {},
        removeListener: () => {},
      });
    });

    cy.reload();

    // Check that animations are disabled or reduced
    cy.get('[data-testid="animated-element"]').should(
      "have.css",
      "animation-duration",
      "0s"
    );
    cy.get('[data-testid="transition-element"]').should(
      "have.css",
      "transition-duration",
      "0s"
    );
  });
});
