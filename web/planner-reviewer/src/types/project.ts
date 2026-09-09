export interface Project {
    id: string;
    name: string;
    description: string | null;
    start_date: string | null;
    end_date: string | null;
    status: string;
    created_at: string;
  }
  
  export interface ProjectsResponse {
    count: number;
    projects: Project[];
  }