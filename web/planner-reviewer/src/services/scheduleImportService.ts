import {
  apiPost,
  apiPostFormData,
} from "./api";

import type {
  ScheduleImportResponse,
  SchedulePreviewResponse,
} from "../types/scheduleImport";


export interface ClearScheduleResponse {
  success: boolean;

  project: {
    id: string;
    name: string;
    start_date: string | null;
    end_date: string | null;
    status: string;
  };

  summary: {
    activities_deleted: number;
    dependencies_deleted: number;
  };
}


function buildScheduleFormData(
  projectId: string,
  file: File
): FormData {
  const formData = new FormData();

  formData.append(
    "project_id",
    projectId
  );

  formData.append(
    "file",
    file
  );

  return formData;
}


export function previewScheduleImport(
  projectId: string,
  file: File
) {
  return apiPostFormData<
    SchedulePreviewResponse
  >(
    "/schedule-import/preview",
    buildScheduleFormData(
      projectId,
      file
    )
  );
}


export function confirmScheduleImport(
  projectId: string,
  file: File
) {
  return apiPostFormData<
    ScheduleImportResponse
  >(
    "/schedule-import/confirm",
    buildScheduleFormData(
      projectId,
      file
    )
  );
}


export function clearProjectSchedule(
  projectId: string
) {
  return apiPost<
    ClearScheduleResponse
  >(
    "/schedule-import/clear",
    {
      project_id: projectId,
    }
  );
}
