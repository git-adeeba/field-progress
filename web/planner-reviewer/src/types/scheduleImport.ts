export interface ScheduleImportProject {
    id: string;
    name: string;
    start_date: string | null;
    end_date: string | null;
    status: string;
  }
  
  
  export interface ScheduleImportActivity {
    activity_code: string;
    activity_name: string;
  
    wbs_level: string | null;
    discipline: string | null;
    area: string | null;
  
    planned_start: string | null;
    planned_finish: string | null;
  
    planned_progress: number;
    planned_quantity: number | null;
    quantity_unit: string | null;
  
    source_row: number | null;
  }
  
  
  export interface ScheduleImportDependency {
    successor_code: string;
    predecessor_code: string;
    dependency_type: string;
    lag_days: number;
    source_row: number | null;
  }
  
  
  export interface ScheduleImportIssue {
    row: number | null;
    field: string;
    message: string;
  }
  
  
  export interface SchedulePreviewSummary {
    source_rows: number;
    activities: number;
    new_activities: number;
    existing_activities: number;
    dependencies: number;
    errors: number;
    warnings: number;
  }
  
  
  export interface SchedulePreviewResponse {
    project: ScheduleImportProject;
  
    filename: string;
    valid: boolean;
  
    summary: SchedulePreviewSummary;
  
    activities_preview:
      ScheduleImportActivity[];
  
    dependencies_preview:
      ScheduleImportDependency[];
  
    errors: ScheduleImportIssue[];
    warnings: ScheduleImportIssue[];
  }
  
  
  export interface ScheduleImportSummary {
    activities_in_file: number;
    activities_inserted: number;
    activities_skipped_existing: number;
  
    dependencies_in_file: number;
    dependencies_inserted: number;
    dependencies_skipped_existing: number;
    dependencies_unresolved: number;
  }
  
  
  export interface ScheduleImportResponse {
    success: boolean;
  
    project: ScheduleImportProject;
  
    filename: string;
  
    summary: ScheduleImportSummary;
  
    warnings: ScheduleImportIssue[];
  
    unresolved_dependencies:
      ScheduleImportDependency[];
  }