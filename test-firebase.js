// Test Firebase configuration directly

const firebaseConfig = {
  apiKey: "AIzaSyCGpr8w2sPsngexBYBg6ktNE64IWENtD2Q",
  authDomain: "report-automation-57f6e.firebaseapp.com",
  projectId: "report-automation-57f6e",
  storageBucket: "report-automation-57f6e.firebasestorage.app",
  messagingSenderId: "87279819935",
  appId: "1:87279819935:web:9f78b1c4c2efe16ad4d6aa",
  measurementId: "G-R2HGN102D3"
};

async function testFirebaseAPI() {
  try {
    console.log("🔧 Testing Firebase API connectivity...");

    // Test the Firebase Auth REST API
    const url = `https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=${firebaseConfig.apiKey}`;

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: 'test@example.com',
        password: 'testpass123',
        returnSecureToken: true
      })
    });

    if (response.ok) {
      console.log("✅ Firebase API is accessible");
      const data = await response.json();
      console.log("Response:", data.error ? data.error.message : "API working");
    } else {
      console.error("❌ Firebase API error:", response.status, response.statusText);
      const errorText = await response.text();
      console.error("Error details:", errorText);
    }
  } catch (error) {
    console.error("❌ Network error:", error.message);
  }
}

testFirebaseAPI();