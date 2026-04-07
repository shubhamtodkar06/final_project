// src/pages/Login.jsx
import { useState } from "react";
import API from "../api/axios";
import { useNavigate } from "react-router-dom";

function Login() {
  const [form, setForm] = useState({ username: "", password: "" });
  const navigate = useNavigate();

  const handleLogin = async () => {
    try {
      const res = await API.post("/api/auth/login/", form);

      localStorage.setItem("access", res.data.access);
      localStorage.setItem("refresh", res.data.refresh);

      navigate("/dashboard");
    } catch {
      alert("Invalid credentials");
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="neu-icon">
            <div className="icon-inner">🔐</div>
          </div>
          <h2>Login</h2>
          <p>Welcome back</p>
        </div>

        <div className="form-group">
          <div className="neu-input">
            <input
              placeholder="Username"
              onChange={(e) =>
                setForm({ ...form, username: e.target.value })
              }
            />
            <label>Username</label>
          </div>
        </div>

        <div className="form-group">
          <div className="neu-input">
            <input
              type="password"
              placeholder="Password"
              onChange={(e) =>
                setForm({ ...form, password: e.target.value })
              }
            />
            <label>Password</label>
          </div>
        </div>

        <button className="neu-button" onClick={handleLogin}>
          Login
        </button>

        <div className="signup-link">
          <p>
            Don't have an account?{" "}
            <span onClick={() => navigate("/register")}>
              Register
            </span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;