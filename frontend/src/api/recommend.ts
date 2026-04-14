import axios from 'axios'
import { SurveyState } from '../types/survey'

const BASE_URL = import.meta.env.VITE_API_URL ?? ''

export interface CategoryBreakdown {
  groceries: number
  dining: number
  gas: number
  travel: number
  transit: number
  streaming: number
  online_retail: number
  utilities: number
}

export interface CardResult {
  card_id: string
  issuer: string
  card_name: string
  annual_fee: number
  reward_type: string
  reward_network: string | null
  affiliate_link: string
  eanv: number
  rewards_total: number
  signup_bonus_value: number
  category_breakdown: CategoryBreakdown
  why_this_card: string
  has_lounge_access: boolean
  has_global_entry: boolean
  intro_apr_months: number
  ongoing_apr_min: number
  ongoing_apr_max: number
}

export interface RecommendationResponse {
  session_id: string
  year: number
  top_cards: CardResult[]
  cards_evaluated: number
}

/** Convert React camelCase survey state → snake_case API payload. */
function toApiPayload(survey: SurveyState) {
  return {
    user_name: survey.userName.trim() || null,
    fico_tier: survey.ficoTier,
    annual_income: survey.annualIncome,
    employment_status: survey.employmentStatus,
    monthly_housing: survey.monthlyHousing,
    recent_inquiries_6m: survey.recentInquiries6m,
    carries_balance: survey.carriesBalance,
    monthly_groceries: survey.monthlyGroceries,
    monthly_dining: survey.monthlyDining,
    monthly_gas: survey.monthlyGas,
    monthly_travel: survey.monthlyTravel,
    monthly_transit: survey.monthlyTransit,
    monthly_streaming: survey.monthlyStreaming,
    monthly_online_retail: survey.monthlyOnlineRetail,
    monthly_utilities: survey.monthlyUtilities,
    has_business_spend: survey.hasBusinessSpend,
    willing_to_pay_fee: survey.willingToPayFee,
    max_annual_fee: survey.willingToPayFee ? survey.maxAnnualFee : 0,
    // rewardType → prefers_cash_back: cash_back=true, points/miles=false
    prefers_cash_back: survey.rewardType === 'cash_back',
    airline_preference: survey.airlinePreference === 'none' ? null : survey.airlinePreference,
    hotel_preference: survey.hotelPreference === 'none' ? null : survey.hotelPreference,
    needs_intro_apr: survey.needsIntroAPR,
  }
}

export async function getRecommendations(
  survey: SurveyState,
  year: 1 | 2 = 1,
): Promise<RecommendationResponse> {
  const { data } = await axios.post<RecommendationResponse>(
    `${BASE_URL}/api/v1/recommend?year=${year}`,
    toApiPayload(survey),
    { headers: { 'Content-Type': 'application/json' } },
  )
  return data
}
