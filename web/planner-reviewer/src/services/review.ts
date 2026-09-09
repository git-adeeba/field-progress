export interface ReviewActivity {
    id: string;
    activity_code: string;
    activity_name: string;
  
    discipline?: string | null;
    area?: string | null;
  
    planned_start?: string | null;
    planned_finish?: string | null;
  
    actual_progress?: number | null;
    status?: string | null;
  }
  
  
  export interface ReviewMatch {
    id: string;
  
    field_event_id: string;
    activity_id: string;
  
    confidence: number;
    semantic_score?: number | null;
    context_score?: number | null;
  
    reason?: string | null;
    status?: string | null;
  
    activity?: ReviewActivity | null;
  }
  
  
  export interface ReviewFieldEvent {
    id: string;
    project_id: string;
  
    source_type: string;
    raw_text: string;
  
    event_date?: string | null;
    discipline?: string | null;
    area?: string | null;
  
    asset_reference?: string | null;
  
    quantity?: number | null;
    unit?: string | null;
  
    status: string;
    created_at: string;
  }
  
  
  export interface ReviewQueueItem {
    field_event: ReviewFieldEvent;
    matches: ReviewMatch[];
  }
  
  
  export interface ReviewQueueResponse {
    count: number;
    items: ReviewQueueItem[];
  }