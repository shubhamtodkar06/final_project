// src/pages/Homework.jsx
import { useState } from "react";
import API from "../api/axios";

function Homework() {
  const [file, setFile] = useState(null);

  const submitHomework = async () => {
    const formData = new FormData();
    formData.append("subject", "Mathematics");
    formData.append("file", file);

    const res = await API.post("/api/homework/submit/", formData);

    alert("Score: " + res.data.score);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Upload Homework</h2>

        <input type="file" onChange={(e) => setFile(e.target.files[0])} />

        <button className="neu-button" onClick={submitHomework}>
          Submit
        </button>
      </div>
    </div>
  );
}

export default Homework;