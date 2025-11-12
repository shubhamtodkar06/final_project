import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../style.css"; // Assuming style.css is in the parent folder, e.g., src/
// If style.css is in the same 'pages' folder, it should be './style.css'

const Login = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    password: "",
    remember: false,
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    const { name, type, value, checked } = e.target;
    setForm({ ...form, [name]: type === "checkbox" ? checked : value });
    setErrors({ ...errors, [name]: "" }); // clear field error while typing
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = {};

    if (!form.username.trim()) newErrors.username = "Username is required";
    if (!form.password.trim()) newErrors.password = "Password is required";

    setErrors(newErrors);

    if (Object.keys(newErrors).length > 0) return;

    try {
      const res = await fetch("http://localhost:8000/api/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: form.username, password: form.password }),
      });

      if (res.ok) {
        const data = await res.json();
        localStorage.setItem("access", data.access);
        localStorage.setItem("refresh", data.refresh);
        if (form.remember) localStorage.setItem("rememberUser", form.username);
        
        //alert(`Welcome back, ${form.username}!`);
        
        // --- THIS IS THE FIX ---
        navigate("/dashboard"); // Navigate to dashboard on success
        
      } else {
        // Handle failed login
        // We can get the specific error from your backend
        const errorData = await res.json();
        alert(`Login failed: ${errorData.error || "Invalid credentials"}`);
      }
    } catch (error) {
      // Handle network errors (e.g., backend is down)
      console.error("Login failed:", error);
      alert("Login service is currently unavailable. Please try again later.");
    }
  };

  const renderInput = (name, label, type, icon) => (
    <div className={`form-group ${errors[name] ? "error" : ""}`}>
      <div className="neu-input">
        <span className="input-icon">{icon}</span>
        <input
          type={type}
          name={name}
          placeholder=" "
          value={form[name]}
          onChange={handleChange}
          required
        />
        <label>{label}</label>
      </div>
      {errors[name] && <div className="error-message show">{errors[name]}</div>}
    </div>
  );

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
        background: "#e0e5ec",
        overflow: "hidden",
        position: "relative",
      }}
    >
      {/* Background Glow */}
      <div
        style={{
          position: "absolute",
          top: "-120px",
          left: "-120px",
          width: "360px",
          height: "360px",
          background:
            "radial-gradient(circle at top left, rgba(255,255,255,0.8), #e0e5ec)",
          filter: "blur(100px)",
        }}
      />
      <div
        style={{
          position: "absolute",
          bottom: "-150px",
          right: "-150px",
          width: "460px",
          height: "460px",
          background:
            "radial-gradient(circle at bottom right, #bec3cf, #e0e5ec)",
          filter: "blur(140px)",
        }}
      />

      {/* Main Neumorphic Card */}
      <div
        className="login-card"
        style={{
          position: "relative",
          zIndex: 1,
          width: "95%",
          maxWidth: "550px",
          background: "#e0e5ec",
          borderRadius: "50px",
          padding: "80px 60px",
          textAlign: "center",
          boxShadow: "25px 25px 70px #bec3cf, -25px -25px 70px #ffffff",
        }}
      >
        {/* User Icon */}
        <div
          style={{
            width: "120px",
            height: "120px",
            margin: "0 auto 30px",
            borderRadius: "50%",
            background: "#e0e5ec",
            boxShadow: "10px 10px 20px #bec3cf, -10px -10px 20px #ffffff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            stroke="#6c7293"
            strokeWidth="1.8"
            viewBox="0 0 24 24"
            width="65"
            height="65"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 12c2.485 0 4.5-2.015 4.5-4.5S14.485 3 12 3 7.5 5.015 7.5 7.5 9.515 12 12 12zm0 0c-4.142 0-7.5 2.239-7.5 5v1.5a.5.5 0 00.5.5h14a.5.5 0 00.5-.5V17c0-2.761-3.358-5-7.5-5z"
            />
          </svg>
        </div>

        <h1
          style={{
            fontSize: "2.5rem",
            fontWeight: "700",
            color: "#3d4468",
            marginBottom: "10px",
          }}
        >
          Welcome Back
        </h1>
        <p
          style={{
            color: "#80849b",
            fontSize: "16px",
            marginBottom: "45px",
            fontWeight: "500",
          }}
        >
          Login to continue your journey
        </p>

        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          {renderInput(
            "username",
            "Username",
            "text",
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              viewBox="0 0 24 24"
            >
              <circle cx="12" cy="8" r="4" />
              <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
            </svg>
          )}
          {renderInput(
            "password",
            "Password",
            "password",
            <svg
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              viewBox="0 0 24 24"
            >
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          )}

          {/* Remember Me + Forgot Password */}
          <div className="form-options">
            <label className="remember-wrapper">
              <input
                type="checkbox"
                name="remember"
                checked={form.remember}
                onChange={handleChange}
              />
              <span className="checkbox-label">
                <span className="neu-checkbox">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    viewBox="0 0 24 24"
                  >
                    <path d="M5 13l4 4L19 7" />
                  </svg>
                </span>
                Remember Me
              </span>
            </label>

            <span
              className="forgot-link"
              onClick={() => alert("Forgot Password clicked")}
            >
              Forgot Password?
            </span>
          </div>

          {/* Submit Button */}
          <button className="neu-button" type="submit">
            Login
          </button>

          {/* Signup Link */}
          <div className="signup-link">
            <p>
              Don’t have an account?{" "}
              <a
                href="#"
                onClick={(e) => {
                  e.preventDefault();
                  navigate("/register");
                }}
              >
                Sign Up
              </a>
            </p>
          </div>
        </form>
      </div>

      {/* Glow animation */}
      <div
        style={{
          position: "absolute",
          top: "50%",
          left: "50%",
          width: "700px",
          height: "700px",
          transform: "translate(-50%, -50%)",
          background:
            "radial-gradient(circle, rgba(255,255,25HA,0.25), transparent 75%)",
          filter: "blur(120px)",
          zIndex: "-1",
          animation: "pulseGlow 6s ease-in-out infinite alternate",
        }}
      ></div>
    </div>
  );
};

export default Login;