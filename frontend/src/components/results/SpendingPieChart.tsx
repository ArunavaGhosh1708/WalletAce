import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import { SurveyState } from '../../types/survey'

interface Props {
  survey: SurveyState
}

const CATEGORY_CONFIG: { key: keyof SurveyState; label: string; color: string }[] = [
  { key: 'monthlyGroceries',    label: 'Groceries',     color: '#22c55e' },
  { key: 'monthlyDining',       label: 'Dining',        color: '#f97316' },
  { key: 'monthlyGas',          label: 'Gas / EV',      color: '#eab308' },
  { key: 'monthlyTravel',       label: 'Travel',        color: '#3b82f6' },
  { key: 'monthlyTransit',      label: 'Transit',       color: '#8b5cf6' },
  { key: 'monthlyStreaming',     label: 'Streaming',     color: '#ec4899' },
  { key: 'monthlyOnlineRetail', label: 'Online Retail', color: '#14b8a6' },
  { key: 'monthlyUtilities',    label: 'Utilities',     color: '#6b7280' },
]

function formatDollar(value: number) {
  return `$${value.toLocaleString()}`
}

export default function SpendingPieChart({ survey }: Props) {
  const data = CATEGORY_CONFIG
    .map(({ key, label, color }) => ({
      name: label,
      value: (survey[key] as number) * 12,
      color,
    }))
    .filter((d) => d.value > 0)

  const totalAnnual = data.reduce((sum, d) => sum + d.value, 0)

  if (data.length === 0) {
    return (
      <div className="flex h-48 items-center justify-center text-sm text-gray-400">
        No spending data entered.
      </div>
    )
  }

  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <h3 className="text-sm font-semibold text-gray-700">Your Annual Spending</h3>
        <span className="text-sm font-bold text-gray-900">{formatDollar(totalAnnual)}/yr</span>
      </div>

      <ResponsiveContainer width="100%" height={260}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="45%"
            innerRadius={60}
            outerRadius={90}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry) => (
              <Cell key={entry.name} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => formatDollar(value)}
            contentStyle={{ borderRadius: '8px', fontSize: '13px' }}
          />
          <Legend
            iconType="circle"
            iconSize={10}
            formatter={(value: string) => (
              <span className="text-xs text-gray-600">{value}</span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  )
}
