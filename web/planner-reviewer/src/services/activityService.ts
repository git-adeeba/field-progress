import { apiGet } from "./api";
import type { ActivitiesResponse } from "../types/activity";

export function getProjectActivities(projectId: string) {
  return apiGet<ActivitiesResponse>(
    `/projects/${encodeURIComponent(projectId)}/activities`
  );
}