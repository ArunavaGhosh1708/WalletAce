import { CardResult } from '../../api/recommend'

interface Props {
  card: CardResult
  rank: 1 | 2
}

const CATEGORY_LABELS: Record<string, string> = {
  groceries:    'Groceries',
  dining:       'Dining',
  gas:          'Gas / EV',
  travel:       'Travel',
  transit:      'Transit',
  streaming:    'Streaming',
  online_retail:'Online Retail',
  utilities:    'Utilities',
}

function fmt(n: number) {
  return n < 0
    ? `-$${Math.abs(n).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
    : `$${n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

function EANVColor(eanv: number) {
  if (eanv >= 500) return 'text-green-600'
  if (eanv >= 0)   return 'text-gray-800'
  return 'text-red-500'
}

export default function CardResultCard({ card, rank }: Props) {
  const displayEANV = card.eanv
  const displayBonus = card.signup_bonus_value

  // Category breakdown — only non-zero entries, sorted descending
  const breakdown = Object.entries(card.category_breakdown)
    .map(([key, value]) => ({ key, label: CATEGORY_LABELS[key] ?? key, value: value as number }))
    .filter((e) => e.value > 0)
    .sort((a, b) => b.value - a.value)

  const maxBreakdown = breakdown[0]?.value ?? 1

  return (
    <div
      className={[
        'flex flex-col rounded-2xl border-2 bg-white shadow-sm',
        rank === 1 ? 'border-brand-500' : 'border-gray-200',
      ].join(' ')}
    >
      {/* Header bar */}
      <div
        className={[
          'flex items-center justify-between rounded-t-2xl px-5 py-3 text-xs font-semibold',
          rank === 1
            ? 'bg-brand-500 text-white'
            : 'bg-gray-50 text-gray-500',
        ].join(' ')}
      >
        <span>{rank === 1 ? '⭐ Best Match' : '2nd Pick'}</span>
        <span className="uppercase tracking-wider">{card.reward_type.replace('_', ' ')}</span>
      </div>

      <div className="flex flex-1 flex-col gap-5 p-5">
        {/* Card identity */}
        <div>
          <p className="text-xs font-medium uppercase tracking-widest text-gray-400">
            {card.issuer}
          </p>
          <h2 className="text-lg font-bold leading-snug text-gray-900">{card.card_name}</h2>
          <p className="mt-1 text-sm text-gray-500">
            {card.annual_fee === 0 ? 'No annual fee' : `$${card.annual_fee}/yr annual fee`}
            {card.reward_network ? ` · ${card.reward_network}` : ''}
          </p>
        </div>

        {/* EANV */}
        <div className="rounded-xl bg-gray-50 p-4">
          <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-gray-400">
            Est. Annual Net Value
          </p>
          <p className={`text-4xl font-extrabold tabular-nums ${EANVColor(displayEANV)}`}>
            {fmt(displayEANV)}
          </p>
          <div className="mt-3 space-y-1 text-sm">
            <div className="flex justify-between text-gray-600">
              <span>Rewards earned</span>
              <span className="font-medium text-green-600">+{fmt(card.rewards_total)}</span>
            </div>
            {displayBonus > 0 && (
              <div className="flex justify-between text-gray-600">
                <span>Sign-up bonus</span>
                <span className="font-medium text-green-600">+{fmt(displayBonus)}</span>
              </div>
            )}
            {card.annual_fee > 0 && (
              <div className="flex justify-between text-gray-600">
                <span>Annual fee</span>
                <span className="font-medium text-red-500">-{fmt(card.annual_fee)}</span>
              </div>
            )}
          </div>
        </div>

        {/* Why this card */}
        <div className="rounded-xl border border-brand-100 bg-brand-50 px-4 py-3">
          <p className="mb-1 text-xs font-semibold uppercase tracking-widest text-brand-600">
            Why this card?
          </p>
          <p className="text-sm text-gray-700">{card.why_this_card}</p>
        </div>

        {/* Category breakdown */}
        {breakdown.length > 0 && (
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-gray-400">
              Rewards by category
            </p>
            <ul className="space-y-2">
              {breakdown.map(({ key, label, value }) => (
                <li key={key} className="flex items-center gap-3">
                  <span className="w-24 shrink-0 text-xs text-gray-500">{label}</span>
                  <div className="flex-1 overflow-hidden rounded-full bg-gray-100" style={{ height: 6 }}>
                    <div
                      className="h-full rounded-full bg-brand-500 transition-all duration-500"
                      style={{ width: `${(value / maxBreakdown) * 100}%` }}
                    />
                  </div>
                  <span className="w-16 text-right text-xs font-semibold tabular-nums text-gray-700">
                    {fmt(value)}/yr
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Perks */}
        {(card.has_lounge_access || card.has_global_entry || card.intro_apr_months > 0) && (
          <div className="flex flex-wrap gap-2">
            {card.has_lounge_access && (
              <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                ✈ Lounge Access
              </span>
            )}
            {card.has_global_entry && (
              <span className="rounded-full bg-purple-50 px-3 py-1 text-xs font-semibold text-purple-700">
                🛂 Global Entry
              </span>
            )}
            {card.intro_apr_months > 0 && (
              <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-semibold text-green-700">
                0% APR for {card.intro_apr_months} months
              </span>
            )}
          </div>
        )}

        {/* APR */}
        <p className="text-xs text-gray-400">
          Ongoing APR: {card.ongoing_apr_min}% – {card.ongoing_apr_max}%
        </p>

        {/* Apply Now CTA */}
        <a
          href={card.affiliate_link}
          target="_blank"
          rel="noopener noreferrer sponsored"
          className={[
            'mt-auto block rounded-xl py-3.5 text-center text-sm font-bold',
            'transition-all duration-150 hover:scale-[1.02] active:scale-100',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500',
            rank === 1
              ? 'bg-brand-500 text-white shadow-md hover:bg-brand-600'
              : 'border-2 border-brand-500 text-brand-600 hover:bg-brand-50',
          ].join(' ')}
        >
          Apply Now →
        </a>

      </div>
    </div>
  )
}
