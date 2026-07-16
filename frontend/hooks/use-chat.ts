"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getChatRoles, streamChatCompletion } from "@/services/api";
import type { ChatMessage, ChatRoleInfo } from "@/types/chat";

const defaultRoleId = "general_assistant";
const defaultModel = "deepseek";

type UseChatState = {
  roles: ChatRoleInfo[];
  selectedRoleId: string;
  model: string;
  messages: ChatMessage[];
  input: string;
  rolesLoading: boolean;
  sending: boolean;
  streaming: boolean;
  error: string | null;
  rolesError: string | null;
};

export function useChat() {
  const [state, setState] = useState<UseChatState>({
    roles: [],
    selectedRoleId: defaultRoleId,
    model: defaultModel,
    messages: [],
    input: "",
    rolesLoading: true,
    sending: false,
    streaming: false,
    error: null,
    rolesError: null,
  });
  const abortControllerRef = useRef<AbortController | null>(null);

  const loadRoles = useCallback(async () => {
    setState((current) => ({ ...current, rolesLoading: true, rolesError: null }));
    try {
      const response = await getChatRoles();
      setState((current) => ({
        ...current,
        roles: response.roles,
        selectedRoleId: response.roles.some((role) => role.id === current.selectedRoleId)
          ? current.selectedRoleId
          : response.roles[0]?.id ?? defaultRoleId,
        rolesLoading: false,
        rolesError: null,
      }));
    } catch (error: unknown) {
      setState((current) => ({
        ...current,
        rolesLoading: false,
        rolesError: getErrorMessage(error),
      }));
    }
  }, []);

  useEffect(() => {
    let isActive = true;
    void getChatRoles()
      .then((response) => {
        if (!isActive) {
          return;
        }
        setState((current) => ({
          ...current,
          roles: response.roles,
          selectedRoleId: response.roles.some((role) => role.id === current.selectedRoleId)
            ? current.selectedRoleId
            : response.roles[0]?.id ?? defaultRoleId,
          rolesLoading: false,
          rolesError: null,
        }));
      })
      .catch((error: unknown) => {
        if (isActive) {
          setState((current) => ({
            ...current,
            rolesLoading: false,
            rolesError: getErrorMessage(error),
          }));
        }
      });
    return () => {
      isActive = false;
      abortControllerRef.current?.abort();
    };
  }, []);

  const setInput = useCallback((input: string) => {
    setState((current) => ({ ...current, input }));
  }, []);

  const selectRole = useCallback((roleId: string) => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setState((current) => ({
      ...current,
      selectedRoleId: roleId,
      messages: [],
      input: "",
      sending: false,
      streaming: false,
      error: null,
    }));
  }, []);

  const clearConversation = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setState((current) => ({
      ...current,
      messages: [],
      input: "",
      sending: false,
      streaming: false,
      error: null,
    }));
  }, []);

  const newConversation = clearConversation;

  const stopGeneration = useCallback(() => {
    abortControllerRef.current?.abort();
    abortControllerRef.current = null;
    setState((current) => ({
      ...current,
      sending: false,
      streaming: false,
      error: current.streaming ? "生成已停止" : current.error,
    }));
  }, []);

  const sendMessage = useCallback(async () => {
    const content = state.input.trim();
    if (!content || state.sending) {
      return;
    }

    const nextMessages: ChatMessage[] = [...state.messages, { role: "user", content }, { role: "assistant", content: "" }];
    const assistantIndex = nextMessages.length - 1;
    const controller = new AbortController();
    abortControllerRef.current = controller;

    setState((current) => ({
      ...current,
      messages: nextMessages,
      input: "",
      sending: true,
      streaming: true,
      error: null,
    }));

    try {
      await streamChatCompletion(
        {
          role_id: state.selectedRoleId,
          model: state.model,
          messages: nextMessages.slice(0, -1),
          temperature: 0.7,
          max_tokens: 1024,
          stream: true,
        },
        {
          signal: controller.signal,
          onDelta: (delta) => {
            setState((current) => ({
              ...current,
              messages: current.messages.map((message, index) =>
                index === assistantIndex ? { ...message, content: message.content + delta } : message,
              ),
            }));
          },
        },
      );
      setState((current) => ({ ...current, sending: false, streaming: false }));
    } catch (error: unknown) {
      if (controller.signal.aborted) {
        setState((current) => ({ ...current, sending: false, streaming: false, error: "生成已停止" }));
        return;
      }
      setState((current) => ({
        ...current,
        sending: false,
        streaming: false,
        error: getErrorMessage(error),
      }));
    } finally {
      if (abortControllerRef.current === controller) {
        abortControllerRef.current = null;
      }
    }
  }, [state.input, state.messages, state.model, state.selectedRoleId, state.sending]);

  return {
    ...state,
    canSend: state.input.trim().length > 0 && !state.sending,
    setInput,
    selectRole,
    sendMessage,
    stopGeneration,
    clearConversation,
    newConversation,
    loadRoles,
  };
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "请求失败，请稍后重试";
}
