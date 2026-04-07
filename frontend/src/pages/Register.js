// src/pages/Register.jsx
import { useState } from "react";
import API from "../api/axios";
import { useNavigate } from "react-router-dom";

function Register() {
  const [form, setForm] = useState({});
  const navigate = useNavigate();

  const handleRegister = async () => {
    try {
      await API.post("/api/auth/register/", form);
      navigate("/");
    } catch {
      alert("Registration failed");
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <div className="neu-icon">
            <div className="icon-inner">📝</div>
          </div>
          <h2>Register</h2>
          <p>Create your account</p>
        </div>

        {["username", "email", "password"].map((field) => (
          <div className="form-group" key={field}>
            <div className="neu-input">
              <input
                type={field === "password" ? "password" : "text"}
                placeholder={field}
                onChange={(e) =>
                  setForm({ ...form, [field]: e.target.value })
                }
              />
              <label>{field}</label>
            </div>
          </div>
        ))}

        <button className="neu-button" onClick={handleRegister}>
          Register
        </button>

        <div className="signup-link">
          <p>
            Already have an account?{" "}
            <span onClick={() => navigate("/")}>Login</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Register;