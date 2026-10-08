import { useEffect, useState } from "react";

import { getHealth, getPatients, getSpecialties } from "../api/client";
import type { Patient, PatientFilters, Role } from "../api/types";

export function useWorklistData({ role, specialty, taskType }: PatientFilters) {
  const [asOf, setAsOf] = useState<string | null>(null);
  const [specialtyResult, setSpecialtyResult] = useState<{
    role: Role;
    names: string[];
  } | null>(null);
  const [patientResult, setPatientResult] = useState<{
    key: string;
    rows: Patient[];
  } | null>(null);
  const patientKey = JSON.stringify([role, specialty, taskType]);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    getHealth(controller.signal)
      .then((health) => {
        if (active) setAsOf(health.as_of);
      })
      .catch(() => {
        if (active) setAsOf(null);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    getSpecialties(role, controller.signal)
      .then((names) => {
        if (active) setSpecialtyResult({ role, names });
      })
      .catch(() => {
        if (active) setSpecialtyResult({ role, names: [] });
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [role]);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    getPatients({ role, specialty, taskType }, controller.signal)
      .then((rows) => {
        if (active) setPatientResult({ key: patientKey, rows });
      })
      .catch(() => {
        if (active) setPatientResult({ key: patientKey, rows: [] });
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [role, specialty, taskType, patientKey]);

  return {
    asOf,
    specialties: specialtyResult?.role === role ? specialtyResult.names : [],
    patients: patientResult?.key === patientKey ? patientResult.rows : [],
  };
}