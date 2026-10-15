import type { Case } from './case'

export interface ScenarioInfo {
  key: string
  name: string
  description: string
}

export interface ScenarioLoadResult {
  case: Case
  records_parsed: number
  records_failed: number
  gaps_detected: number
}
