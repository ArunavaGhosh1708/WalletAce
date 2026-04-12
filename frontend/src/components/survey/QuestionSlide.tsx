import { QuestionDef } from '../../data/questions'
import { SurveyState } from '../../types/survey'
import RadioInput from './inputs/RadioInput'
import SliderInput from './inputs/SliderInput'
import TextInput from './inputs/TextInput'
import ToggleInput from './inputs/ToggleInput'

interface Props {
  question: QuestionDef
  value: SurveyState[keyof SurveyState]
  onChange: (value: SurveyState[keyof SurveyState]) => void
  visible: boolean
}

export default function QuestionSlide({ question, value, onChange, visible }: Props) {
  return (
    <div
      className={[
        'transition-opacity duration-200 ease-in-out',
        visible ? 'opacity-100 animate-fade-in' : 'opacity-0 pointer-events-none',
      ].join(' ')}
    >
      {/* Group badge */}
      <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-brand-500">
        {question.groupLabel}
      </p>

      {/* Question title */}
      <h2 className="mb-1 text-xl font-bold text-gray-900 sm:text-2xl">
        {question.title}
      </h2>

      {/* Subtitle / hint */}
      <p className="mb-8 text-sm text-gray-500">{question.subtitle}</p>

      {/* Input */}
      {question.type === 'radio' && question.options && (
        <RadioInput
          options={question.options}
          value={value as string | number}
          onChange={onChange as (v: string | number) => void}
        />
      )}

      {question.type === 'slider' &&
        question.min !== undefined &&
        question.max !== undefined &&
        question.step !== undefined &&
        question.format && (
          <SliderInput
            value={value as number}
            min={question.min}
            max={question.max}
            step={question.step}
            format={question.format}
            onChange={onChange as (v: number) => void}
          />
        )}

      {question.type === 'toggle' && (
        <ToggleInput
          value={value as boolean}
          onChange={onChange as (v: boolean) => void}
        />
      )}

      {question.type === 'text' && (
        <TextInput
          value={value as string}
          onChange={onChange as (v: string) => void}
        />
      )}
    </div>
  )
}
