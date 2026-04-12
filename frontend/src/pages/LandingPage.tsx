import { useNavigate } from 'react-router-dom'

export default function LandingPage() {
  const navigate = useNavigate()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-br from-brand-600 to-brand-700 px-4 text-center">
      {/* Logo / wordmark */}
      <div className="mb-8">
        <h1 className="text-5xl font-extrabold tracking-tight text-white sm:text-6xl">
          WalletAce
        </h1>
        <p className="mt-2 text-lg font-medium text-brand-100">
          Credit Card Recommendation Engine
        </p>
      </div>

      {/* Value hook */}
      <div className="mb-10 max-w-lg rounded-2xl bg-white/10 px-8 py-6 backdrop-blur-sm">
        <p className="text-3xl font-bold text-white">
          You could earn <span className="text-yellow-300">$700 more/year</span>
        </p>
        <p className="mt-2 text-base text-brand-100">
          Most households leave hundreds on the table by not matching their
          spending habits to the right card. Answer a few quick questions —
          we'll do the math.
        </p>
      </div>

      {/* Trust signals */}
      <div className="mb-10 flex flex-wrap items-center justify-center gap-6 text-sm text-brand-100">
        <span className="flex items-center gap-1.5">
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
          </svg>
          50+ cards analysed
        </span>
        <span className="flex items-center gap-1.5">
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
          </svg>
          Under 3 minutes
        </span>
        <span className="flex items-center gap-1.5">
          <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
          </svg>
          No signup required
        </span>
      </div>

      {/* CTA */}
      <button
        onClick={() => navigate('/survey')}
        className="rounded-2xl bg-white px-10 py-4 text-lg font-bold text-brand-600
                   shadow-lg transition-all duration-150 hover:scale-105 hover:shadow-xl
                   active:scale-100 focus:outline-none focus-visible:ring-4
                   focus-visible:ring-white/50"
      >
        Find My Best Card →
      </button>

      <p className="mt-6 text-xs text-brand-200">
        Informational recommendations only. Not financial advice.
      </p>
    </div>
  )
}
