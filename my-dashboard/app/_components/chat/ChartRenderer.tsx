'use client'

import { ChartConfig } from '@/app/_types/chart'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'

interface ChartRendererProps {
  config: ChartConfig
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

export function ChartRenderer({ config }: ChartRendererProps) {
  if (config.type === 'line' || config.type === 'line-multi') {
    return (
      <div className="w-full mt-4 mb-6" style={{ minHeight: '320px', height: '320px' }}>
        <h3 className="text-sm font-semibold mb-2">{config.title}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={config.data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={config.xAxis} />
            <YAxis />
            <Tooltip />
            <Legend />
            {config.series && config.series.length > 0 ? (
              config.series.map((series, index) => (
                <Line
                  key={series}
                  type="monotone"
                  dataKey={series}
                  stroke={COLORS[index % COLORS.length]}
                  strokeWidth={2}
                />
              ))
            ) : (
              <Line
                type="monotone"
                dataKey={config.yAxis}
                stroke={COLORS[0]}
                strokeWidth={2}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (config.type === 'bar' || config.type === 'bar-grouped') {
    return (
      <div className="w-full mt-4 mb-6" style={{ minHeight: '320px', height: '320px' }}>
        <h3 className="text-sm font-semibold mb-2">{config.title}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={config.data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={config.xAxis} />
            <YAxis />
            <Tooltip />
            <Legend />
            {config.series && config.series.length > 0 ? (
              config.series.map((series, index) => (
                <Bar
                  key={series}
                  dataKey={series}
                  fill={COLORS[index % COLORS.length]}
                />
              ))
            ) : (
              <Bar dataKey={config.yAxis} fill={COLORS[0]} />
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (config.type === 'bar-horizontal') {
    return (
      <div className="w-full mt-4 mb-6" style={{ minHeight: '320px', height: '320px' }}>
        <h3 className="text-sm font-semibold mb-2">{config.title}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={config.data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey={config.xAxis} type="category" width={100} />
            <Tooltip />
            <Legend />
            {config.series && config.series.length > 0 ? (
              config.series.map((series, index) => (
                <Bar
                  key={series}
                  dataKey={series}
                  fill={COLORS[index % COLORS.length]}
                />
              ))
            ) : (
              <Bar dataKey={config.yAxis} fill={COLORS[0]} />
            )}
          </BarChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (config.type === 'pie') {
    return (
      <div className="w-full mt-4 mb-6" style={{ minHeight: '320px', height: '320px' }}>
        <h3 className="text-sm font-semibold mb-2">{config.title}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={config.data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name} ${percent ? (percent * 100).toFixed(0) : 0}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey={config.valueKey || 'value'}
              nameKey={config.nameKey || 'name'}
            >
              {config.data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    )
  }

  if (config.type === 'card') {
    return (
      <div className="mt-4 mb-6 p-4 border rounded-lg bg-muted/50">
        <h3 className="text-sm font-semibold mb-2">{config.title}</h3>
        <div className="text-2xl font-bold">{config.value}</div>
        {config.label && <div className="text-sm text-muted-foreground mt-1">{config.label}</div>}
        {config.change !== undefined && (
          <div className={`text-sm mt-1 ${config.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {config.change >= 0 ? '+' : ''}{config.change}%
          </div>
        )}
      </div>
    )
  }

  if (config.type === 'table') {
    return (
      <div className="mt-4 mb-6">
        <h3 className="text-sm font-semibold mb-2">{config.title}</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse border border-border">
            <thead className="bg-muted">
              <tr>
                {config.columns?.map((col) => (
                  <th key={col.key} className="border border-border px-4 py-2 text-left font-semibold">
                    {col.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {config.data.map((row, index) => (
                <tr key={index} className="border-b border-border">
                  {config.columns?.map((col) => (
                    <td key={col.key} className="border border-border px-4 py-2">
                      {row[col.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  return (
    <div className="mt-4 p-4 border rounded-lg bg-muted/50">
      <p className="text-sm text-muted-foreground">Chart type &quot;{config.type}&quot; not yet implemented</p>
    </div>
  )
}

