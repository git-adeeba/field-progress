export interface AuditActor {
    id: string;
    full_name: string | null;
    email: string | null;
    role: string | null;
  }
  
  export interface AuditActivity {
    id: string;
    activity_code: string | null;
    activity_name: string | null;
  }
  
  export interface AuditLog {
    id: string;
    project_id: string | null;
    user_id: string | null;
    action: string;
    entity_type: string;
    entity_id: string;
    old_value: Record<string, unknown> | null;
    new_value: Record<string, unknown> | null;
    created_at: string;
    actor: AuditActor | null;
    activity: AuditActivity | null;
  }
  
  export interface AuditTrailResponse {
    project: { id: string; name: string; status: string };
    summary: {
      total_events: number;
      action_counts: Record<string, number>;
    };
    pagination: {
      page: number;
      page_size: number;
      filtered_total: number;
      total_pages: number;
      has_previous: boolean;
      has_next: boolean;
    };
    audit_logs: AuditLog[];
  }
  