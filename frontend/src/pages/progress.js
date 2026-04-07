// src/pages/Progress.jsx
import { useEffect, useState } from "react";
import API from "../api/axios";

function Progress() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchProgress();
  }, []);

  const fetchProgress = async () => {
    const res = await API.get("/api/progress/overview/");
    setData(res.data);
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h2>Progress</h2>

        {data && (
          <pre>{JSON.stringify(data, null, 2)}</pre>
        )}
      </div>
    </div>
  );
}

export default Progress;