// Simple test to verify frontend-backend connection
// Run this in the browser console or as a Node.js script

const API_BASE = 'http://localhost:5000/api';

async function testBackendConnection() {
    console.log('🧪 Testing Frontend-Backend Connection...');
    
    try {
        // Test health check
        const healthResponse = await fetch('http://localhost:5000/health');
        if (healthResponse.ok) {
            console.log('✅ Backend is running');
        } else {
            console.log('❌ Backend health check failed');
            return;
        }
        
        // Test public forms endpoint
        const formsResponse = await fetch(`${API_BASE}/forms/public`);
        if (formsResponse.ok) {
            const formsData = await formsResponse.json();
            console.log('✅ Public forms endpoint working:', formsData);
        } else {
            console.log('❌ Public forms endpoint failed:', formsResponse.status);
        }
        
        // Test authentication
        const loginResponse = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                email: 'test@example.com',
                password: 'testpassword123'
            })
        });
        
        if (loginResponse.ok) {
            const loginData = await loginResponse.json();
            console.log('✅ Authentication working:', loginData);
            
            // Test protected endpoints with token
            const token = loginData.access_token;
            const headers = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            };
            
            // Test forms endpoint
            const protectedFormsResponse = await fetch(`${API_BASE}/forms`, { headers });
            if (protectedFormsResponse.ok) {
                const protectedFormsData = await protectedFormsResponse.json();
                console.log('✅ Protected forms endpoint working:', protectedFormsData);
            } else {
                console.log('❌ Protected forms endpoint failed:', protectedFormsResponse.status);
            }
            
            // Test automated reports endpoint
            const reportsResponse = await fetch(`${API_BASE}/reports/automated`, { headers });
            if (reportsResponse.ok) {
                const reportsData = await reportsResponse.json();
                console.log('✅ Automated reports endpoint working:', reportsData);
            } else {
                console.log('❌ Automated reports endpoint failed:', reportsResponse.status);
            }
            
        } else {
            console.log('❌ Authentication failed:', loginResponse.status);
        }
        
    } catch (error) {
        console.error('❌ Connection test failed:', error);
    }
}

// Export for Node.js or run directly in browser
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { testBackendConnection };
} else {
    // Browser environment
    window.testBackendConnection = testBackendConnection;
    console.log('🧪 Run testBackendConnection() to test the connection');
} 