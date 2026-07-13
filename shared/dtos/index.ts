export interface BaseResponse<T> {
  traceId: string;
  correlationId: string;
  serverTimestamp: string;
  executionDurationMs: number;
  data: T | null;
  error: ErrorPayload | null;
}

export interface ErrorPayload {
  code: string;
  message: string;
  severity: 'WARNING' | 'CRITICAL';
  details?: Array<{ field: string; value: string; issue: string }>;
}
