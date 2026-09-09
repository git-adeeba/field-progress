import { apiGet } from "./api";
import type { ProjectsResponse } from "../types/project";

export function getProjects() {
  return apiGet<ProjectsResponse>("/projects");
}