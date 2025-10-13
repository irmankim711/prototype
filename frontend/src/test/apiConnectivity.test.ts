import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';

async function testApiConnectivity() {
  console.log('--- API Connectivity Test ---');

  // 1. Ping /api/forms/ without auth
  try {
    await axios.get(`${API_BASE_URL}/api/forms/`);
    console.log('❌ /api/forms/ should not be accessible without auth');
  } catch (err: any) {
    if (err.response && err.response.status === 401) {
      console.log('✅ /api/forms/ correctly requires authentication (401)');
    } else {
      console.log('❌ Unexpected error for /api/forms/ without auth:', err.message);
    }
  }

  // 2. Register user (ignore if already exists)
  const testEmail = `apitest_${Date.now()}@example.com`;
  const testPassword = 'apitest123';
  try {
    await axios.post(`${API_BASE_URL}/api/auth/register`, { // ✅ FIXED: Keep /api prefix since this uses direct axios, not the configured instance
      email: testEmail,
      password: testPassword,
    });
    console.log('✅ User registered:', testEmail);
  } catch (err: any) {
    if (err.response && err.response.status === 409) {
      console.log('ℹ️  User already exists, will try login');
    } else {
      console.log('❌ Registration error:', err.message);
      return;
    }
  }

  // 3. Login
  let token = '';
  try {
    const res = await axios.post(`${API_BASE_URL}/api/auth/login`, { // ✅ FIXED: Keep /api prefix since this uses direct axios, not the configured instance
      email: testEmail,
      password: testPassword,
    });
    token = res.data.access_token;
    if (token) {
      console.log('✅ Login successful, got JWT');
    } else {
      console.log('❌ Login did not return a token');
      return;
    }
  } catch (err: any) {
    console.log('❌ Login error:', err.message);
    return;
  }

  // 4. Authenticated request to /api/forms/
  try {
    const res = await axios.get(`${API_BASE_URL}/api/forms/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (Array.isArray(res.data.forms) || res.data.forms) {
      console.log('✅ Authenticated /api/forms/ request succeeded');
    } else {
      console.log('❌ /api/forms/ did not return expected data');
    }
  } catch (err: any) {
    console.log('❌ Authenticated /api/forms/ error:', err.message);
  }
}

// Run the test if this file is executed directly
if (typeof require !== 'undefined' && require.main === module) {
  testApiConnectivity();
} 