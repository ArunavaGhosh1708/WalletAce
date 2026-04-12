import { useState, useCallback, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import ProgressBar from '../components/survey/ProgressBar'
import QuestionSlide from '../components/survey/QuestionSlide'
import { QUESTIONS } from '../data/questions'
import { SurveyState, defaultSurvey } from '../types/survey'
import { getRecommendations } from '../api/recommend'

/** Returns true if the current question has a valid answer. */
function isAnswered(question: (typeof QUESTIONS)[number], survey: SurveyState): boolean {
  const value = survey[question.id]
  if (question.type === 'radio') {
    return value !== '' && value !== 0 && value !== null
  }
  if (question.type === 'text') {
    return typeof value === 'string' && value.trim().length > 0
  }
  // Sliders and toggles always have a value
  return true
}

export default function SurveyPage() {
  const navigate = useNavigate()
  const [survey, setSurvey] = useState<SurveyState>(defaultSurvey)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [visible, setVisible] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  // Reset to fresh state on every mount — prevents stale answers from a previous session
  useEffect(() => {
    setSurvey(defaultSurvey)
    setCurrentIndex(0)
    setError(null)
    setSubmitting(false)
  }, [])

  // Only show questions whose showIf condition is met
  const visibleQuestions = useMemo(
    () => QUESTIONS.filter((q) => !q.showIf || q.showIf(survey)),
    [survey],
  )

  const safeIndex = Math.min(currentIndex, visibleQuestions.length - 1)
  const question = visibleQuestions[safeIndex]
  const isLast = safeIndex === visibleQuestions.length - 1

  /** Crossfade to a new question index. */
  const goTo = useCallback((nextIndex: number) => {
    setVisible(false)
    setError(null)
    setTimeout(() => {
      setCurrentIndex(nextIndex)
      setVisible(true)
    }, 180)
  }, [])

  const handleChange = useCallback(
    (value: SurveyState[keyof SurveyState]) => {
      setSurvey((prev) => ({ ...prev, [question.id]: value }))
    },
    [question.id],
  )

  const handleNext = async () => {
    if (!isAnswered(question, survey)) {
      setError('Please select an answer before continuing.')
      return
    }

    if (isLast) {
      setSubmitting(true)
      try {
        const result = await getRecommendations(survey, 1)
        navigate('/results', { state: { result, survey }, replace: false })
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : 'Something went wrong. Please try again.'
        setError(message)
        setSubmitting(false)
      }
      return
    }

    goTo(safeIndex + 1)
  }

  const handleBack = () => {
    if (safeIndex > 0) goTo(safeIndex - 1)
  }

  return (
    <div className="flex min-h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="border-b border-gray-100 bg-white px-4 py-4 sm:px-8">
        <div className="mx-auto max-w-xl">
          <div className="mb-3 flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="text-sm font-semibold text-brand-600 hover:text-brand-700"
            >
              ← WalletAce
            </button>
            <span className="text-xs text-gray-400">
              Group {question.group} of 3 — {question.groupLabel}
            </span>
          </div>
          <ProgressBar current={safeIndex + 1} total={visibleQuestions.length} />
        </div>
      </header>

      {/* Question area */}
      <main className="flex flex-1 items-start justify-center px-4 py-10 sm:px-8">
        <div className="w-full max-w-xl">
          <QuestionSlide
            question={question}
            value={survey[question.id]}
            onChange={handleChange}
            visible={visible}
          />

          {/* Validation error */}
          {error && (
            <p className="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm font-medium text-red-600">
              {error}
            </p>
          )}
        </div>
      </main>

      {/* Navigation footer */}
      <footer className="border-t border-gray-100 bg-white px-4 py-4 sm:px-8">
        <div className="mx-auto flex max-w-xl items-center justify-between gap-3">
          <button
            onClick={handleBack}
            disabled={safeIndex === 0}
            className="rounded-xl border-2 border-gray-200 bg-white px-6 py-3 text-sm
                       font-semibold text-gray-600 transition-all hover:border-gray-300
                       disabled:cursor-not-allowed disabled:opacity-40
                       focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            ← Back
          </button>

          <button
            onClick={handleNext}
            disabled={submitting}
            className="flex-1 rounded-xl bg-brand-500 px-6 py-3 text-sm font-semibold
                       text-white shadow-sm transition-all hover:bg-brand-600 active:scale-95
                       disabled:cursor-not-allowed disabled:opacity-60
                       focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500"
          >
            {submitting ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
                </svg>
                Analysing…
              </span>
            ) : isLast ? (
              'Get My Recommendations →'
            ) : (
              'Next →'
            )}
          </button>
        </div>
      </footer>

      {/* Loading overlay */}
      {submitting && (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm">
          <svg className="mb-4 h-12 w-12 animate-spin text-brand-500" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"/>
          </svg>
          <p className="text-lg font-semibold text-gray-800">Analysing your spending…</p>
          <p className="mt-1 text-sm text-gray-500">Finding your best cards</p>
        </div>
      )}
    </div>
  )
}
