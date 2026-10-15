export interface HealthStatus {
  status: string
  app_name: string
  environment: string
  db_connected: boolean
  db_error: string | null
}
