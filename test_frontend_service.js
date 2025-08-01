// Test the updated formBuilder service
import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:5000";

// Test the getPublicForms method logic
async function testGetPublicForms() {
  try {
    console.log("Testing getPublicForms method...");

    const publicResponse = await axios.get("/api/forms/public", {
      baseURL: API_BASE_URL,
      timeout: 10000,
    });

    console.log("Raw response:", publicResponse.data);

    // Extract forms array from API response
    const responseData = publicResponse.data;
    if (
      responseData &&
      responseData.success &&
      Array.isArray(responseData.forms)
    ) {
      console.log(
        "✅ SUCCESS: Extracted forms array with",
        responseData.forms.length,
        "forms"
      );
      return responseData.forms;
    }

    // Fallback: return empty array if response structure is unexpected
    console.log("❌ Unexpected response structure, returning empty array");
    return [];
  } catch (error) {
    console.error("❌ Error in getPublicForms:", error);
    return [];
  }
}

// Run the test
testGetPublicForms().then((forms) => {
  console.log("Final result:", forms);
  console.log("Number of forms:", forms.length);
  if (forms.length > 0) {
    console.log("Sample form:", forms[0]);
  }
});
