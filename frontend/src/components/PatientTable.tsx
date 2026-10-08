import type { Patient } from "../api/types";

export function PatientTable({ patients }: { patients: Patient[] }) {
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
          {patients.map((patient) => (
            <tr key={patient.patient_id}>
              <td style={{ verticalAlign: "top" }}>{patient.patient_id}</td>
              <td style={{ verticalAlign: "top" }}>
                {patient.enrollments.map((enrollment) => (
                  <div key={enrollment.program}>
                    {enrollment.program} - <em>{enrollment.risk_tier}</em>
                  </div>
                ))}
              </td>
              <td style={{ verticalAlign: "top" }}>
                {patient.tasks.length === 0 ? (
                  <span style={{ color: "#6b7280" }}>No tasks</span>
                ) : (
                  patient.tasks.map((task, index) => (
                    <div key={index}>
                      {task.specialty ?? "-"} - {task.task_type}
                      <span style={{ color: "#6b7280" }}> ({task.reason})</span>
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