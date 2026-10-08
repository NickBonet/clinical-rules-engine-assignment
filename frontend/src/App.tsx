import { useState } from "react";

import type { PatientFilters } from "./api/types";
import { PatientTable } from "./components/PatientTable";
import { ReferenceDate } from "./components/ReferenceDate";
import { TaskTable } from "./components/TaskTable";
import { WorklistFilters } from "./components/WorklistFilters";
import type { View } from "./components/WorklistFilters";
import { useWorklistData } from "./hooks/useWorklistData";

export function App() {
  const [view, setView] = useState<View>("patients");
  const [filters, setFilters] = useState<PatientFilters>({
    role: "scheduler",
    specialty: "",
    taskType: "",
  });
  const { asOf, patients, specialties } = useWorklistData(filters);

  return (
    <main style={{ fontFamily: "system-ui, sans-serif", padding: "1.5rem", maxWidth: 960 }}>
      <h1>Clinical Rules Engine Assignment</h1>
      <ReferenceDate asOf={asOf} />
      <WorklistFilters
        view={view}
        filters={filters}
        specialties={specialties}
        onViewChange={setView}
        onFiltersChange={setFilters}
      />
      {view === "patients" ? (
        <PatientTable patients={patients} />
      ) : (
        <TaskTable tasks={patients.flatMap((patient) => patient.tasks)} />
      )}
    </main>
  );
}
