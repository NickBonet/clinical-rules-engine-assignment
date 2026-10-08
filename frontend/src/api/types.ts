export type TaskType = "scheduling" | "referral";
export type Role = "scheduler" | "clinical";

export type Task = {
  patient_id: string;
  program: string;
  need_type: string;
  specialty: string | null;
  task_type: TaskType;
  reason: string;
};

export type Enrollment = { program: string; risk_tier: string };

export type Patient = {
  patient_id: string;
  enrollments: Enrollment[];
  tasks: Task[];
};

export type Health = { status: "ok"; as_of: string };

export type PatientFilters = {
  role: Role;
  specialty: string;
  taskType: TaskType | "";
};