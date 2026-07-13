export interface BaseKafkaEvent<T> {
  eventId: string;
  eventType: string;
  timestamp: string;
  producer: string;
  payload: T;
}
