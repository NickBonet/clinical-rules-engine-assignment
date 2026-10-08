import type { Health, Patient, PatientFilters, Role } from "./types";

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
): Promise<Patient[]> {
  const params = new URLSearchParams({ role });
  if (specialty) params.set("specialty", specialty);
  if (taskType) params.set("task_type", taskType);
  return get<Patient[]>(`/patients?${params}`, signal);
}