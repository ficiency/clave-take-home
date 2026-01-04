import { Pool } from 'pg'

let poolInstance: Pool | null = null

export function getPostgresPool(): Pool {
  if (!poolInstance) {
    const connectionString = process.env.DATABASE_URL || process.env.SUPABASE_DB_URL
    
    if (!connectionString) {
      throw new Error('DATABASE_URL or SUPABASE_DB_URL environment variable is required for SQL execution')
    }

    poolInstance = new Pool({
      connectionString,
      ssl: connectionString.includes('supabase') ? { rejectUnauthorized: false } : undefined,
    })
  }

  return poolInstance
}

