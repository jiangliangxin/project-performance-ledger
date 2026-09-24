export interface User {
  id: string
  username: string
  email?: string | null
  display_name: string
  role: 'admin' | 'member'
  status: 'active' | 'disabled'
  created_at: string
  last_login_at?: string | null
}

export interface ProjectTypeRule {
  id: string
  project_type_id: string
  version_no: number
  standard_performance_yuan: number
  default_ratio_percent: number | null
  publicity_required: boolean
  collection_stage: 'none' | 'advance' | 'full' | 'advance_and_full'
  payout_pattern: 'single' | 'after_advance' | 'advance_then_full' | 'manual'
  effective_from: string
  effective_to?: string | null
  is_active: boolean
  source_note?: string | null
}

export interface ProjectType {
  id: string
  name: string
  status: string
  rules: ProjectTypeRule[]
}

export interface Payout {
  id: string
  cooperation_record_id: string
  batch_type: string
  amount_yuan: number
  received_date: string
  note?: string | null
  is_void: boolean
}

export interface RecordItem {
  id: string
  owner_id: string
  company_name: string
  project_type_id: string
  project_type_name: string
  record_date: string
  work_status: string
  completion_date?: string | null
  publicity_status: string
  publicity_date?: string | null
  advance_received_date?: string | null
  full_received_date?: string | null
  participation_mode: string
  my_ratio_percent: number | null
  standard_performance_yuan: number | null
  override_standard_yuan: number | null
  manual_due_amount_yuan: number | null
  my_due_amount_yuan: number | null
  paid_total_yuan: number
  outstanding_yuan: number | null
  current_status: string
  current_status_label: string
  snapshot_publicity_required: boolean
  snapshot_collection_stage: string
  snapshot_payout_pattern: string
  note?: string | null
  override_reason?: string | null
  archived_at?: string | null
  payouts: Payout[]
}

export interface PerformanceChange {
  id: string
  field_name: string
  old_value: string | null
  new_value: string | null
  reason: string
  created_at: string
}

export interface DashboardSummary {
  project_count: number
  in_progress_count: number
  completed_count: number
  paid_total_cents: number
  due_total_cents: number
  outstanding_total_cents: number
  unknown_due_count: number
  status_counts: Record<string, number>
}

export interface ImportRow {
  row_number: number
  company_name: string
  project_type_name: string
  record_date?: string | null
  standard_performance_yuan?: number | null
  my_ratio_percent?: number | null
  matched_project_type_id?: string | null
  errors: string[]
  warnings: string[]
}

export interface ImportPreview {
  source_type: string
  delimiter: string
  has_header: boolean
  rows: ImportRow[]
  valid_count: number
  warning_count: number
  error_count: number
}
