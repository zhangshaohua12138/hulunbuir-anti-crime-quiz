export type BlockType =
  | 'hero'
  | 'stats'
  | 'cta'
  | 'latest'
  | 'steps'
  | 'prizes'
  | 'notice'
  | 'features'
  | 'ranking'
  | 'custom-text'
  | 'custom-image'
  | 'custom-search'
  | 'custom-button'
  | 'custom-divider'
  | 'custom-carousel'
  | 'custom-banner'

export interface LayoutBlock {
  id: string
  type: BlockType
  visible: boolean
  props: Record<string, unknown>
}

export interface LayoutTemplate {
  id: string
  name: string
  layout: PageLayout
  createdAt?: number
}

export interface PageLayout {
  version: number
  blocks: LayoutBlock[]
}

export interface BootConfig {
  title: string
  organizer: string
  brandSubtitle?: string
  homeEyebrow?: string
  homeIntro?: string
  homeMeta?: string
  homeCardTitle?: string
  homeCta?: string
  homeGiftTitle?: string
  footerText?: string
  startAt: string
  endAt: string
  passScore: number
  winnerCount: number
  awardDescription?: string
  themeColor?: string
  pageBackground?: string
  cardBackground?: string
  headerBackground?: string
  textColor?: string
  mutedColor?: string
  borderColor?: string
  iconColor?: string
  buttonTextColor?: string
  buttonTextAuto?: boolean
  template?: string
  layout?: PageLayout
  copy?: Record<string, string>
  [key: string]: unknown
}

export interface BootAccount {
  freeRemaining: number
  reviveRemaining: number
  canRevive: boolean
  points: number
}

export interface Bootstrap {
  mode: string
  user: null | { id: string; nickname: string; avatar?: string; is_test?: number; rules?: number }
  config: BootConfig
  state: string
  account: BootAccount | null
  activeAttempt?: unknown
  latestResult?: unknown
  prizes?: Array<{ id: string; name: string; type: string; amountCents?: number }>
}

export interface AdminMe {
  username: string
  role: 'super' | 'operator'
}
export interface QuizOption {
  id: string
  text: string
}

export interface QuizQuestion {
  id: string
  type: 'single' | 'multiple'
  stem: string
  options: QuizOption[]
}

export interface Attempt {
  id: string
  questions: QuizQuestion[]
  answers: Record<string, string[]>
  deadlineAt: string
  status: 'active' | 'submitted' | 'expired'
  score: number
  passed: boolean
  revived?: boolean
  drawn?: boolean
  lottery?: unknown
}

export interface LotteryResult {
  won: boolean
  message: string
  order?: { id: string; status?: string; type?: string; amountCents?: number } | null
  prize?: { id: string; name: string; type?: string } | null
}
