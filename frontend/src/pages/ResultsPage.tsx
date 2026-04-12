import { useLocation, useNavigate } from 'react-router-dom'
import CardResultCard from '../components/results/CardResultCard'
import SpendingPieChart from '../components/results/SpendingPieChart'
import { RecommendationResponse } from '../api/recommend'
import { SurveyState } from '../types/survey'

interface LocationState {
  result: RecommendationResponse
  survey: SurveyState
}

export default function ResultsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LocationState | null

  // Guard: if navigated directly without state, redirect to home
  if (!state?.result) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-gray-50 px-4">
        <p className="text-gray-500">No results found. Please take the survey first.</p>
        <button
          onClick={() => navigate('/')}
          className="rounded-xl bg-brand-500 px-6 py-3 text-sm font-semibold text-white"
        >
          Start Over
        </button>
      </div>
    )
  }

  const { result, survey } = state
  const { top_cards, cards_evaluated, session_id } = result
  const userName = survey.userName?.trim() || null

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top banner */}
      <header className="bg-brand-600 px-4 py-5 text-center text-white sm:px-8">
        <p className="text-xs font-semibold uppercase tracking-widest text-brand-200">
          {userName ? `${userName}'s personalised results` : 'Your personalised results'}
        </p>
        <h1 className="mt-1 text-2xl font-extrabold sm:text-3xl">
          You could earn up to{' '}
          <span className="text-yellow-300">
            ${Math.max(0, top_cards[0].eanv).toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </span>{' '}
          this year
        </h1>
        <p className="mt-1 text-sm text-brand-100">
          Based on your spending profile · {cards_evaluated} cards evaluated
        </p>
      </header>

      <main className="mx-auto max-w-5xl px-4 py-8 sm:px-8">

        {/* Card comparison grid */}
        <div className="mb-10 grid grid-cols-1 gap-6 sm:grid-cols-2">
          {top_cards.map((card, i) => (
            <CardResultCard
              key={card.card_id}
              card={card}
              rank={(i + 1) as 1 | 2}
            />
          ))}
        </div>

        {/* Spending breakdown chart */}
        <section className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
          <SpendingPieChart survey={survey} />
        </section>

        {/* Disclaimer + actions */}
        <div className="mt-8 space-y-4 text-center">
          <p className="text-xs text-gray-400">
            WalletAce provides informational recommendations only, not financial advice or
            credit approvals. Rates and bonuses are subject to change — verify with the
            issuer before applying.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <button
              onClick={() => navigate('/survey', { state: null, replace: true })}
              className="rounded-xl border-2 border-gray-200 bg-white px-5 py-2.5 text-sm
                         font-semibold text-gray-600 transition hover:border-gray-300
                         focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            >
              Retake Survey
            </button>
            <button
              onClick={() => navigate('/')}
              className="rounded-xl border-2 border-gray-200 bg-white px-5 py-2.5 text-sm
                         font-semibold text-gray-600 transition hover:border-gray-300
                         focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
            >
              ← Home
            </button>
          </div>

          <p className="text-xs text-gray-300">Session: {session_id}</p>
        </div>
      </main>
    </div>
  )
}
