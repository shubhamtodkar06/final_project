// src/pages/Reports.jsx
import { useEffect, useState } from "react";
import API from "../api/axios";

function Reports() {
  const [report, setReport] = useState("");

  useEffect(() => {
    fetchReport();
  }, []);

  const fetchReport = async () => {
    const res = await API.get("/api/reports/weekly/");
    setReport(res.data.summary);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Weekly Report</h2>
        <p>{report}</p>
      </div>
    </div>
  );
}

export default Reports;