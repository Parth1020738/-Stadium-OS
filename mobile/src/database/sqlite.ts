import SQLite from 'react-native-sqlite-storage';

SQLite.enablePromise(true);

export interface OfflineOutboxItem {
  id: string;
  endpoint: string;
  payload: string;
  timestamp: string;
}

export async function initializeDatabase() {
  const db = await SQLite.openDatabase({ name: 'aegis_offline.db', location: 'default' });
  
  // Create outbox table for offline queued tasks
  await db.executeSql(`
    CREATE TABLE IF NOT EXISTS outbox (
      id TEXT PRIMARY KEY,
      endpoint TEXT NOT NULL,
      payload TEXT NOT NULL,
      timestamp TEXT NOT NULL
    );
  `);
  
  console.log('Local SQLite offline storage initialized successfully.');
  return db;
}
