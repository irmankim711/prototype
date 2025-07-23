import React, { useState } from "react";
import { login, testDatabaseConnection } from "../services/api";

interface LoginFormProps {
  onLoginSuccess?: (token: string) => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState("test@example.com");
  const [password, setPassword] = useState("testpass123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [dbStatus, setDbStatus] = useState<string>("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await login({ email, password });
      console.log("Login successful:", response);
      onLoginSuccess?.(response.access_token);
    } catch (err) {
      console.error("Login failed:", err);
      setError("Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const testConnection = async () => {
    try {
      const result = await testDatabaseConnection();
      setDbStatus(`✅ Connected! ${result.table_count} tables found`);
    } catch (err) {
      setDbStatus("❌ Connection failed");
    }
  };

  return (
    <div
      style={{
        maxWidth: "400px",
        margin: "50px auto",
        padding: "20px",
        border: "1px solid #ddd",
        borderRadius: "8px",
      }}
    >
      <h2>Login to StratoSys MVP</h2>

      <div style={{ marginBottom: "20px" }}>
        <button
          onClick={testConnection}
          style={{ padding: "8px 16px", marginBottom: "10px" }}
        >
          Test Backend Connection
        </button>
        {dbStatus && (
          <div
            style={{
              fontSize: "14px",
              color: dbStatus.includes("✅") ? "green" : "red",
            }}
          >
            {dbStatus}
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "15px" }}>
          <label htmlFor="email">Email:</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={{ width: "100%", padding: "8px", marginTop: "5px" }}
            autoComplete="email"
          />
        </div>

        <div style={{ marginBottom: "15px" }}>
          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            style={{ width: "100%", padding: "8px", marginTop: "5px" }}
            autoComplete="current-password"
          />
        </div>

        {error && (
          <div style={{ color: "red", marginBottom: "15px", fontSize: "14px" }}>
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          style={{
            width: "100%",
            padding: "10px",
            backgroundColor: loading ? "#ccc" : "#007bff",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>

      <div style={{ marginTop: "20px", fontSize: "12px", color: "#666" }}>
        <p>Test credentials:</p>
        <p>Email: test@example.com</p>
        <p>Password: testpass123</p>
      </div>
    </div>
  );
};
