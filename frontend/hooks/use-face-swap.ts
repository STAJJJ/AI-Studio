"use client";

import { useEffect, useRef, useState } from "react";

import { createFaceSwapTask, getTask, uploadFile } from "@/services/api";
import type { FaceSwapTaskResponse, FileUploadResponse } from "@/types/face-swap";

export type FaceSwapPhase = "idle" | "uploading" | "generating" | "completed" | "failed";

interface StartFaceSwapInput {
  sourceFile: File;
  targetFile: File;
}

interface UseFaceSwapResult {
  phase: FaceSwapPhase;
  isBusy: boolean;
  sourceUpload: FileUploadResponse | null;
  targetUpload: FileUploadResponse | null;
  task: FaceSwapTaskResponse | null;
  error: string | null;
  start: (input: StartFaceSwapInput) => Promise<void>;
  reset: () => void;
}

const POLL_INTERVAL_MS = 2000;

export function useFaceSwap(): UseFaceSwapResult {
  const [phase, setPhase] = useState<FaceSwapPhase>("idle");
  const [sourceUpload, setSourceUpload] = useState<FileUploadResponse | null>(null);
  const [targetUpload, setTargetUpload] = useState<FileUploadResponse | null>(null);
  const [task, setTask] = useState<FaceSwapTaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestTokenRef = useRef(0);
  const busyRef = useRef(false);

  function clearPollTimer() {
    if (pollTimeoutRef.current !== null) {
      clearTimeout(pollTimeoutRef.current);
      pollTimeoutRef.current = null;
    }
  }

  function finish() {
    busyRef.current = false;
    clearPollTimer();
  }

  function reset() {
    requestTokenRef.current += 1;
    finish();
    setPhase("idle");
    setSourceUpload(null);
    setTargetUpload(null);
    setTask(null);
    setError(null);
  }

  function schedulePoll(taskId: string, requestToken: number) {
    clearPollTimer();
    pollTimeoutRef.current = setTimeout(() => {
      void pollTask(taskId, requestToken);
    }, POLL_INTERVAL_MS);
  }

  async function pollTask(taskId: string, requestToken: number) {
    if (requestTokenRef.current !== requestToken) {
      return;
    }

    try {
      const nextTask = await getTask(taskId);
      if (requestTokenRef.current !== requestToken) {
        return;
      }
      setTask(nextTask);

      if (nextTask.status === "succeeded") {
        finish();
        setPhase("completed");
        setError(null);
        window.dispatchEvent(new Event("ai-studio:history-updated"));
        return;
      }

      if (nextTask.status === "failed") {
        finish();
        setPhase("failed");
        setError(nextTask.error?.message ?? "Face swap task failed.");
        return;
      }

      schedulePoll(taskId, requestToken);
    } catch (caught) {
      if (requestTokenRef.current !== requestToken) {
        return;
      }
      finish();
      setPhase("failed");
      setError(caught instanceof Error ? caught.message : "Face swap status polling failed.");
    }
  }

  async function start({ sourceFile, targetFile }: StartFaceSwapInput) {
    if (busyRef.current) {
      return;
    }

    busyRef.current = true;
    requestTokenRef.current += 1;
    const requestToken = requestTokenRef.current;

    clearPollTimer();
    setPhase("uploading");
    setSourceUpload(null);
    setTargetUpload(null);
    setTask(null);
    setError(null);

    try {
      const source = await uploadFile(sourceFile, "source_face");
      if (requestTokenRef.current !== requestToken) {
        return;
      }
      setSourceUpload(source);

      const target = await uploadFile(targetFile, "target_image");
      if (requestTokenRef.current !== requestToken) {
        return;
      }
      setTargetUpload(target);

      const createdTask = await createFaceSwapTask(source.id, target.id);
      if (requestTokenRef.current !== requestToken) {
        return;
      }
      setTask(createdTask);
      setPhase("generating");
      schedulePoll(createdTask.task_id, requestToken);
    } catch (caught) {
      if (requestTokenRef.current !== requestToken) {
        return;
      }
      finish();
      setPhase("failed");
      setError(caught instanceof Error ? caught.message : "Face swap failed.");
    }
  }

  useEffect(() => {
    return () => {
      requestTokenRef.current += 1;
      finish();
    };
  }, []);

  return {
    phase,
    isBusy: phase === "uploading" || phase === "generating",
    sourceUpload,
    targetUpload,
    task,
    error,
    start,
    reset,
  };
}
