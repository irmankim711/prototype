// cypress/e2e/04-mobile-pwa.cy.js
describe("Mobile PWA Functionality", () => {
  beforeEach(() => {
    cy.login();
  });

  it("should be responsive on mobile devices", () => {
    cy.visit("/dashboard");

    // Test iPhone X
    cy.checkMobileView();
    cy.get('[data-testid="mobile-navigation"]').should("be.visible");
    cy.get('[data-testid="mobile-menu-toggle"]').click();
    cy.get('[data-testid="mobile-menu"]').should("be.visible");

    // Test navigation works on mobile
    cy.get('[data-testid="mobile-nav-forms"]').click();
    cy.url().should("include", "/forms");
    cy.get('[data-testid="forms-grid"]').should("be.visible");

    // Test tablet view
    cy.checkTabletView();
    cy.get('[data-testid="tablet-layout"]').should("be.visible");

    // Test desktop view
    cy.checkDesktopView();
    cy.get('[data-testid="desktop-sidebar"]').should("be.visible");
  });

  it("should have valid PWA manifest", () => {
    cy.checkPWAManifest();

    cy.request("/manifest.json").then((response) => {
      expect(response.body.name).to.equal("StratoSys Report Generator");
      expect(response.body.short_name).to.equal("StratoSys");
      expect(response.body.start_url).to.equal("/");
      expect(response.body.display).to.equal("standalone");
      expect(response.body.theme_color).to.exist;
      expect(response.body.background_color).to.exist;
      expect(response.body.icons).to.be.an("array");
      expect(response.body.icons.length).to.be.greaterThan(0);
    });
  });

  it("should register service worker for offline functionality", () => {
    cy.visit("/");
    cy.checkServiceWorker();

    cy.window().then((win) => {
      win.navigator.serviceWorker.getRegistrations().then((registrations) => {
        expect(registrations.length).to.be.greaterThan(0);
      });
    });
  });

  it("should work offline for cached pages", () => {
    cy.visit("/dashboard");
    cy.wait(2000); // Wait for caching

    // Simulate offline mode
    cy.window().then((win) => {
      cy.stub(win.navigator, "onLine").value(false);
    });

    // Visit cached page
    cy.visit("/dashboard");
    cy.get('[data-testid="dashboard-content"]').should("be.visible");
    cy.get('[data-testid="offline-indicator"]').should("be.visible");
  });

  it("should support touch gestures on mobile", () => {
    cy.checkMobileView();
    cy.visit("/forms");

    // Test swipe gesture for form cards
    cy.get('[data-testid="form-card"]:first')
      .trigger("touchstart", { touches: [{ clientX: 100, clientY: 100 }] })
      .trigger("touchmove", { touches: [{ clientX: 200, clientY: 100 }] })
      .trigger("touchend");

    cy.get('[data-testid="form-actions"]').should("be.visible");

    // Test pull-to-refresh
    cy.get("body")
      .trigger("touchstart", { touches: [{ clientX: 100, clientY: 50 }] })
      .trigger("touchmove", { touches: [{ clientX: 100, clientY: 200 }] })
      .trigger("touchend");

    cy.get('[data-testid="refresh-indicator"]').should("be.visible");
  });

  it("should have proper mobile form interactions", () => {
    cy.checkMobileView();
    cy.visit("/forms/create");

    // Test mobile form builder
    cy.get('[data-testid="mobile-form-builder"]').should("be.visible");
    cy.get('[data-testid="form-title-input"]').type("Mobile Test Form");

    // Test field addition on mobile
    cy.get('[data-testid="add-field-fab"]').click();
    cy.get('[data-testid="field-type-bottom-sheet"]').should("be.visible");
    cy.get('[data-testid="field-type-text"]').click();

    // Test field configuration
    cy.get('[data-testid="field-config-modal"]').should("be.visible");
    cy.get('[data-testid="field-label-input"]').type("Mobile Field");
    cy.get('[data-testid="save-field-mobile"]').click();

    // Save form
    cy.get('[data-testid="save-form-mobile"]').click();
    cy.get('[data-testid="success-toast"]').should("be.visible");
  });

  it("should support mobile report viewing", () => {
    cy.checkMobileView();
    cy.visit("/reports");

    // Test mobile report list
    cy.get('[data-testid="mobile-reports-list"]').should("be.visible");
    cy.get('[data-testid="report-card"]:first').click();

    // Test mobile report viewer
    cy.get('[data-testid="mobile-report-viewer"]').should("be.visible");
    cy.get('[data-testid="report-content"]').should("be.visible");

    // Test zoom functionality
    cy.get('[data-testid="zoom-in-button"]').click();
    cy.get('[data-testid="report-content"]').should("have.css", "transform");

    // Test sharing on mobile
    cy.get('[data-testid="mobile-share-button"]').click();
    cy.get('[data-testid="share-options"]').should("be.visible");
    cy.get('[data-testid="share-email"]').should("be.visible");
    cy.get('[data-testid="share-download"]').should("be.visible");
  });

  it("should handle mobile navigation properly", () => {
    cy.checkMobileView();
    cy.visit("/dashboard");

    // Test hamburger menu
    cy.get('[data-testid="mobile-menu-toggle"]').click();
    cy.get('[data-testid="mobile-sidebar"]').should("be.visible");

    // Test navigation items
    cy.get('[data-testid="nav-dashboard"]').should("be.visible");
    cy.get('[data-testid="nav-forms"]').should("be.visible");
    cy.get('[data-testid="nav-reports"]').should("be.visible");
    cy.get('[data-testid="nav-analytics"]').should("be.visible");

    // Test navigation
    cy.get('[data-testid="nav-forms"]').click();
    cy.url().should("include", "/forms");
    cy.get('[data-testid="mobile-sidebar"]').should("not.be.visible");

    // Test back navigation
    cy.get('[data-testid="mobile-back-button"]').click();
    cy.url().should("include", "/dashboard");
  });

  it("should optimize performance on mobile", () => {
    cy.checkMobileView();
    cy.visit("/dashboard");

    // Check that heavy components are lazy loaded
    cy.get('[data-testid="dashboard-skeleton"]').should("be.visible");
    cy.get('[data-testid="dashboard-content"]', { timeout: 10000 }).should(
      "be.visible"
    );
    cy.get('[data-testid="dashboard-skeleton"]').should("not.exist");

    // Check that images are optimized
    cy.get('[data-testid="dashboard-chart"] img').should(($img) => {
      expect($img[0].naturalWidth).to.be.lessThan(800);
    });
  });

  it("should support mobile accessibility features", () => {
    cy.checkMobileView();
    cy.visit("/dashboard");

    // Check touch targets are large enough (44px minimum)
    cy.get('[data-testid="mobile-menu-toggle"]').should(
      "have.css",
      "min-height",
      "44px"
    );
    cy.get('[data-testid="create-form-fab"]').should(
      "have.css",
      "min-height",
      "56px"
    );

    // Check focus management
    cy.get('[data-testid="mobile-menu-toggle"]').focus();
    cy.get('[data-testid="mobile-menu-toggle"]').should("have.focus");

    // Check screen reader labels
    cy.get('[data-testid="mobile-menu-toggle"]').should(
      "have.attr",
      "aria-label"
    );
    cy.get('[data-testid="create-form-fab"]').should("have.attr", "aria-label");
  });
});
