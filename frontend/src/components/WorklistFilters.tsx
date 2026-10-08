import type { PatientFilters, Role, TaskType } from "../api/types";

export type View = "patients" | "tasks";

type WorklistFiltersProps = {
  view: View;
  filters: PatientFilters;
  specialties: string[];
  onViewChange: (view: View) => void;
  onFiltersChange: (filters: PatientFilters) => void;
};

export function WorklistFilters({
  view,
  filters,
  specialties,
  onViewChange,
  onFiltersChange,
}: WorklistFiltersProps) {
  const { role, specialty, taskType } = filters;

  return (
    <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem", flexWrap: "wrap" }}>
      <label>
        View{" "}
        <select value={view} onChange={(event) => onViewChange(event.target.value as View)}>
          <option value="patients">By patient</option>
          <option value="tasks">By task</option>
        </select>
      </label>

      <label>
        Role{" "}
        <select
          value={role}
          onChange={(event) => onFiltersChange({
            role: event.target.value as Role,
            specialty: "",
            taskType: "",
          })}
        >
          <option value="scheduler">Scheduler (scheduling only)</option>
          <option value="clinical">Clinical team (scheduling + referral)</option>
        </select>
      </label>

      <label>
        Specialty{" "}
        <select
          value={specialty}
          onChange={(event) => onFiltersChange({ ...filters, specialty: event.target.value })}
        >
          <option value="">All</option>
          {specialties.map((name) => (
            <option key={name} value={name}>{name}</option>
          ))}
        </select>
      </label>

      <label>
        Task type{" "}
        <select
          value={taskType}
          onChange={(event) => onFiltersChange({
            ...filters,
            taskType: event.target.value as TaskType | "",
          })}
          disabled={role === "scheduler"}
        >
          <option value="">All</option>
          <option value="scheduling">Scheduling</option>
          <option value="referral">Referral</option>
        </select>
      </label>
    </div>
  );
}