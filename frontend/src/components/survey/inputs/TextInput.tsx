interface Props {
  value: string
  onChange: (v: string) => void
  placeholder?: string
}

export default function TextInput({ value, onChange, placeholder }: Props) {
  return (
    <input
      type="text"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder ?? 'Type your answer…'}
      className="w-full rounded-xl border-2 border-gray-200 px-4 py-4 text-lg font-medium
                 text-gray-900 outline-none transition-all placeholder:text-gray-300
                 focus:border-brand-500 focus:ring-2 focus:ring-brand-100"
      autoFocus
    />
  )
}
