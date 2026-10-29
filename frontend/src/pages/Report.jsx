import React, { useEffect, useState } from "react";
import { api } from "../api.js";

export default function Report() {
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [deleted, setDeleted] = useState(false);

  useEffect(() => {
    api("/reports/me").then(setReport).catch((err) => setError(err.message));
  }, []);

  async function deleteData() {
    if (!window.confirm("Delete all answers and your report for this organization?")) return;
    setError("");
    try {
      await api("/reports/me", { method: "DELETE" });
      setDeleted(true);
      setReport(null);
    } catch (err) {
      setError(err.message);
    }
  }

  if (error) return <p className="error">{error}</p>;
  if (deleted) {
    return (
      <div className="card">
        <h2>Your data was deleted</h2>
        <p>Your answers and report for this organization have been removed.</p>
      </div>
    );
  }
  if (!report) return <p>Loading…</p>;
  return (
    <div className="card">
      <h2>{report.name}: {report.level}</h2>
      <p>Average score: {report.average_score ?? "Not assessed"}</p>
      <h3>Risks</h3>
      <ul>{report.risks.map((r) => <li key={r}>{r}</li>)}</ul>
      <h3>Next steps</h3>
      <ul>{report.next_steps.map((s) => <li key={s}>{s}</li>)}</ul>
      <h3>Personal action plan</h3>
      {report.action_plan.length === 0 ? (
        <p>No targeted actions yet.</p>
      ) : (
        <ul>
          {report.action_plan.map((item) => (
            <li key={item.priority}><b>{item.priority}:</b> {item.action}<br /><small>{item.reason}</small></li>
          ))}
        </ul>
      )}
      <button className="danger" onClick={deleteData}>Delete my answers and report</button>
    </div>
  );
}
