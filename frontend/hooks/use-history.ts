"use client";

import { useCallback, useEffect, useState } from "react";

import { getWorkflowHistory, getWorkflowHistoryRun } from "@/services/api";
import type { HistoryFilters, WorkflowHistoryListResponse, WorkflowRunDetail, WorkflowRunSummary } from "@/types/history";

interface UseHistoryOptions {
  limit?: number;
  initialRunId?: string | null;
}

interface UseHistoryResult {
  filters: HistoryFilters;
  items: WorkflowRunSummary[];
  total: number;
  selectedRun: WorkflowRunDetail | null;
  loading: boolean;
  detailLoading: boolean;
  error: string | null;
  setWorkflowType: (value: HistoryFilters["workflowType"]) => void;
  setStatus: (value: HistoryFilters["status"]) => void;
  selectRun: (runId: string) => Promise<void>;
  refresh: () => Promise<void>;
}

const defaultFilters: HistoryFilters = { workflowType: "all", status: "all" };

export function useHistory(options: UseHistoryOptions = {}): UseHistoryResult {
  const [filters, setFilters] = useState<HistoryFilters>(defaultFilters);
  const [data, setData] = useState<WorkflowHistoryListResponse | null>(null);
  const [selectedRun, setSelectedRun] = useState<WorkflowRunDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const limit = options.limit ?? 50;
  const initialRunId = options.initialRunId ?? null;

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getWorkflowHistory({
        workflowType: filters.workflowType === "all" ? undefined : filters.workflowType,
        status: filters.status === "all" ? undefined : filters.status,
        limit,
        offset: 0,
      });
      setData(response);
      if (selectedRun && !response.items.some((item) => item.id === selectedRun.id)) {
        setSelectedRun(null);
      }
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load workflow history.");
    } finally {
      setLoading(false);
    }
  }, [filters.status, filters.workflowType, limit, selectedRun]);

  const selectRun = useCallback(async (runId: string) => {
    setDetailLoading(true);
    setError(null);
    try {
      setSelectedRun(await getWorkflowHistoryRun(runId));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load workflow details.");
    } finally {
      setDetailLoading(false);
    }
  }, []);

  function setWorkflowType(value: HistoryFilters["workflowType"]) {
    setFilters((current) => ({ ...current, workflowType: value }));
  }

  function setStatus(value: HistoryFilters["status"]) {
    setFilters((current) => ({ ...current, status: value }));
  }

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!initialRunId || selectedRun?.id === initialRunId) {
      return;
    }
    void selectRun(initialRunId);
  }, [initialRunId, selectRun, selectedRun?.id]);

  useEffect(() => {
    function handleHistoryUpdated() {
      void load();
    }

    window.addEventListener("ai-studio:history-updated", handleHistoryUpdated);
    return () => window.removeEventListener("ai-studio:history-updated", handleHistoryUpdated);
  }, [load]);

  return {
    filters,
    items: data?.items ?? [],
    total: data?.total ?? 0,
    selectedRun,
    loading,
    detailLoading,
    error,
    setWorkflowType,
    setStatus,
    selectRun,
    refresh: load,
  };
}
