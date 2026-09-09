import { apiGet } from "./api";
import type { AuditTrailResponse } from "../types/auditTrail";

export interface AuditTrailFilters {
  action?: string;
  entityType?: string;
  search?: string;
  page?: number;
  pageSize?: number;
}

export function getProjectAuditTrail(
  projectId: string,
  filters: AuditTrailFilters = {},
) {
  const params = new URLSearchParams();

  if (filters.action) params.set("action", filters.action);
  if (filters.entityType) params.set("entity_type", filters.entityType);
  if (filters.search) params.set("search", filters.search);

  params.set("page", String(filters.page ?? 1));
  params.set("page_size", String(filters.pageSize ?? 25));

  return apiGet<AuditTrailResponse>(
    `/audit-trail/project/${projectId}?${params.toString()}`,
  );
}
