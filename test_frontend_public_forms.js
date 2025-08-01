#!/usr/bin/env node

/**
 * Test script to verify frontend public forms API call
 * This simulates the exact call made by PublicForms.tsx
 */

const axios = require("axios");

async function testPublicFormsAPI() {
  try {
    console.log("🧪 Testing Frontend Public Forms API Call...\n");

    // Simulate the exact call made by formBuilderAPI.getPublicForms()
    console.log("📡 Making request to: /forms/public with baseURL: /api");
    console.log("📡 Full URL will be: /api/forms/public");

    const publicResponse = await axios.get("/forms/public", {
      baseURL: "http://localhost:5000/api", // Using absolute URL for testing
      timeout: 10000,
    });

    console.log("✅ Request successful!");
    console.log("📊 Status:", publicResponse.status);
    console.log(
      "📦 Response data:",
      JSON.stringify(publicResponse.data, null, 2)
    );

    // Test the response parsing logic
    const responseData = publicResponse.data;
    if (
      responseData &&
      responseData.success &&
      Array.isArray(responseData.forms)
    ) {
      console.log(
        `✅ Response format is correct! Found ${responseData.forms.length} public forms.`
      );
      return responseData.forms;
    } else {
      console.log(
        "⚠️  Response format unexpected, will fallback to empty array"
      );
      return [];
    }
  } catch (error) {
    console.error("❌ Error testing public forms API:", error.message);
    if (error.response) {
      console.error("📊 Status:", error.response.status);
      console.error("📦 Response:", error.response.data);
    }
    throw error;
  }
}

// Run the test
if (require.main === module) {
  testPublicFormsAPI()
    .then((forms) => {
      console.log("\n🎉 Test completed successfully!");
      console.log(`📋 Public forms available: ${forms.length}`);
    })
    .catch((error) => {
      console.error("\n💥 Test failed:", error.message);
      process.exit(1);
    });
}

module.exports = { testPublicFormsAPI };
