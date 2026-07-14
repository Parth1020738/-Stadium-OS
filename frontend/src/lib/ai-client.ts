import type { AxiosRequestConfig } from "axios";
import { apiClient } from "./api-client";

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface AIChatRequest {
  messages: ChatMessage[];
  session_id?: string;
}

export interface AIChatResponse {
  response: string;
  session_id: string;
  tokens_used: number;
}

export const aiClient = {
  async chat(req: AIChatRequest, config?: AxiosRequestConfig): Promise<AIChatResponse> {
    const res = await apiClient.post<AIChatResponse>("/ai/chat", req, config);
    return res.data;
  },

  async summarize(text: string, maxLength = 500, config?: AxiosRequestConfig): Promise<string> {
    const res = await apiClient.post<{ summary: string }>("/ai/summarize", { text, max_length: maxLength }, config);
    return res.data.summary;
  },

  async recommend(scenario: string, parameters?: Record<string, unknown>, config?: AxiosRequestConfig) {
    const res = await apiClient.post("/ai/recommend", { scenario, parameters }, config);
    return res.data;
  },

  async translate(text: string, targetLanguage: string, config?: AxiosRequestConfig): Promise<string> {
    const res = await apiClient.post<{ translated_text: string }>("/ai/translate", { text, target_language: targetLanguage }, config);
    return res.data.translated_text;
  },

  async briefing(scope = "stadium", config?: AxiosRequestConfig) {
    const res = await apiClient.post("/ai/briefing", { scope }, config);
    return res.data;
  },

  async copilot(query: string, config?: AxiosRequestConfig) {
    const res = await apiClient.post("/ai/copilot", { query }, config);
    return res.data;
  },

  /**
   * Listen to the Server-Sent Event stream from backend for a specific prompt.
   */
  stream(prompt: string, onChunk: (text: string) => void, onDone: () => void, onError: (err: unknown) => void, signal?: AbortSignal) {
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
    const url = `${baseUrl}/ai/stream?prompt=${encodeURIComponent(prompt)}`;

    const eventSource = new EventSource(url);

    // Attach token if needed (Note: default EventSource doesn't support custom headers easily, 
    // so we pass token via cookie or rely on session if cookies are used, or pass token in URL.
    // For SSE query token authentication is standard).
    
    eventSource.onmessage = (event) => {
      if (signal?.aborted) {
        eventSource.close();
        onDone();
        return;
      }
      if (event.data === "[DONE]") {
        eventSource.close();
        onDone();
        return;
      }
      try {
        const parsed = JSON.parse(event.data);
        if (parsed.error) {
          onError(parsed.error);
          eventSource.close();
        } else if (parsed.text) {
          onChunk(parsed.text);
        }
      } catch (err) {
        onError(err);
      }
    };

    eventSource.onerror = (err) => {
      onError(err);
      eventSource.close();
    };

    if (signal) {
      signal.addEventListener("abort", () => {
        eventSource.close();
      });
    }

    return () => {
      eventSource.close();
    };
  }
};
