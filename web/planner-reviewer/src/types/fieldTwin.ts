export type PlanState =
  | "ahead"
  | "on_track"
  | "behind"
  | "no_field_evidence";

export type FieldState =
  | "completed"
  | "in_progress"
  | "started"
  | "blocked"
  | "field_activity_detected"
  | "no_field_evidence"
  | "unverified";

export interface TwinExecutionEvent {
  id?: string;
  project_id?: string;
  activity_id?: string | null;
  field_event_id?: string | null;

  execution_type?: string;
  execution_name?: string;

  quantity?: number | null;
  unit?: string | null;

  progress_contribution?: number | null;

  occurred_at?: string;
  status?: string;

  created_at?: string;
}

export interface TwinActivity {
  activity_id: string;

  activity_code?: string | null;
  activity_name?: string | null;

  wbs_level?: number | string | null;

  discipline?: string | null;
  area?: string | null;

  planned_start?: string | null;
  planned_finish?: string | null;

  actual_start?: string | null;
  actual_finish?: string | null;

  planned_progress: number;
  actual_progress: number;

  progress_difference: number;

  schedule_status?: string | null;

  field_state: FieldState;
  plan_state: PlanState;

  has_field_evidence: boolean;

  execution_event_count: number;

  latest_execution_event:
    | TwinExecutionEvent
    | null;
}

export interface TwinSummary {
  total_activities: number;

  activities_with_field_evidence: number;

  completed_on_field: number;

  ahead: number;
  on_track: number;
  behind: number;

  no_field_evidence: number;

  average_planned_progress: number;
  average_actual_progress: number;
}

export interface TwinProject {
  id: string;
  name?: string | null;
  description?: string | null;
  status?: string | null;

  start_date?: string | null;
  end_date?: string | null;
}

export interface FieldTwinResponse {
  project: TwinProject;

  generated_at: string;

  summary: TwinSummary;

  activities: TwinActivity[];
}