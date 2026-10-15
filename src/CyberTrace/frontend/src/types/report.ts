export interface Report {
  id: string
  case_id: string
  format: 'json' | 'csv' | 'pdf'
  generated_by: string | null
  generated_at: string
}
