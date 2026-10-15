export interface ParseErrorItem {
  id: string
  evidence_file_id: string
  case_id: string
  line_number: number
  raw_line: string
  reason: string
  parser_name: string
  created_at: string
  evidence_filename: string
}

export interface ParsingGapItem {
  id: string
  evidence_file_id: string
  gap_start_line: number | null
  gap_end_line: number | null
  description: string
  created_at: string
  evidence_filename: string
}

export interface ParseIssuesResponse {
  parse_errors: ParseErrorItem[]
  parsing_gaps: ParsingGapItem[]
}
