import { apiGet } from "./api";

import type {
  FieldTwinResponse,
} from "../types/fieldTwin";


export function getFieldTwin(
  projectId: string
) {
  return apiGet<FieldTwinResponse>(
    `/field-twin/${encodeURIComponent(
      projectId
    )}`
  );
}