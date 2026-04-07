// src/pages/Notes.jsx
import { useState } from "react";
import API from "../api/axios";

function Notes() {
  const [notes, setNotes] = useState("");

  const generateNotes = async () => {
    const res = await API.post("/api/student_notes/generate/", {
      filters: { subjects: ["Math"], topics: ["Fractions"] },
      include_suggestions: true,
    });

    setNotes(res.data.content);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>AI Notes</h2>

        <button className="neu-button" onClick={generateNotes}>
          Generate Notes
        </button>

        <pre>{notes}</pre>
      </div>
    </div>
  );
}

export default Notes;