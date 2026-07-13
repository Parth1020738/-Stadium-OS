export function generateCorrelationId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

export function parseIsoString(dateStr: string): Date {
  return new Date(dateStr);
}
