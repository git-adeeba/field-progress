export type ExceptionSeverity =
  | "critical"
  | "high"
  | "medium"
  | "low";


export type ExceptionType =
  | "AHEAD_OF_PLAN"
  | "BEHIND_PLAN"
  | "BLOCKED_ACTIVITY"
  | "MISSING_UPDATE"
  | "UNPLANNED_WORK"
  | "SEQUENCE_DEVIATION"
  | "PROGRESS_STAGNATION"
  | "REWORK";


export type ExceptionStatus =
  | "open"
  | "resolved";


export interface ProjectException {
  id: string;

  project_id: string;

  activity_id:
    string | null;

  source_field_event_id:
    string | null;

  exception_type:
    ExceptionType;

  severity:
    ExceptionSeverity;

  title: string;

  description:
    string | null;

  planned_progress:
    number | null;

  actual_progress:
    number | null;

  variance:
    number | null;

  fingerprint: string;

  status:
    ExceptionStatus;

  detected_at: string;

  updated_at: string;

  resolved_at:
    string | null;

  resolution_note:
    string | null;
}


export interface ExceptionSummary {
  total: number;

  open: number;

  resolved: number;

  severity_counts: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };

  type_counts:
    Record<string, number>;
}


export interface ExceptionPagination {
  page: number;

  page_size: number;

  filtered_total: number;

  total_pages: number;

  has_previous: boolean;

  has_next: boolean;
}


export interface ProjectExceptionsResponse {
  project: {
    id: string;
    name: string;
    status: string;
  };

  summary:
    ExceptionSummary;

  pagination:
    ExceptionPagination;

  exceptions:
    ProjectException[];
}


export interface ResolveExceptionResponse {
  message: string;

  exception:
    ProjectException | null;
}