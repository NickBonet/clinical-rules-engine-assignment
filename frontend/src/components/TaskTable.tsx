import type { Task } from "../api/types";

export function TaskTable({ tasks }: { tasks: Task[] }) {
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
          {tasks.map((task, index) => (
            <tr key={index}>
              <td>{task.patient_id}</td>
              <td>{task.program}</td>
              <td>{task.specialty}</td>
              <td>{task.task_type}</td>
              <td>{task.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}