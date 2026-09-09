import {
    apiGet,
    apiPost,
  } from "./api";
  
  import type {
    ProjectExceptionsResponse,
    ResolveExceptionResponse,
  } from "../types/exception";
  
  
  export interface ExceptionFilters {
    status?: string;
  
    exceptionType?: string;
  
    severity?: string;
  
    search?: string;
  
    page?: number;
  
    pageSize?: number;
  }
  
  
  function buildQueryString(
    filters:
      ExceptionFilters = {}
  ) {
    const params =
      new URLSearchParams();
  
  
    if (filters.status) {
      params.set(
        "status",
        filters.status
      );
    }
  
  
    if (
      filters.exceptionType
    ) {
      params.set(
        "exception_type",
        filters.exceptionType
      );
    }
  
  
    if (filters.severity) {
      params.set(
        "severity",
        filters.severity
      );
    }
  
  
    if (
      filters.search &&
      filters.search.trim()
    ) {
      params.set(
        "search",
        filters.search.trim()
      );
    }
  
  
    params.set(
      "page",
      String(
        filters.page ?? 1
      )
    );
  
  
    params.set(
      "page_size",
      String(
        filters.pageSize ?? 25
      )
    );
  
  
    const query =
      params.toString();
  
  
    return query
      ? `?${query}`
      : "";
  }
  
  
  export async function getProjectExceptions(
    projectId: string,
    filters:
      ExceptionFilters = {}
  ): Promise<ProjectExceptionsResponse> {
  
    const query =
      buildQueryString(
        filters
      );
  
  
    return apiGet<ProjectExceptionsResponse>(
      `/exceptions/project/${projectId}${query}`
    );
  }
  
  
  export async function resolveException(
    exceptionId: string,
    resolutionNote: string
  ): Promise<ResolveExceptionResponse> {
  
    return apiPost<ResolveExceptionResponse>(
      `/exceptions/${exceptionId}/resolve`,
      {
        resolution_note:
          resolutionNote,
      }
    );
  }