import { useEffect, useMemo, useState } from "react";

type Task = {
  patient_id: string;
  program: string;
  need_type: string;
  specialty: string | null;
  task_type: "scheduling" | "referral";
  reason: string;
};

type Enrollment = { program: string; risk_tier: string };

type Patient = {
  patient_id: string;
  enrollments: Enrollment[];
  tasks: Task[];
};

type Role = "scheduler" | "clinical";
type View = "patients" | "tasks";

export function App() {
  const [role, setRole] = useState<Role>("scheduler");
  const [view, setView] = useState<View>("patients");
  const [specialty, setSpecialty] = useState<string>("");
  const [taskType, setTaskType] = useState<string>("");
  const [patients, setPatients] = useState<Patient[]>([]);
  const [specialties, setSpecialties] = useState<string[]>([]);
  const [asOf, setAsOf] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((h) => setAsOf(h.as_of))
      .catch(() => setAsOf(null));
  }, []);

  // Specialty options for the role, from a dedicated endpoint — so selecting a
  // specialty doesn't narrow the list, and the options stay authoritative in the API.
  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    fetch(`/api/specialties?role=${role}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Failed to load specialties");
        return response.json();
      })
      .then((names: string[]) => {
        if (active) setSpecialties(names);
      })
      .catch(() => {
        if (active) setSpecialties([]);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [role]);

  // Displayed patients: filtered server-side by role, specialty, and task type.
  // The API returns only matching patients, each with just their matching tasks.
  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    const params = new URLSearchParams({ role });
    if (specialty) params.set("specialty", specialty);
    if (taskType) params.set("task_type", taskType);

    fetch(`/api/patients?${params}`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error("Failed to load patients");
        return response.json();
      })
      .then((rows: Patient[]) => {
        if (active) setPatients(rows);
      })
      .catch(() => {
        if (active) setPatients([]);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [role, specialty, taskType]);

  const taskRows = useMemo(() => patients.flatMap((p) => p.tasks), [patients]);

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
          View{" "}
          <select value={view} onChange={(e) => setView(e.target.value as View)}>
            <option value="patients">By patient</option>
            <option value="tasks">By task</option>
          </select>
        </label>

        <label>
          Role{" "}
          <select
            value={role}
            onChange={(e) => {
              setRole(e.target.value as Role);
              setPatients([]);
              setSpecialties([]);
              // Clear filters when switching roles; the effects refetch.
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
          <select
            value={specialty}
            onChange={(e) => {
              setSpecialty(e.target.value);
              setPatients([]);
            }}
          >
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
            onChange={(e) => {
              setTaskType(e.target.value);
              setPatients([]);
            }}
            disabled={role === "scheduler"}
          >
            <option value="">All</option>
            <option value="scheduling">Scheduling</option>
            <option value="referral">Referral</option>
          </select>
        </label>
      </div>

      {view === "patients" ? (
        <PatientTable patients={patients} />
      ) : (
        <TaskTable tasks={taskRows} />
      )}
    </main>
  );
}

function PatientTable({ patients }: { patients: Patient[] }) {
  return (
    <>
      <p>{patients.length} patient(s)</p>
      <table border={1} cellPadding={6} style={{ borderCollapse: "collapse", width: "100%" }}>
        <thead>
          <tr>
            <th>Patient</th>
            <th>Enrollments (risk tier)</th>
            <th>Tasks</th>
          </tr>
        </thead>
        <tbody>
          {patients.map((p) => (
            <tr key={p.patient_id}>
              <td style={{ verticalAlign: "top" }}>{p.patient_id}</td>
              <td style={{ verticalAlign: "top" }}>
                {p.enrollments.map((e, i) => (
                  <div key={i}>
                    {e.program} — <em>{e.risk_tier}</em>
                  </div>
                ))}
              </td>
              <td style={{ verticalAlign: "top" }}>
                {p.tasks.length === 0 ? (
                  <span style={{ color: "#6b7280" }}>No tasks</span>
                ) : (
                  p.tasks.map((t, i) => (
                    <div key={i}>
                      {t.specialty ?? "—"} — {t.task_type}
                      <span style={{ color: "#6b7280" }}> ({t.reason})</span>
                    </div>
                  ))
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function TaskTable({ tasks }: { tasks: Task[] }) {
  return (
    <>
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
    </>
  );
}
