import { useEffect, useMemo, useState } from "react";

type Task = {
  patient_id: string;
  program: string;
  need_type: string;
  specialty: string | null;
  task_type: "scheduling" | "referral";
  reason: string;
};

type Role = "scheduler" | "clinical";

export function App() {
  const [role, setRole] = useState<Role>("scheduler");
  const [specialty, setSpecialty] = useState<string>("");
  const [taskType, setTaskType] = useState<string>("");
  const [allTasks, setAllTasks] = useState<Task[]>([]);
  const [asOf, setAsOf] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((h) => setAsOf(h.as_of))
      .catch(() => setAsOf(null));
  }, []);

  // Fetch tasks for the selected role; filter specialty and type locally.
  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    fetch(`/api/tasks?role=${role}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Failed to load tasks");
        return response.json();
      })
      .then((tasks: Task[]) => {
        if (active) setAllTasks(tasks);
      })
      .catch(() => {
        if (active) setAllTasks([]);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [role]);

  const specialties = useMemo(
    () => [...new Set(allTasks.map((t) => t.specialty).filter(Boolean))].sort() as string[],
    [allTasks],
  );

  const tasks = useMemo(
    () =>
      allTasks.filter(
        (t) =>
          (!specialty || t.specialty === specialty) &&
          (!taskType || t.task_type === taskType),
      ),
    [allTasks, specialty, taskType],
  );

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "1.5rem", maxWidth: 960 }}>
      <h1>Clinical Rules Worklist</h1>

      <div
        style={{
          background: "#eef4ff",
          border: "1px solid #c3d4f5",
          borderRadius: 6,
          padding: "0.6rem 0.9rem",
          marginBottom: "1rem",
          fontSize: "0.9rem",
        }}
      >
        <strong>Reference date (as-of):</strong>{" "}
        {asOf ? <code>{asOf}</code> : "loading…"}
        <div style={{ color: "#44506b", marginTop: "0.25rem" }}>
          All eligibility, risk tiers, A1C windows, and visit-cadence tasks are
          evaluated relative to this date. Reference date defaults to the latest
          lab result date in the dataset.
        </div>
      </div>

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", flexWrap: "wrap" }}>
        <label>
          Role{" "}
          <select
            value={role}
            onChange={(e) => {
              setRole(e.target.value as Role);
              setAllTasks([]);
              // Clear filters when switching roles.
              setSpecialty("");
              setTaskType("");
            }}
          >
            <option value="scheduler">Scheduler (scheduling only)</option>
            <option value="clinical">Clinical team (scheduling + referral)</option>
          </select>
        </label>

        <label>
          Specialty{" "}
          <select value={specialty} onChange={(e) => setSpecialty(e.target.value)}>
            <option value="">All</option>
            {specialties.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </label>

        <label>
          Task type{" "}
          <select
            value={taskType}
            onChange={(e) => setTaskType(e.target.value)}
            disabled={role === "scheduler"}
          >
            <option value="">All</option>
            <option value="scheduling">Scheduling</option>
            <option value="referral">Referral</option>
          </select>
        </label>
      </div>

      <p>{tasks.length} task(s)</p>
      <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th>Patient</th>
            <th>Program</th>
            <th>Specialty</th>
            <th>Task</th>
            <th>Reason</th>
          </tr>
        </thead>
        <tbody>
          {tasks.map((t, i) => (
            <tr key={i}>
              <td>{t.patient_id}</td>
              <td>{t.program}</td>
              <td>{t.specialty}</td>
              <td>{t.task_type}</td>
              <td>{t.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
