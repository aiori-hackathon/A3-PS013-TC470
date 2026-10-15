export interface Case {
  id: string
  name: string
  description: string | null
  is_synthetic: boolean
  scenario_key: string | null
  created_by: string | null
  created_at: string
}

export interface CaseDetail extends Case {
  evidence_count: number
  log_record_count: number
  parse_error_count: number
}
