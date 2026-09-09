export interface Activity {
    id: string;
    project_id: string;
    activity_code: string;
    activity_name: string;
    wbs_level: string | null;
    discipline: string | null;
    area: string | null;
    planned_start: string | null;
    planned_finish: string | null;
    actual_start: string | null;
    actual_finish: string | null;
    planned_progress: number | null;
    actual_progress: number | null;
    status: string;
  }
  
  export interface ActivitiesResponse {
    count: number;
    activities: Activity[];
  }