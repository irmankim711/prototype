// Google Forms Integration Test Script
// Open your browser console and run these commands to test your integration

console.log("🧪 Google Forms Integration Test Starting...");

// Test 1: Check if service is available
console.log("📋 Test 1: Service Availability");
try {
  console.log("✅ googleFormsService available:", typeof googleFormsService);
} catch (error) {
  console.error("❌ googleFormsService not available:", error);
}

// Test 2: Test authentication
console.log("\n🔐 Test 2: Authentication");
async function testAuth() {
  try {
    const authData = await googleFormsService.initiateAuth();
    console.log("✅ Auth URL generated:", authData.auth_url ? "Yes" : "No");
    console.log("📝 Auth message:", authData.message);
    return true;
  } catch (error) {
    console.error("❌ Authentication failed:", error);
    return false;
  }
}

// Test 3: Load user forms
console.log("\n📝 Test 3: Load User Forms");
async function testLoadForms() {
  try {
    const formsData = await googleFormsService.getUserForms();
    console.log("✅ Forms loaded successfully");
    console.log("📊 Total forms:", formsData.total);
    console.log("📋 Forms list:", formsData.forms);

    if (formsData.forms.length > 0) {
      const firstForm = formsData.forms[0];
      console.log("🎯 First form details:");
      console.log("  - ID:", firstForm.id);
      console.log("  - Title:", firstForm.title);
      console.log("  - Responses:", firstForm.responseCount);
      console.log(
        "  - Created:",
        new Date(firstForm.createdTime).toLocaleDateString()
      );

      return firstForm.id;
    } else {
      console.log("ℹ️ No forms found. Create some Google Forms first.");
      return null;
    }
  } catch (error) {
    console.error("❌ Failed to load forms:", error);
    return null;
  }
}

// Test 4: Load form responses
console.log("\n💬 Test 4: Form Responses");
async function testFormResponses(formId) {
  if (!formId) {
    console.log("⏭️ Skipping - no form ID available");
    return;
  }

  try {
    const responses = await googleFormsService.getFormResponses(formId);
    console.log("✅ Responses loaded successfully");
    console.log("📊 Total responses:", responses.total);
    console.log("📝 Sample responses:", responses.responses.slice(0, 3));
  } catch (error) {
    console.error("❌ Failed to load responses:", error);
  }
}

// Test 5: Load form analytics
console.log("\n📊 Test 5: Form Analytics");
async function testFormAnalytics(formId) {
  if (!formId) {
    console.log("⏭️ Skipping - no form ID available");
    return;
  }

  try {
    const analytics = await googleFormsService.getFormAnalytics(formId);
    console.log("✅ Analytics loaded successfully");
    console.log("📈 Analytics data:", analytics.analytics);
  } catch (error) {
    console.error("❌ Failed to load analytics:", error);
  }
}

// Test 6: Generate report
console.log("\n📄 Test 6: Report Generation");
async function testReportGeneration(formId) {
  if (!formId) {
    console.log("⏭️ Skipping - no form ID available");
    return;
  }

  try {
    const report = await googleFormsService.generateReport({
      google_form_id: formId,
      report_type: "summary",
      date_range: "last_30_days",
      form_source: "google_form",
    });
    console.log("✅ Report generated successfully");
    console.log("📄 Report details:", report);
  } catch (error) {
    console.error("❌ Failed to generate report:", error);
  }
}

// Run all tests
async function runAllTests() {
  console.log("\n🚀 Running all tests...\n");

  // Test authentication
  const authWorking = await testAuth();

  if (authWorking) {
    // Test loading forms
    const formId = await testLoadForms();

    // Test responses and analytics with first form
    if (formId) {
      await testFormResponses(formId);
      await testFormAnalytics(formId);
      await testReportGeneration(formId);
    }
  }

  console.log("\n✅ All tests completed!");
  console.log("\n💡 Next steps:");
  console.log(
    "1. If authentication worked, you can now use Google Forms in ReportBuilder"
  );
  console.log(
    '2. Go to ReportBuilder and select "Google Forms" as data source'
  );
  console.log("3. Authorize access and select a form to generate reports");
}

// Auto-run tests
runAllTests();

// Manual test functions (you can call these individually)
window.testGoogleFormsAuth = testAuth;
window.testGoogleFormsLoad = testLoadForms;
window.testGoogleFormsResponses = testFormResponses;
window.testGoogleFormsAnalytics = testFormAnalytics;
window.testGoogleFormsReport = testReportGeneration;

console.log("\n🔧 Manual test functions available:");
console.log("- testGoogleFormsAuth()");
console.log("- testGoogleFormsLoad()");
console.log("- testGoogleFormsResponses(formId)");
console.log("- testGoogleFormsAnalytics(formId)");
console.log("- testGoogleFormsReport(formId)");
