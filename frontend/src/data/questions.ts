import { SurveyState } from '../types/survey'

export type InputType = 'radio' | 'slider' | 'toggle' | 'text'
export type SliderFormat = 'dollar' | 'count'

export interface RadioOption {
  value: string | number
  label: string
}

export interface QuestionDef {
  id: keyof SurveyState
  group: 1 | 2 | 3
  groupLabel: string
  title: string
  subtitle: string
  type: InputType
  // Radio
  options?: RadioOption[]
  // Slider
  min?: number
  max?: number
  step?: number
  format?: SliderFormat
  // Conditional display
  showIf?: (survey: SurveyState) => boolean
}

export const QUESTIONS: QuestionDef[] = [
  // ── Intro ────────────────────────────────────────────────────────────────

  {
    id: 'userName',
    group: 1,
    groupLabel: 'Welcome',
    title: 'What is your name?',
    subtitle: 'We\'ll personalise your recommendations.',
    type: 'text',
  },

  // ── Group 1: Eligibility & Financial Health ──────────────────────────────

  {
    id: 'ficoTier',
    group: 1,
    groupLabel: 'Eligibility',
    title: 'What is your estimated credit score?',
    subtitle: 'This ensures we only show cards you can realistically get.',
    type: 'radio',
    options: [
      { value: 'lt580',    label: 'Below 580 (Poor)'        },
      { value: '580_669',  label: '580 – 669 (Fair)'        },
      { value: '670_739',  label: '670 – 739 (Good)'        },
      { value: '740_799',  label: '740 – 799 (Very Good)'   },
      { value: '800_850',  label: '800 – 850 (Exceptional)' },
    ],
  },
  {
    id: 'annualIncome',
    group: 1,
    groupLabel: 'Eligibility',
    title: 'What is your approximate pretax annual household income?',
    subtitle: 'Some premium cards have income requirements.',
    type: 'radio',
    options: [
      { value: 25000,  label: 'Under $40,000'          },
      { value: 57000,  label: '$40,001 – $75,000'       },
      { value: 100000, label: '$75,001 – $125,000'      },
      { value: 187000, label: '$125,001 – $250,000'     },
      { value: 300000, label: '$250,001 or more'        },
    ],
  },
  {
    id: 'employmentStatus',
    group: 1,
    groupLabel: 'Eligibility',
    title: 'What is your current employment status?',
    subtitle: 'Issuers consider income stability when evaluating applications.',
    type: 'radio',
    options: [
      { value: 'employed',      label: 'Employed'      },
      { value: 'self_employed', label: 'Self-employed'  },
      { value: 'student',       label: 'Student'        },
      { value: 'unemployed',    label: 'Unemployed'     },
    ],
  },
  {
    id: 'monthlyHousing',
    group: 1,
    groupLabel: 'Eligibility',
    title: 'What is your monthly rent or mortgage payment?',
    subtitle: 'Used to assess your overall financial obligations.',
    type: 'slider',
    min: 0,
    max: 10000,
    step: 50,
    format: 'dollar',
  },
  {
    id: 'recentInquiries6m',
    group: 1,
    groupLabel: 'Eligibility',
    title: 'How many credit cards have you applied for in the last 6 months?',
    subtitle: "Chase's 5/24 rule blocks approvals if you've opened 5+ cards recently.",
    type: 'slider',
    min: 0,
    max: 10,
    step: 1,
    format: 'count',
  },
  {
    id: 'carriesBalance',
    group: 1,
    groupLabel: 'Eligibility',
    title: 'Do you typically carry a balance month to month?',
    subtitle: 'If yes, APR becomes the top priority — rewards rarely outweigh 22%+ interest.',
    type: 'toggle',
  },

  // ── Group 2: Monthly Spending Habits ─────────────────────────────────────

  {
    id: 'monthlyGroceries',
    group: 2,
    groupLabel: 'Spending',
    title: 'How much do you spend on groceries each month?',
    subtitle: 'Supermarkets and grocery stores.',
    type: 'slider',
    min: 0,
    max: 2000,
    step: 25,
    format: 'dollar',
  },
  {
    id: 'monthlyDining',
    group: 2,
    groupLabel: 'Spending',
    title: 'How much do you spend on dining out each month?',
    subtitle: 'Restaurants, takeout, cafés, and bars.',
    type: 'slider',
    min: 0,
    max: 3000,
    step: 25,
    format: 'dollar',
  },
  {
    id: 'monthlyGas',
    group: 2,
    groupLabel: 'Spending',
    title: 'How much do you spend on gas or EV charging each month?',
    subtitle: 'Fuel stations and EV charging networks.',
    type: 'slider',
    min: 0,
    max: 1000,
    step: 10,
    format: 'dollar',
  },
  {
    id: 'monthlyTravel',
    group: 2,
    groupLabel: 'Spending',
    title: 'How much do you spend on flights and hotels each month?',
    subtitle: 'Averaged across the year including holiday trips.',
    type: 'slider',
    min: 0,
    max: 5000,
    step: 50,
    format: 'dollar',
  },
  {
    id: 'monthlyTransit',
    group: 2,
    groupLabel: 'Spending',
    title: 'How much do you spend on rideshare and transit each month?',
    subtitle: 'Uber, Lyft, tolls, trains, and public transport.',
    type: 'slider',
    min: 0,
    max: 1000,
    step: 10,
    format: 'dollar',
  },
  {
    id: 'monthlyStreaming',
    group: 2,
    groupLabel: 'Spending',
    title: 'How much do you spend on streaming and digital subscriptions?',
    subtitle: 'Netflix, Spotify, Hulu, Apple TV+, and similar services.',
    type: 'slider',
    min: 0,
    max: 500,
    step: 5,
    format: 'dollar',
  },
  {
    id: 'monthlyOnlineRetail',
    group: 2,
    groupLabel: 'Spending',
    title: 'How much do you spend on online shopping each month?',
    subtitle: 'Amazon, eBay, and other online marketplaces.',
    type: 'slider',
    min: 0,
    max: 2000,
    step: 25,
    format: 'dollar',
  },
  {
    id: 'monthlyUtilities',
    group: 2,
    groupLabel: 'Spending',
    title: 'How much do you spend on utilities each month?',
    subtitle: 'Phone, internet, electricity, and other utility bills.',
    type: 'slider',
    min: 0,
    max: 1000,
    step: 10,
    format: 'dollar',
  },

  // ── Group 3: Lifestyle & Preferences ─────────────────────────────────────

  {
    id: 'hasBusinessSpend',
    group: 3,
    groupLabel: 'Preferences',
    title: 'Do you have significant business-related expenses?',
    subtitle: 'Some cards offer elevated rewards on office supplies, advertising, and software.',
    type: 'toggle',
  },
  {
    id: 'willingToPayFee',
    group: 3,
    groupLabel: 'Preferences',
    title: 'Are you willing to pay an annual fee?',
    subtitle: "Premium cards often earn more than they cost — we'll show you the math.",
    type: 'toggle',
  },
  {
    id: 'maxAnnualFee',
    group: 3,
    groupLabel: 'Preferences',
    title: 'How much annual fee are you willing to pay?',
    subtitle: 'We will only recommend cards at or below this amount.',
    type: 'slider',
    min: 0,
    max: 1000,
    step: 5,
    format: 'dollar',
    showIf: (survey) => survey.willingToPayFee === true,
  },
  {
    id: 'rewardType',
    group: 3,
    groupLabel: 'Preferences',
    title: 'Do you prefer cash back or travel rewards?',
    subtitle: 'Travel points can be worth 1.5–2× cash back when redeemed well.',
    type: 'radio',
    options: [
      { value: 'cash_back', label: 'Cash Back'     },
      { value: 'points',    label: 'Travel Points' },
      { value: 'miles',     label: 'Airline Miles' },
    ],
  },
  {
    id: 'airlinePreference',
    group: 3,
    groupLabel: 'Preferences',
    title: 'Do you fly primarily with one airline?',
    subtitle: 'Co-branded cards earn bonus miles and unlock elite-like perks.',
    type: 'radio',
    options: [
      { value: 'delta',     label: 'Delta'          },
      { value: 'united',    label: 'United'         },
      { value: 'aa',        label: 'American'       },
      { value: 'southwest', label: 'Southwest'      },
      { value: 'alaska',    label: 'Alaska Airlines' },
      { value: 'jetblue',   label: 'JetBlue'        },
      { value: 'none',      label: 'No preference'  },
    ],
  },
  {
    id: 'hotelPreference',
    group: 3,
    groupLabel: 'Preferences',
    title: 'Do you stay primarily with one hotel chain?',
    subtitle: 'Co-branded hotel cards offer free nights and status perks.',
    type: 'radio',
    options: [
      { value: 'marriott', label: 'Marriott' },
      { value: 'hilton',   label: 'Hilton'   },
      { value: 'hyatt',    label: 'Hyatt'    },
      { value: 'ihg',      label: 'IHG'      },
      { value: 'none',     label: 'No preference' },
    ],
  },
  {
    id: 'needsIntroAPR',
    group: 3,
    groupLabel: 'Preferences',
    title: 'Is your primary goal a 0% intro APR or balance transfer?',
    subtitle: 'A 0% intro period can save hundreds in interest while you pay down debt.',
    type: 'toggle',
  },
]

export const TOTAL_QUESTIONS = QUESTIONS.length  // 20
