export interface TimelineRecord {
  id: string
  case_id: string
  evidence_file_id: string
  line_number: number
  raw_line: string
  event_time_utc: string
  original_timezone: string
  source_ip: string | null
  user_or_actor: string | null
  event_type: string
  message: string
  severity: string
  extra: Record<string, unknown> | null
  evidence_filename: string
  evidence_sha256: string
  near_parse_gap: boolean
}

export interface TimelineResponse {
  total: number
  limit: number
  offset: number
  records: TimelineRecord[]
}

export interface TimelineFilters {
  q?: string
  start_time?: string
  end_time?: string
  event_type?: string
  severity?: string
  source?: string
  sort?: string
  order?: 'asc' | 'desc'
  limit?: number
  offset?: number
}
