import { useEffect, useRef, useState } from "react";

import { getHealth, getPatients, getSpecialties, getTasks } from "../api/client";
import type { Patient, PatientFilters, Role, Task } from "../api/types";
import type { View } from "../components/WorklistFilters";

type WorklistResult = {
  key: string;
  patients: Patient[];
  tasks: Task[];
  nextCursor: string | number | null;
};

export function useWorklistData(
  { role, specialty, taskType }: PatientFilters,
  view: View,
) {
  const [asOf, setAsOf] = useState<string | null>(null);
  const [specialtyResult, setSpecialtyResult] = useState<{
    role: Role;
    names: string[];
  } | null>(null);
  const [worklistResult, setWorklistResult] = useState<WorklistResult | null>(null);
  const [loadingMore, setLoadingMore] = useState(false);
  const moreController = useRef<AbortController | null>(null);
  const worklistKey = JSON.stringify([view, role, specialty, taskType]);

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

    moreController.current?.abort();
    moreController.current = null;
    setLoadingMore(false);

    const loadFirstPage = async () => {
      if (view === "patients") {
        const page = await getPatients({ role, specialty, taskType }, controller.signal);
        return { patients: page.items, tasks: [], nextCursor: page.next_cursor };
      }
      const page = await getTasks({ role, specialty, taskType }, controller.signal);
      return { patients: [], tasks: page.items, nextCursor: page.next_cursor };
    };

    loadFirstPage()
      .then((page) => {
        if (active) setWorklistResult({ key: worklistKey, ...page });
      })
      .catch(() => {
        if (active) {
          setWorklistResult({
            key: worklistKey,
            patients: [],
            tasks: [],
            nextCursor: null,
          });
        }
      });

    return () => {
      active = false;
      controller.abort();
      moreController.current?.abort();
    };
  }, [view, role, specialty, taskType, worklistKey]);

  const currentResult = worklistResult?.key === worklistKey ? worklistResult : null;

  function loadMore() {
    if (!currentResult || currentResult.nextCursor === null || loadingMore) return;

    const controller = new AbortController();
    moreController.current?.abort();
    moreController.current = controller;
    setLoadingMore(true);

    const nextPage = view === "patients"
      ? getPatients(
        { role, specialty, taskType },
        controller.signal,
        String(currentResult.nextCursor),
      ).then((page) => ({ patients: page.items, tasks: [], nextCursor: page.next_cursor }))
      : getTasks(
        { role, specialty, taskType },
        controller.signal,
        Number(currentResult.nextCursor),
      ).then((page) => ({ patients: [], tasks: page.items, nextCursor: page.next_cursor }));

    nextPage
      .then((page) => {
        setWorklistResult((current) => {
          if (current?.key !== worklistKey) return current;
          return {
            ...current,
            patients: [...current.patients, ...page.patients],
            tasks: [...current.tasks, ...page.tasks],
            nextCursor: page.nextCursor,
          };
        });
      })
      .catch(() => undefined)
      .finally(() => {
        if (moreController.current === controller) {
          moreController.current = null;
          setLoadingMore(false);
        }
      });
  }

  return {
    asOf,
    specialties: specialtyResult?.role === role ? specialtyResult.names : [],
    patients: currentResult?.patients ?? [],
    tasks: currentResult?.tasks ?? [],
    hasMore: currentResult?.nextCursor !== null && currentResult !== null,
    loadingMore,
    loadMore,
  };
}