import React, { useState } from "react";
import "./Register.css";

export default function Register() {

  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    password2: "",
    first_name: "",
    last_name: "",
    mobile_no: "",
    parents_no: "",
    country: "",
    state: "",
    city: "",
    age: "",
  });

  const [studentOTP, setStudentOTP] = useState("");
  const [enteredStudentOTP, setEnteredStudentOTP] = useState("");

  const [parentOTP, setParentOTP] = useState("");
  const [enteredParentOTP, setEnteredParentOTP] = useState("");

  const [popupMessage, setPopupMessage] = useState(""); // ✅ Popup Text
  const [showPopup, setShowPopup] = useState(false); // ✅ Popup Visibility

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const generateOTP = () => Math.floor(100000 + Math.random() * 900000).toString();

  const sendStudentOTP = () => {
    const otp = generateOTP();
    setStudentOTP(otp);
    alert("Student OTP: " + otp);
  };

  const sendParentOTP = () => {
    const otp = generateOTP();
    setParentOTP(otp);
    alert("Parent OTP: " + otp);
  };

  const verifyOTP = (entered, actual, who) => {
    if (entered === actual) {
      setPopupMessage(`${who} OTP Verified Successfully ✅`);
      setShowPopup(true);
    } else {
      setPopupMessage(`${who} OTP Incorrect ❌`);
      setShowPopup(true);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (enteredStudentOTP !== studentOTP) return alert("Verify Student OTP First");
    if (enteredParentOTP !== parentOTP) return alert("Verify Parent OTP First");

    const backendData = {
      username: form.username,
      email: form.email,
      password: form.password,
      password2: form.password2,
      first_name: form.first_name,
      last_name: form.last_name,
    };

    let res = await fetch("http://127.0.0.1:8000/accounts/register/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(backendData),
    });

    if (!res.ok) return alert("Registration Failed");

    localStorage.setItem("profile_extra", JSON.stringify({
      mobile_no: form.mobile_no,
      parents_no: form.parents_no,
      country: form.country,
      state: form.state,
      city: form.city,
      age: form.age,
    }));

    let loginRes = await fetch("http://127.0.0.1:8000/accounts/login/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username: form.username, password: form.password }),
    });

    let loginData = await loginRes.json();

    if (loginData.access) {
      localStorage.setItem("access_token", loginData.access);
      localStorage.setItem("refresh_token", loginData.refresh);
      alert("Registered & Logged In Successfully");
      window.location.href = "/";
    }
  };

  return (
    <div className="reg-container">
      <h1 className="reg-title">Register</h1>

      <form className="reg-form" onSubmit={handleSubmit}>

        <input name="username" placeholder="Username" onChange={handleChange} required />
        <input name="first_name" placeholder="First Name" onChange={handleChange} required />
        <input name="last_name" placeholder="Last Name" onChange={handleChange} required />

        <input name="mobile_no" placeholder="Student Mobile" onChange={handleChange} required />
        <button type="button" className="reg-btn" onClick={sendStudentOTP}>Send Student OTP</button>
        <input placeholder="Enter Student OTP" value={enteredStudentOTP} onChange={(e)=>setEnteredStudentOTP(e.target.value)} required />
        <button type="button" className="verify-btn" onClick={() => verifyOTP(enteredStudentOTP, studentOTP, "Student")}>Verify OTP</button>

        <input name="parents_no" placeholder="Parent Mobile" onChange={handleChange} required />
        <button type="button" className="reg-btn" onClick={sendParentOTP}>Send Parent OTP</button>
        <input placeholder="Enter Parent OTP" value={enteredParentOTP} onChange={(e)=>setEnteredParentOTP(e.target.value)} required />
        <button type="button" className="verify-btn" onClick={() => verifyOTP(enteredParentOTP, parentOTP, "Parent")}>Verify OTP</button>

        <input type="email" name="email" placeholder="Email" onChange={handleChange} required />
        <input name="country" placeholder="Country" onChange={handleChange} required />
        <input name="state" placeholder="State" onChange={handleChange} required />
        <input name="city" placeholder="City" onChange={handleChange} required />
        <input name="age" maxLength="2" placeholder="Age (2 digits)" onChange={handleChange} required />

        <input type="password" name="password" placeholder="Password" onChange={handleChange} required />
        <input type="password" name="password2" placeholder="Confirm Password" onChange={handleChange} required />

        <button className="reg-btn" type="submit">Register</button>

      </form>

      {/* ✅ Popup Box */}
      {showPopup && (
        <div className="popup">
          <div className="popup-box">
            <p>{popupMessage}</p>
            <button onClick={() => setShowPopup(false)} className="reg-btn">OK</button>
          </div>
        </div>
      )}
    </div>
  );
}
