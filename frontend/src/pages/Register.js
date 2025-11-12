import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../style.css";

const Register = () => {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    firstName: "",
    lastName: "",
    email: "", // 1. ADDED EMAIL TO STATE
    password: "",
    confirmPassword: "",
    mobile: "",
  });

  const [errors, setErrors] = useState({});

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setErrors({ ...errors, [e.target.name]: "" });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const newErrors = {};

    Object.keys(form).forEach((key) => {
      // We will let email be optional on the frontend for now
      // but you could add validation here if you want.
      if (key !== 'email' && !form[key].trim()) {
        newErrors[key] = "This field is required";
      }
    });

    if (form.password && form.confirmPassword && form.password !== form.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    setErrors(newErrors);
    if (Object.keys(newErrors).length > 0) return;

    try {
      const res = await fetch("http://localhost:8000/api/auth/register/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: form.username,
          password: form.password,
          password2: form.confirmPassword,
          first_name: form.firstName,
          last_name: form.lastName,
          mobile: form.mobile,
          email: form.email, // 3. ADDED EMAIL TO THE REQUEST
        }),
      });

      if (res.ok) {
        alert(`Welcome, ${form.firstName}! Your account has been created.`);
        navigate("/login"); // Redirect to login page
      } else {
        const errorData = await res.json();
        console.error("Registration error:", errorData);
        const errorMessages = Object.entries(errorData)
          .map(([field, messages]) => `${field}: ${messages.join(", ")}`)
          .join("\n");
        alert(`Registration failed:\n${errorMessages}`);
      }
    } catch (error) {
      console.error("Registration failed:", error);
      alert("Registration service is currently unavailable.");
    }
  };

  const renderInput = (name, label, type, icon) => (
    <div className={`form-group ${errors[name] ? "error" : ""}`}>
      <div className="neu-input uniform-box">
        <span className="input-icon">{icon}</span>
        <input
          type={type}
          name={name}
          placeholder=" "
          value={form[name]}
          onChange={handleChange}
          required={name !== 'email'} // Makes email optional
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
      {/* ... (all your style and glow divs) ... */}

      {/* Main Card */}
      <div
        className="login-card"
        style={{
          position: "relative",
          zIndex: 1,
          width: "95%",
          maxWidth: "580px",
          background: "#e0e5ec",
          borderRadius: "50px",
          padding: "80px 60px",
          textAlign: "center",
          boxShadow: "25px 25px 70px #bec3cf, -25px -25px 70px #ffffff",
        }}
      >
        {/* ... (icon and headers) ... */}
        
        <h1 style={{ fontSize: "2.6rem", fontWeight: "700", color: "#3d4468", marginBottom: "10px" }}>
          Welcome
        </h1>
        <p style={{ color: "#80849b", fontSize: "16px", marginBottom: "50px", fontWeight: "500" }}>
          Create your account to get started
        </p>

        <form onSubmit={handleSubmit}>
          {renderInput(
            "username",
            "Username",
            "text",
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
              <circle cx="12" cy="8" r="4" />
              <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
            </svg>
          )}

          {/* Equal Width for First/Last Name */}
          <div style={{ display: "flex", gap: "15px", flexWrap: "wrap" }}>
            <div style={{ flex: 1 }}>{renderInput(
              "firstName",
              "First Name",
              "text",
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
                <path d="M16 11a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z" />
                <path d="M12 14c-4 0-7 2-7 4v1h14v-1c0-2-3-4-7-4Z" />
              </svg>
            )}</div>
            <div style={{ flex: 1 }}>{renderInput(
              "lastName",
              "Last Name",
              "text",
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
                <path d="M16 11a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z" />
                <path d="M12 14c-4 0-7 2-7 4v1h14v-1c0-2-3-4-7-4Z" />
              </svg>
            )}</div>
          </div>

          {/* 2. ADDED EMAIL RENDER CALL */}
          {renderInput(
            "email",
            "Email (Optional)",
            "email",
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
              <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
              <polyline points="22,6 12,13 2,6" />
            </svg>
          )}

          {renderInput(
            "mobile",
            "Mobile Number",
            "tel",
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
              <path d="M7 2h10a2 2 0 0 1 2 2v16a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z" />
              <path d="M12 18h.01" />
            </svg>
          )}
          {renderInput(
            "password",
            "Password",
            "password",
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          )}
          {renderInput(
            "confirmPassword",
            "Confirm Password",
            "password",
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          )}

          <button className="neu-button" type="submit">
            Create Account
          </button>

          <p style={{ marginTop: "20px", color: "#6c7293", fontSize: "14px" }}>
            Already have an account?{" "}
            <span
              onClick={() => navigate("/login")}
              style={{ color: "#3d4468", fontWeight: "600", cursor: "pointer" }}
            >
              Login
            </span>
          </p>
        </form>
      </div>
    </div>
  );
};

export default Register;