import { useState, useCallback, useRef } from "react";
import { aiClient, ChatMessage, AIChatResponse } from "../lib/ai-client";

export interface UseAIReturn {
  loading: boolean;
  error: string | null;
  result: unknown;
  streamText: string;
  chat: (messages: ChatMessage[], sessionId?: string) => Promise<AIChatResponse | null>;
  summarize: (text: string, maxLength?: number) => Promise<string | null>;
  recommend: (scenario: string, parameters?: Record<string, unknown>) => Promise<unknown>;
  translate: (text: string, targetLanguage: string) => Promise<string | null>;
  copilot: (query: string) => Promise<unknown>;
  startStream: (prompt: string) => void;
  cancel: () => void;
  reset: () => void;
}

interface CustomError {
  message?: string;
  response?: {
    data?: {
      detail?: string;
    };
  };
}

export function useAI(): UseAIReturn {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<unknown>(null);
  const [streamText, setStreamText] = useState<string>("");

  const abortControllerRef = useRef<AbortController | null>(null);
  const streamCleanupRef = useRef<(() => void) | null>(null);

  const cancel = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (streamCleanupRef.current) {
      streamCleanupRef.current();
    }
    setLoading(false);
  }, []);

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setResult(null);
    setStreamText("");
    cancel();
  }, [cancel]);

  const executeSafe = useCallback(async <T>(apiCall: (signal?: AbortSignal) => Promise<T>): Promise<T | null> => {
    setLoading(true);
    setError(null);
    cancel();

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const data = await apiCall(controller.signal);
      setResult(data);
      setLoading(false);
      return data;
    } catch (err: unknown) {
      const customErr = err as CustomError;
      if (customErr.message === "canceled" || customErr.message === "AbortError") {
        return null;
      }
      const errMsg = customErr.response?.data?.detail || customErr.message || "An error occurred during AI execution.";
      setError(errMsg);
      setLoading(false);
      return null;
    }
  }, [cancel]);

  const chat = useCallback(async (messages: ChatMessage[], sessionId?: string) => {
    return executeSafe((signal) => aiClient.chat({ messages, session_id: sessionId }, { signal }));
  }, [executeSafe]);

  const summarize = useCallback(async (text: string, maxLength = 500) => {
    return executeSafe((signal) => aiClient.summarize(text, maxLength, { signal }));
  }, [executeSafe]);

  const recommend = useCallback(async (scenario: string, parameters?: Record<string, unknown>) => {
    return executeSafe((signal) => aiClient.recommend(scenario, parameters, { signal }));
  }, [executeSafe]);

  const translate = useCallback(async (text: string, targetLanguage: string) => {
    return executeSafe((signal) => aiClient.translate(text, targetLanguage, { signal }));
  }, [executeSafe]);

  const copilot = useCallback(async (query: string) => {
    return executeSafe((signal) => aiClient.copilot(query, { signal }));
  }, [executeSafe]);

  const startStream = useCallback((prompt: string) => {
    setLoading(true);
    setError(null);
    setStreamText("");
    cancel();

    const controller = new AbortController();
    abortControllerRef.current = controller;

    const cleanup = aiClient.stream(
      prompt,
      (chunk) => {
        setStreamText((prev) => prev + chunk);
      },
      () => {
        setLoading(false);
      },
      (err) => {
        const errorObj = err as Error;
        setError(errorObj?.message || String(err));
        setLoading(false);
      },
      controller.signal
    );

    streamCleanupRef.current = cleanup;
  }, [cancel]);

  return {
    loading,
    error,
    result,
    streamText,
    chat,
    summarize,
    recommend,
    translate,
    copilot,
    startStream,
    cancel,
    reset
  };
}
