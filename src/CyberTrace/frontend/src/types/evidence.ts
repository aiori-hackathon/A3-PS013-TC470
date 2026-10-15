export interface EvidenceFile {
  id: string
  case_id: string
  original_filename: string
  detected_format: string
  declared_format: string | null
  sha256_hash: string
  byte_size: number
  uploaded_by: string | null
  uploaded_at: string
  source_timezone_assumption: string
  notes: string | null
}

export interface EvidenceUploadResult {
  evidence: EvidenceFile
  records_parsed: number
  records_failed: number
  gaps_detected: number
  // automated_seconds is a real measurement of the parse+ingest stage.
  // manual_estimate_seconds is a labeled assumption (lines x a fixed
  // seconds-per-line constant) -- never presented as a measured fact.
  automated_seconds: number
  manual_estimate_seconds: number
}

export interface EvidenceVerifyResult {
  evidence_id: string
  verified: boolean
  recorded_sha256: string
  recomputed_sha256: string | null
  error: string | null
  checked_at: string
}
