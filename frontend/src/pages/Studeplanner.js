// src/pages/Planner.jsx
import { useState } from "react";
import API from "../api/axios";

function Planner() {
  const [plan, setPlan] = useState(null);

  const generatePlan = async () => {
    const res = await API.post("/api/recommendations/study-plan/", {
      filters: { subjects: ["Math"] },
      include_suggestions: true,
    });

    setPlan(res.data.planner);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Study Planner</h2>

        <button className="neu-button" onClick={generatePlan}>
          Generate Plan
        </button>

        {plan &&
          Object.entries(plan.daily_plan).map(([day, task]) => (
            <p key={day}>
              <strong>{day}:</strong> {task}
            </p>
          ))}
      </div>
    </div>
  );
}

export default Planner;