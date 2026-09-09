import {
    apiGet,
    apiPost,
  } from "./api";
  
  import type {
    ReviewQueueResponse,
  } from "../types/review";
  
  
  export function getReviewQueue() {
    return apiGet<ReviewQueueResponse>(
      "/matches/review-queue"
    );
  }
  
  
  export function approveMatch(
    matchId: string
  ) {
    return apiPost(
      `/matches/${encodeURIComponent(matchId)}/approve`,
      {}
    );
  }
  
  
  export function rejectMatch(
    matchId: string
  ) {
    return apiPost(
      `/matches/${encodeURIComponent(matchId)}/reject`,
      {}
    );
  }