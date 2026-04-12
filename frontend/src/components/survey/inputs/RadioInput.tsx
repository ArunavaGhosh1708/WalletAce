import { RadioOption } from '../../../data/questions'

interface Props {
  options: RadioOption[]
  value: string | number
  onChange: (value: string | number) => void
}

export default function RadioInput({ options, value, onChange }: Props) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      {options.map((opt) => {
        const selected = value === opt.value
        return (
          <button
            key={String(opt.value)}
            type="button"
            onClick={() => onChange(opt.value)}
            className={[
              'flex items-center gap-3 rounded-xl border-2 px-5 py-4 text-left',
              'transition-all duration-150 hover:border-brand-500 focus:outline-none',
              'focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2',
              selected
                ? 'border-brand-500 bg-brand-50 text-brand-700 font-semibold'
                : 'border-gray-200 bg-white text-gray-700 hover:bg-gray-50',
            ].join(' ')}
          >
            {/* Radio circle */}
            <span
              className={[
                'flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2',
                selected ? 'border-brand-500' : 'border-gray-300',
              ].join(' ')}
            >
              {selected && (
                <span className="h-2.5 w-2.5 rounded-full bg-brand-500" />
              )}
            </span>
            <span className="text-sm leading-snug">{opt.label}</span>
          </button>
        )
      })}
    </div>
  )
}
