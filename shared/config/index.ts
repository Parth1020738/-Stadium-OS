import { z } from 'zod';

export const configSchema = z.object({
  NODE_ENV: z.enum(['development', 'production', 'test']).default('development'),
  PORT: z.coerce.number().default(3000),
  DATABASE_URL: z.string(),
  REDIS_URL: z.string(),
  KAFKA_BOOTSTRAP_SERVERS: z.string(),
  JWT_SECRET: z.string().min(32),
  JWT_EXPIRES_IN: z.coerce.number().default(3600),
});

export type Config = z.infer<typeof configSchema>;
