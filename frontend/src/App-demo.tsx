import React, { useState } from "react";
import { LoginForm } from "./components/LoginForm";
import { Dashboard } from "./components/Dashboard";

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [token, setToken] = useState<string | null>(
    localStorage.getItem("token")
  );

  const handleLoginSuccess = (accessToken: string) => {
    setToken(accessToken);
    setIsLoggedIn(true);
    localStorage.setItem("token", accessToken);
  };

  const handleLogout = () => {
    setToken(null);
    setIsLoggedIn(false);
    localStorage.removeItem("token");
  };

  // Check if user is already logged in
  React.useEffect(() => {
    if (token) {
      setIsLoggedIn(true);
    }
  }, [token]);

  return (
    <div className="App">
      <header
        style={{
          padding: "20px",
          backgroundColor: "#f8f9fa",
          borderBottom: "1px solid #e9ecef",
        }}
      >
        <h1>StratoSys MVP - Frontend Connected to Backend</h1>
        {isLoggedIn && (
          <button
            onClick={handleLogout}
            style={{
              padding: "8px 16px",
              backgroundColor: "#dc3545",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              float: "right",
            }}
          >
            Logout
          </button>
        )}
      </header>

      <main>
        {!isLoggedIn ? (
          <LoginForm onLoginSuccess={handleLoginSuccess} />
        ) : (
          <Dashboard />
        )}
      </main>

      <footer
        style={{
          marginTop: "50px",
          padding: "20px",
          backgroundColor: "#f8f9fa",
          borderTop: "1px solid #e9ecef",
          textAlign: "center",
          color: "#6c757d",
        }}
      >
        <p>StratoSys MVP - All API endpoints are connected and functional!</p>
        <p>Backend running on: http://127.0.0.1:5000</p>
      </footer>
    </div>
  );
}

export default App;
