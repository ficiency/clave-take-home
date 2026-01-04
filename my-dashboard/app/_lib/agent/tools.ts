import { DynamicStructuredTool } from '@langchain/core/tools'
import { z } from 'zod'
import { getPostgresPool } from '@/app/_lib/db/postgres'
import { ChartConfig, ChartType } from '@/app/_types/chart'

const ALLOWED_TABLES = [
  'locations',
  'orders',
  'order_items',
  'ai_orders',
  'ai_order_items',
]

const DANGEROUS_KEYWORDS = [
  'DELETE',
  'DROP',
  'INSERT',
  'UPDATE',
  'ALTER',
  'CREATE',
  'TRUNCATE',
  'GRANT',
  'REVOKE',
]

function validateSQL(sql: string): { valid: boolean; error?: string } {
  const upperSQL = sql.trim().toUpperCase()
  
  // Permitir SELECT directo o CTE (WITH ... SELECT)
  const isSelect = upperSQL.startsWith('SELECT')
  const isCTE = upperSQL.startsWith('WITH')
  
  if (!isSelect && !isCTE) {
    return { valid: false, error: 'Only SELECT statements are allowed (including CTEs with WITH)' }
  }

  // Si es CTE, verificar que solo contenga SELECTs dentro
  if (isCTE) {
    // Contar SELECTs y verificar que haya al menos uno
    const selectCount = (upperSQL.match(/\bSELECT\b/g) || []).length
    if (selectCount === 0) {
      return { valid: false, error: 'CTE must contain SELECT statements' }
    }
  }

  for (const keyword of DANGEROUS_KEYWORDS) {
    // Escapar la keyword para regex (por si tiene caracteres especiales)
    const escapedKeyword = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    // Buscar la keyword como palabra completa usando word boundaries
    const keywordPattern = new RegExp(`\\b${escapedKeyword}\\b`, 'i')
    if (keywordPattern.test(upperSQL)) {
      return { valid: false, error: `Dangerous keyword detected: ${keyword}` }
    }
  }

  // Check for table names (case-insensitive matching)
  for (const table of ALLOWED_TABLES) {
    // Escape table name for regex (in case it has special chars)
    const escapedTable = table.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    // Match "FROM table" or "FROM "table"" or "JOIN table" etc
    const fromPattern = new RegExp(`\\bFROM\\s+["\`]?${escapedTable}["\`]?\\b`, 'i')
    const joinPattern = new RegExp(`\\bJOIN\\s+["\`]?${escapedTable}["\`]?\\b`, 'i')
    if (fromPattern.test(sql) || joinPattern.test(sql)) {
      return { valid: true }
    }
  }

  return { valid: false, error: `Query must use one of the allowed tables: ${ALLOWED_TABLES.join(', ')}` }
}

export function createExecuteSQLTool() {
  return new DynamicStructuredTool({
    name: 'execute_sql',
    description: 'Execute a SQL SELECT query against the database. Use when user asks for data or analytics. Only SELECT statements are allowed.',
    schema: z.object({
      query: z.string().describe('SQL SELECT statement (read-only)'),
    }),
    func: async ({ query }) => {
      try {
        console.log('\n[TOOL: execute_sql] Executing SQL query:')
        console.log('─'.repeat(80))
        console.log(query)
        console.log('─'.repeat(80))

        const validation = validateSQL(query)
        if (!validation.valid) {
          console.log(`[TOOL: execute_sql] ❌ Validation failed: ${validation.error}`)
          return JSON.stringify({ error: validation.error })
        }

        const pool = getPostgresPool()
        const result = await pool.query(query)

        console.log(`[TOOL: execute_sql] ✅ Query executed successfully. Rows returned: ${result.rows.length}`)
        if (result.rows.length > 0) {
          console.log(`[TOOL: execute_sql] First row sample:`, JSON.stringify(result.rows[0], null, 2))
        }
        console.log('')

        return JSON.stringify({ data: result.rows || [] })
      } catch (error) {
        console.log(`[TOOL: execute_sql] ❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
        console.log('')
        return JSON.stringify({ 
          error: error instanceof Error ? error.message : 'Unknown error executing SQL' 
        })
      }
    },
  })
}

export function createChartTool() {
  return new DynamicStructuredTool({
    name: 'create_chart',
    description: 'Create a chart visualization from data. Use this AFTER executing SQL queries to visualize the results. The chart will be displayed to the user.',
    schema: z.object({
      chartConfig: z.object({
        type: z.enum(['bar', 'bar-horizontal', 'bar-grouped', 'line', 'line-multi', 'pie', 'card', 'table']),
        title: z.string(),
        data: z.array(z.record(z.string(), z.any())),
        xAxis: z.string().optional(),
        yAxis: z.string().optional(),
        series: z.array(z.string()).optional(),
        nameKey: z.string().optional(),
        valueKey: z.string().optional(),
        value: z.union([z.number(), z.string()]).optional(),
        label: z.string().optional(),
        change: z.number().optional(),
        columns: z.array(z.object({
          key: z.string(),
          label: z.string(),
        })).optional(),
      }),
    }),
    func: async ({ chartConfig }) => {
      try {
        console.log('\n[TOOL: create_chart] Creating chart:')
        console.log('─'.repeat(80))
        console.log(JSON.stringify(chartConfig, null, 2))
        console.log('─'.repeat(80))
        console.log('')

        return JSON.stringify({ success: true, chart: chartConfig })
      } catch (error) {
        console.log(`[TOOL: create_chart] ❌ Error: ${error instanceof Error ? error.message : 'Unknown error'}`)
        console.log('')
        return JSON.stringify({ 
          error: error instanceof Error ? error.message : 'Unknown error creating chart' 
        })
      }
    },
  })
}

