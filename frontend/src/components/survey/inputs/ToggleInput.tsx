interface Props {
  value: boolean
  onChange: (value: boolean) => void
}

export default function ToggleInput({ value, onChange }: Props) {
  return (
    <div className="flex items-center justify-center gap-6">
      {/* No button */}
      <button
        type="button"
        onClick={() => onChange(false)}
        className={[
          'w-32 rounded-xl border-2 py-4 text-sm font-semibold transition-all duration-150',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2',
          !value
            ? 'border-brand-500 bg-brand-50 text-brand-700'
            : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300',
        ].join(' ')}
      >
        No
      </button>

      {/* Visual toggle pill */}
      <button
        type="button"
        role="switch"
        aria-checked={value}
        onClick={() => onChange(!value)}
        className={[
          'relative inline-flex h-8 w-16 shrink-0 cursor-pointer items-center rounded-full',
          'border-2 border-transparent transition-colors duration-200 ease-in-out',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2',
          value ? 'bg-brand-500' : 'bg-gray-200',
        ].join(' ')}
      >
        <span
          className={[
            'pointer-events-none inline-block h-6 w-6 transform rounded-full',
            'bg-white shadow-md ring-0 transition duration-200 ease-in-out',
            value ? 'translate-x-8' : 'translate-x-0.5',
          ].join(' ')}
        />
      </button>

      {/* Yes button */}
      <button
        type="button"
        onClick={() => onChange(true)}
        className={[
          'w-32 rounded-xl border-2 py-4 text-sm font-semibold transition-all duration-150',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2',
          value
            ? 'border-brand-500 bg-brand-50 text-brand-700'
            : 'border-gray-200 bg-white text-gray-500 hover:border-gray-300',
        ].join(' ')}
      >
        Yes
      </button>
    </div>
  )
}
