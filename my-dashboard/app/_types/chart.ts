export type ChartType =
  | 'bar'
  | 'bar-horizontal'
  | 'bar-grouped'
  | 'line'
  | 'line-multi'
  | 'pie'
  | 'card'
  | 'table'

export interface ChartConfig {
  type: ChartType
  title: string
  data: Array<Record<string, any>>
  
  // For bar/line charts
  xAxis?: string
  yAxis?: string
  series?: string[]
  
  // For pie charts
  nameKey?: string
  valueKey?: string
  
  // For card
  value?: number | string
  label?: string
  change?: number
  
  // For table
  columns?: Array<{ key: string; label: string }>
}

