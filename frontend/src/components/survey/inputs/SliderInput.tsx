import { SliderFormat } from '../../../data/questions'

interface Props {
  value: number
  min: number
  max: number
  step: number
  format: SliderFormat
  onChange: (value: number) => void
}

function formatValue(value: number, format: SliderFormat): string {
  if (format === 'dollar') {
    return `$${value.toLocaleString()}`
  }
  return String(value)
}

export default function SliderInput({ value, min, max, step, format, onChange }: Props) {
  const pct = ((value - min) / (max - min)) * 100

  return (
    <div className="space-y-4">
      {/* Value badge */}
      <div className="flex justify-center">
        <span className="inline-block rounded-2xl bg-brand-500 px-6 py-2 text-2xl font-bold text-white tabular-nums shadow-sm">
          {formatValue(value, format)}
        </span>
      </div>

      {/* Range input */}
      <div className="relative px-1">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="slider-thumb w-full cursor-pointer appearance-none rounded-full bg-gray-200 accent-brand-500"
          style={{
            background: `linear-gradient(to right, #4f46e5 ${pct}%, #e5e7eb ${pct}%)`,
            height: '6px',
          }}
        />
        {/* Min / Max labels */}
        <div className="mt-2 flex justify-between text-xs text-gray-400">
          <span>{formatValue(min, format)}</span>
          <span>{formatValue(max, format)}</span>
        </div>
      </div>
    </div>
  )
}
