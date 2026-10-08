import type { CursorPage, Health, Patient, PatientFilters, Role, Task } from "./types";

async function get<T>(path: string, signal: AbortSignal): Promise<T> {
  const response = await fetch(`/api${path}`, { signal });
  if (!response.ok) {
    throw new Error(`Request failed (${response.status}): ${path}`);
  }
  return response.json();
}

export function getHealth(signal: AbortSignal): Promise<Health> {
  return get<Health>("/health", signal);
}

export function getSpecialties(role: Role, signal: AbortSignal): Promise<string[]> {
  const params = new URLSearchParams({ role });
  return get<string[]>(`/specialties?${params}`, signal);
}

export function getPatients(
  { role, specialty, taskType }: PatientFilters,
  signal: AbortSignal,
  cursor?: string,
): Promise<CursorPage<Patient, string>> {
  const params = new URLSearchParams({ role });
  if (specialty) params.set("specialty", specialty);
  if (taskType) params.set("task_type", taskType);
  if (cursor) params.set("cursor", cursor);
  return get<CursorPage<Patient, string>>(`/patients?${params}`, signal);
}

export function getTasks(
  { role, specialty, taskType }: PatientFilters,
  signal: AbortSignal,
  cursor?: number,
): Promise<CursorPage<Task, number>> {
  const params = new URLSearchParams({ role });
  if (specialty) params.set("specialty", specialty);
  if (taskType) params.set("task_type", taskType);
  if (cursor !== undefined) params.set("cursor", String(cursor));
  return get<CursorPage<Task, number>>(`/tasks?${params}`, signal);
}