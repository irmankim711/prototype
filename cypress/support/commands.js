// cypress/support/commands.js

// Custom commands for authentication
Cypress.Commands.add(
  "login",
  (
    email = Cypress.env("test_email"),
    password = Cypress.env("test_password")
  ) => {
    cy.request({
      method: "POST",
      url: `${Cypress.env("backend_url")}/api/auth/login`,
      body: {
        email,
        password,
      },
    }).then((response) => {
      expect(response.status).to.eq(200);
      const token = response.body.access_token;
      window.localStorage.setItem("authToken", token);
      window.localStorage.setItem("user", JSON.stringify(response.body.user));
    });
  }
);

Cypress.Commands.add(
  "loginUI",
  (
    email = Cypress.env("test_email"),
    password = Cypress.env("test_password")
  ) => {
    cy.visit("/");
    cy.get('[data-testid="login-button"]').click();
    cy.get('[data-testid="email-input"]').type(email);
    cy.get('[data-testid="password-input"]').type(password);
    cy.get('[data-testid="submit-login"]').click();
    cy.url().should("include", "/dashboard");
  }
);

// Custom commands for form creation
Cypress.Commands.add("createForm", (formData) => {
  cy.request({
    method: "POST",
    url: `${Cypress.env("backend_url")}/api/forms`,
    headers: {
      Authorization: `Bearer ${window.localStorage.getItem("authToken")}`,
    },
    body: formData,
  }).then((response) => {
    expect(response.status).to.eq(201);
    return response.body;
  });
});

// Custom commands for mobile testing
Cypress.Commands.add("checkMobileView", () => {
  cy.viewport("iphone-x");
  cy.get('[data-testid="mobile-menu-toggle"]').should("be.visible");
  cy.get('[data-testid="desktop-sidebar"]').should("not.be.visible");
});

Cypress.Commands.add("checkTabletView", () => {
  cy.viewport("ipad-2");
  cy.get('[data-testid="responsive-layout"]').should("be.visible");
});

Cypress.Commands.add("checkDesktopView", () => {
  cy.viewport(1280, 720);
  cy.get('[data-testid="desktop-sidebar"]').should("be.visible");
});

// Custom commands for PWA testing
Cypress.Commands.add("checkPWAManifest", () => {
  cy.request("/manifest.json").then((response) => {
    expect(response.status).to.eq(200);
    expect(response.body).to.have.property("name");
    expect(response.body).to.have.property("short_name");
    expect(response.body).to.have.property("icons");
  });
});

Cypress.Commands.add("checkServiceWorker", () => {
  cy.window().then((win) => {
    expect(win.navigator.serviceWorker).to.exist;
  });
});

// Custom commands for accessibility testing
Cypress.Commands.add("checkA11y", () => {
  cy.injectAxe();
  cy.checkA11y(null, {
    rules: {
      "color-contrast": { enabled: true },
      "keyboard-navigation": { enabled: true },
      "focus-management": { enabled: true },
    },
  });
});

// Custom commands for report generation testing
Cypress.Commands.add("waitForReportGeneration", (reportId, timeout = 30000) => {
  cy.request({
    method: "GET",
    url: `${Cypress.env("backend_url")}/api/reports/${reportId}/status`,
    headers: {
      Authorization: `Bearer ${window.localStorage.getItem("authToken")}`,
    },
    timeout,
  }).then((response) => {
    if (response.body.status === "processing") {
      cy.wait(2000);
      cy.waitForReportGeneration(reportId, timeout);
    } else {
      expect(response.body.status).to.eq("completed");
    }
  });
});
