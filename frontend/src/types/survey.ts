/** Internal survey state — camelCase for React, converted to snake_case for API. */
export interface SurveyState {
  // Intro
  userName: string

  // Group 1 — Eligibility & Financial Health
  ficoTier: string
  annualIncome: number
  employmentStatus: string
  monthlyHousing: number
  recentInquiries6m: number
  carriesBalance: boolean

  // Group 2 — Monthly Spending Habits
  monthlyGroceries: number
  monthlyDining: number
  monthlyGas: number
  monthlyTravel: number
  monthlyTransit: number
  monthlyStreaming: number
  monthlyOnlineRetail: number
  monthlyUtilities: number

  // Group 3 — Lifestyle & Preferences
  hasBusinessSpend: boolean
  willingToPayFee: boolean
  maxAnnualFee: number          // 0 = no limit; only relevant when willingToPayFee=true
  rewardType: string
  airlinePreference: string
  hotelPreference: string
  needsIntroAPR: boolean
}

export const defaultSurvey: SurveyState = {
  userName: '',
  ficoTier: '',
  annualIncome: 0,
  employmentStatus: '',
  monthlyHousing: 0,
  recentInquiries6m: 0,
  carriesBalance: false,
  monthlyGroceries: 0,
  monthlyDining: 0,
  monthlyGas: 0,
  monthlyTravel: 0,
  monthlyTransit: 0,
  monthlyStreaming: 0,
  monthlyOnlineRetail: 0,
  monthlyUtilities: 0,
  hasBusinessSpend: false,
  willingToPayFee: true,
  maxAnnualFee: 0,
  rewardType: '',
  airlinePreference: 'none',
  hotelPreference: 'none',
  needsIntroAPR: false,
}
