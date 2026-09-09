export interface ReviewActivity {
    id: string;
    activity_code: string;
    activity_name: string;
    discipline?: string | null;
    area?: string | null;
    status?: string | null;
    planned_progress?: number | null;
    actual_progress?: number | null;
  }
  
  export interface ReviewFieldEvent {
    id: string;
    project_id?: string;
    source_type: string;
    status: string;
    raw_text: string;
    discipline?: string | null;
    area?: string | null;
    quantity?: number | null;
    unit?: string | null;
  }
  
  export interface ReviewMatch {
    id: string;
    confidence: number;
    semantic_score?: number | null;
    context_score?: number | null;
    reason?: string | null;
    activity?: ReviewActivity | null;
  }
  
  export interface ReviewQueueItem {
    field_event: ReviewFieldEvent;
    matches: ReviewMatch[];
  }
  
  export interface ReviewQueueResponse {
    count?: number;
    items: ReviewQueueItem[];
  }