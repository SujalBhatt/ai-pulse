import React, { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Dashboard({ org }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api(`/dashboard?org_id=${org.org_id}`)
      .then(setData)
      .catch((err) => setError(err.message));
  }, [org]);

  if (error) return <p className="error">{error}</p>;
  if (!data) return <p>Loading dashboard...</p>;
  return (
    <div className="card">
      <h2>{data.organization} dashboard</h2>
      <p>Department results are hidden until at least five employees complete the diagnostic.</p>
      <table>
        <thead>
          <tr><th>Department</th><th>Completed</th><th>Average</th><th>Level</th></tr>
        </thead>
        <tbody>
          {data.departments.map((department) => (
            <tr key={department.department}>
              <td>{department.department}</td>
              <td>{department.responded}</td>
              <td>{department.redacted ? "Hidden" : department.average_score}</td>
              <td>{department.level}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <h3>Top risks</h3>
      {data.top_risks.length === 0 ? (
        <p>No risks from reportable teams.</p>
      ) : (
        <ul>{data.top_risks.map(([risk, count]) => <li key={risk}>{risk} ({count})</li>)}</ul>
      )}
    </div>
  );
}
