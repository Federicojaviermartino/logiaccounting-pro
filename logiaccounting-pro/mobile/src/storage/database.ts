/**
 * SQLite Database Manager - Offline data storage
 */

import * as SQLite from 'expo-sqlite';

const DB_NAME = 'logiaccounting.db';

let db: SQLite.SQLiteDatabase | null = null;

export async function initializeDatabase(): Promise<void> {
  db = await SQLite.openDatabaseAsync(DB_NAME);

  await db.execAsync(`
    PRAGMA journal_mode = WAL;
    PRAGMA foreign_keys = ON;

    -- Invoices table
    CREATE TABLE IF NOT EXISTS invoices (
      id TEXT PRIMARY KEY,
      invoice_number TEXT NOT NULL,
      customer_id TEXT,
      customer_name TEXT,
      status TEXT DEFAULT 'draft',
      issue_date TEXT,
      due_date TEXT,
      subtotal REAL DEFAULT 0,
      tax REAL DEFAULT 0,
      total REAL DEFAULT 0,
      currency TEXT DEFAULT 'USD',
      notes TEXT,
      payment_terms TEXT,
      created_at TEXT,
      updated_at TEXT,
      synced_at TEXT,
      local_modified_at TEXT,
      is_deleted INTEGER DEFAULT 0
    );

    -- Invoice items table
    CREATE TABLE IF NOT EXISTS invoice_items (
      id TEXT PRIMARY KEY,
      invoice_id TEXT NOT NULL,
      description TEXT,
      quantity REAL DEFAULT 1,
      unit_price REAL DEFAULT 0,
      tax_rate REAL DEFAULT 0,
      total REAL DEFAULT 0,
      FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
    );

    -- Inventory table
    CREATE TABLE IF NOT EXISTS inventory (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      sku TEXT UNIQUE,
      barcode TEXT,
      description TEXT,
      quantity INTEGER DEFAULT 0,
      reorder_level INTEGER DEFAULT 0,
      unit_price REAL DEFAULT 0,
      cost_price REAL DEFAULT 0,
      category TEXT,
      image_url TEXT,
      created_at TEXT,
      updated_at TEXT,
      synced_at TEXT,
      local_modified_at TEXT,
      is_deleted INTEGER DEFAULT 0
    );

    -- Customers table
    CREATE TABLE IF NOT EXISTS customers (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      email TEXT,
      phone TEXT,
      address TEXT,
      city TEXT,
      country TEXT,
      tax_id TEXT,
      notes TEXT,
      created_at TEXT,
      updated_at TEXT,
      synced_at TEXT,
      local_modified_at TEXT,
      is_deleted INTEGER DEFAULT 0
    );

    -- Expenses table
    CREATE TABLE IF NOT EXISTS expenses (
      id TEXT PRIMARY KEY,
      description TEXT,
      amount REAL DEFAULT 0,
      currency TEXT DEFAULT 'USD',
      category TEXT,
      vendor TEXT,
      expense_date TEXT,
      receipt_url TEXT,
      notes TEXT,
      created_at TEXT,
      updated_at TEXT,
      synced_at TEXT,
      local_modified_at TEXT,
      is_deleted INTEGER DEFAULT 0
    );

    -- Sync queue table
    CREATE TABLE IF NOT EXISTS sync_queue (
      id TEXT PRIMARY KEY,
      entity_type TEXT NOT NULL,
      entity_id TEXT NOT NULL,
      operation TEXT NOT NULL,
      payload TEXT,
      priority INTEGER DEFAULT 0,
      retry_count INTEGER DEFAULT 0,
      last_error TEXT,
      created_at TEXT,
      processed_at TEXT
    );

    -- Create indexes for faster queries
    CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
    CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_id);
    CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(issue_date);
    CREATE INDEX IF NOT EXISTS idx_invoices_synced ON invoices(synced_at);
    CREATE INDEX IF NOT EXISTS idx_inventory_sku ON inventory(sku);
    CREATE INDEX IF NOT EXISTS idx_inventory_barcode ON inventory(barcode);
    CREATE INDEX IF NOT EXISTS idx_sync_queue_priority ON sync_queue(priority DESC, created_at ASC);
  `);
}

export function getDatabase(): SQLite.SQLiteDatabase {
  if (!db) {
    throw new Error('Database not initialized. Call initializeDatabase() first.');
  }
  return db;
}

export async function closeDatabase(): Promise<void> {
  if (db) {
    await db.closeAsync();
    db = null;
  }
}

export async function clearAllData(): Promise<void> {
  const database = getDatabase();
  await database.execAsync(`
    DELETE FROM invoice_items;
    DELETE FROM invoices;
    DELETE FROM inventory;
    DELETE FROM customers;
    DELETE FROM expenses;
    DELETE FROM sync_queue;
  `);
}

export async function getTableRowCount(tableName: string): Promise<number> {
  const database = getDatabase();
  const result = await database.getFirstAsync<{ count: number }>(
    `SELECT COUNT(*) as count FROM ${tableName} WHERE is_deleted = 0`
  );
  return result?.count ?? 0;
}

export async function getDatabaseStats(): Promise<{
  invoices: number;
  inventory: number;
  customers: number;
  expenses: number;
  pendingSync: number;
}> {
  const [invoices, inventory, customers, expenses, pendingSync] = await Promise.all([
    getTableRowCount('invoices'),
    getTableRowCount('inventory'),
    getTableRowCount('customers'),
    getTableRowCount('expenses'),
    (async () => {
      const db = getDatabase();
      const result = await db.getFirstAsync<{ count: number }>(
        'SELECT COUNT(*) as count FROM sync_queue WHERE processed_at IS NULL'
      );
      return result?.count ?? 0;
    })(),
  ]);

  return { invoices, inventory, customers, expenses, pendingSync };
}
