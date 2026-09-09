import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  ArrowRight,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  CircleDot,
  MapPin,
  RefreshCw,
  Sparkles,
  Tag,
  X,
} from "lucide-react";

import {
  approveMatch,
  getReviewQueue,
  rejectMatch,
} from "../services/reviewService";

import type {
  ReviewQueueItem,
  ReviewMatch,
} from "../types/review";

import {
  useSearchParams,
} from "react-router-dom";

function confidenceLabel(
  confidence: number
) {
  if (confidence >= 75) {
    return "High confidence";
  }

  if (confidence >= 50) {
    return "Medium confidence";
  }

  return "Needs review";
}

function confidenceClass(
  confidence: number
) {
  if (confidence >= 75) {
    return "high";
  }

  if (confidence >= 50) {
    return "medium";
  }

  return "low";
}

function MatchCandidate({
  match,
  rank,
  processing,
  onApprove,
  onReject,
  compact = false,
}: {
  match: ReviewMatch;
  rank: number;
  processing: boolean;
  onApprove: () => void;
  onReject: () => void;
  compact?: boolean;
}) {
  const activity = match.activity;

  return (
    <article
      className={`review-v1-candidate ${
        compact
          ? "review-v1-candidate-compact"
          : ""
      }`}
    >
      <div className="review-v1-candidate-head">
        <div>
          <span className="review-v1-rank">
            #{rank}
          </span>

          <span className="review-v1-code">
            {activity?.activity_code ||
              "No code"}
          </span>
        </div>

        <span
          className={`review-v1-confidence-pill ${confidenceClass(
            match.confidence
          )}`}
        >
          {Math.round(
            match.confidence
          )}
          %
        </span>
      </div>

      <h3>
        {activity?.activity_name ||
          "Unknown activity"}
      </h3>

      <div className="review-v1-activity-meta">
        {activity?.discipline && (
          <span>
            <Tag size={12} />
            {activity.discipline}
          </span>
        )}

        {activity?.area && (
          <span>
            <MapPin size={12} />
            {activity.area}
          </span>
        )}
      </div>

      {!compact && (
        <>
          <div className="review-v1-score-bars">
            <div>
              <header>
                <span>
                  Text similarity
                </span>

                <strong>
                  {Math.round(
                    match.semantic_score ||
                      0
                  )}
                  %
                </strong>
              </header>

              <div>
                <i
                  style={{
                    width: `${Math.min(
                      Math.max(
                        match.semantic_score ||
                          0,
                        0
                      ),
                      100
                    )}%`,
                  }}
                />
              </div>
            </div>

            <div>
              <header>
                <span>
                  Context score
                </span>

                <strong>
                  {Math.round(
                    match.context_score ||
                      0
                  )}
                  %
                </strong>
              </header>

              <div>
                <i
                  style={{
                    width: `${Math.min(
                      Math.max(
                        match.context_score ||
                          0,
                        0
                      ),
                      100
                    )}%`,
                  }}
                />
              </div>
            </div>
          </div>

          {match.reason && (
            <div className="review-v1-reason">
              <Sparkles size={14} />

              <span>
                {match.reason}
              </span>
            </div>
          )}

          <div className="review-v1-actions">
            <button
              className="review-v1-approve"
              disabled={processing}
              onClick={onApprove}
            >
              <Check size={15} />

              {processing
                ? "Processing..."
                : "Approve match"}
            </button>

            <button
              className="review-v1-reject"
              disabled={processing}
              onClick={onReject}
            >
              <X size={15} />
              Reject
            </button>
          </div>
        </>
      )}
    </article>
  );
}

function QueueItem({
  item,
  refresh,
}: {
  item: ReviewQueueItem;
  refresh: () => Promise<void>;
}) {
  const [expanded, setExpanded] =
    useState(false);

  const [processingId, setProcessingId] =
    useState<string | null>(null);

  const event = item.field_event;

  const topMatch = item.matches[0];

  const alternatives =
    item.matches.slice(1);

  async function handleApprove(
    matchId: string
  ) {
    try {
      setProcessingId(matchId);

      await approveMatch(matchId);

      await refresh();
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : "Approval failed"
      );
    } finally {
      setProcessingId(null);
    }
  }

  async function handleReject(
    matchId: string
  ) {
    try {
      setProcessingId(matchId);

      await rejectMatch(matchId);

      await refresh();
    } catch (error) {
      alert(
        error instanceof Error
          ? error.message
          : "Rejection failed"
      );
    } finally {
      setProcessingId(null);
    }
  }

  return (
    <section className="review-v1-workspace">
      <div className="review-v1-flow-labels">
        <span>
          FIELD REALITY
        </span>

        <ArrowRight size={14} />

        <span>
          AI INTERPRETATION
        </span>

        <ArrowRight size={14} />

        <span>
          SCHEDULE
        </span>
      </div>

      <div className="review-v1-main-grid">
        <article className="review-v1-evidence-panel">
          <div className="review-v1-panel-heading">
            <div className="review-v1-panel-icon blue">
              <CircleDot size={17} />
            </div>

            <div>
              <span>
                FIELD EVIDENCE
              </span>

              <h3>
                Execution Update
              </h3>
            </div>
          </div>

          <div className="review-v1-source-row">
            <span>
              {event.source_type}
            </span>

            <span>
              {event.status}
            </span>
          </div>

          <div className="review-v1-evidence-text">
            “{event.raw_text}”
          </div>

          <div className="review-v1-context">
            <span>
              CONTEXT
            </span>

            {event.discipline && (
              <div>
                <Tag size={13} />

                <section>
                  <span>
                    Discipline
                  </span>

                  <strong>
                    {event.discipline}
                  </strong>
                </section>
              </div>
            )}

            {event.area && (
              <div>
                <MapPin size={13} />

                <section>
                  <span>
                    Area
                  </span>

                  <strong>
                    {event.area}
                  </strong>
                </section>
              </div>
            )}

            {event.quantity !== null &&
              event.quantity !==
                undefined && (
                <div>
                  <CircleDot
                    size={13}
                  />

                  <section>
                    <span>
                      Quantity
                    </span>

                    <strong>
                      {event.quantity}{" "}
                      {event.unit || ""}
                    </strong>
                  </section>
                </div>
              )}
          </div>
        </article>

        <article className="review-v1-ai-panel">
          <div className="review-v1-ai-heading">
            <div>
              <Sparkles size={18} />
            </div>

            <section>
              <span>
                AI MATCH ANALYSIS
              </span>

              <h3>
                Context-aware
                reconciliation
              </h3>
            </section>
          </div>

          {topMatch ? (
            <>
              <div className="review-v1-confidence">
                <div
                  className={`review-v1-confidence-ring ${confidenceClass(
                    topMatch.confidence
                  )}`}
                  style={{
                    ["--confidence" as string]:
                      `${Math.min(
                        Math.max(
                          topMatch.confidence,
                          0
                        ),
                        100
                      ) * 3.6}deg`,
                  }}
                >
                  <div>
                    <strong>
                      {Math.round(
                        topMatch.confidence
                      )}
                      %
                    </strong>

                    <span>
                      confidence
                    </span>
                  </div>
                </div>

                <div className="review-v1-confidence-copy">
                  <strong>
                    {confidenceLabel(
                      topMatch.confidence
                    )}
                  </strong>

                  <p>
                    Candidate ranked using
                    execution text and
                    contextual project
                    signals.
                  </p>
                </div>
              </div>

              <div className="review-v1-ai-signals">
                <div>
                  <CheckCircle2
                    size={14}
                  />

                  Field event interpreted
                </div>

                <div>
                  <CheckCircle2
                    size={14}
                  />

                  Schedule candidates
                  ranked
                </div>

                <div>
                  <CheckCircle2
                    size={14}
                  />

                  Context score evaluated
                </div>
              </div>
            </>
          ) : (
            <div className="review-v1-no-match">
              No suggested candidate.
            </div>
          )}
        </article>

        <article className="review-v1-schedule-panel">
          <div className="review-v1-panel-heading">
            <div className="review-v1-panel-icon violet">
              <CheckCircle2
                size={17}
              />
            </div>

            <div>
              <span>
                TOP SCHEDULE MATCH
              </span>

              <h3>
                Suggested activity
              </h3>
            </div>
          </div>

          {topMatch ? (
            <MatchCandidate
              match={topMatch}
              rank={1}
              processing={
                processingId ===
                topMatch.id
              }
              onApprove={() =>
                handleApprove(
                  topMatch.id
                )
              }
              onReject={() =>
                handleReject(
                  topMatch.id
                )
              }
            />
          ) : (
            <div className="review-v1-no-match">
              No activity candidate
              available.
            </div>
          )}
        </article>
      </div>

      {alternatives.length > 0 && (
        <div className="review-v1-alternatives">
          <button
            onClick={() =>
              setExpanded(
                (previous) =>
                  !previous
              )
            }
          >
            {expanded ? (
              <ChevronUp
                size={15}
              />
            ) : (
              <ChevronDown
                size={15}
              />
            )}

            {expanded
              ? "Hide alternatives"
              : `Show ${alternatives.length} alternative matches`}
          </button>

          {expanded && (
            <div className="review-v1-alternative-grid">
              {alternatives.map(
                (match, index) => (
                  <MatchCandidate
                    key={match.id}
                    match={match}
                    rank={index + 2}
                    processing={
                      processingId ===
                      match.id
                    }
                    onApprove={() =>
                      handleApprove(
                        match.id
                      )
                    }
                    onReject={() =>
                      handleReject(
                        match.id
                      )
                    }
                  />
                )
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}

export default function ReviewQueue() {
  const [
    searchParams,
  ] =
    useSearchParams();

  const requestedProjectId =
    searchParams.get(
      "project_id"
    );

  const [items, setItems] =
    useState<ReviewQueueItem[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const loadQueue =
    useCallback(async () => {
      try {
        setError(null);

        const response =
          await getReviewQueue();

        const queueItems =
          response.items || [];

        if (!requestedProjectId) {
          setItems(queueItems);
          return;
        }

        const projectItems =
          queueItems.filter(
            (item) => {
              const event =
                item.field_event as
                  typeof item.field_event & {
                    project_id?: string;
                  };

              return (
                event.project_id ===
                requestedProjectId
              );
            }
          );

        setItems(projectItems);
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Failed to load review queue"
        );
      } finally {
        setLoading(false);
      }
    }, [requestedProjectId]);

  useEffect(() => {
    loadQueue();
  }, [loadQueue]);

  return (
    <div className="review-v1-page">
      <div className="review-v1-page-heading">
        <div>
          <div className="review-v1-eyebrow">
            <Sparkles size={13} />
            AI-ASSISTED RECONCILIATION
          </div>

          <h2>
            Validate field reality
            before it becomes progress.
          </h2>

          <p>
            Every suggested match stays
            explainable and under planner
            control.
          </p>
        </div>

        <div className="review-v1-page-actions">
          <div>
            <span>Waiting for review</span>

            <strong>
              {items.length}
            </strong>
          </div>

          <button
            onClick={loadQueue}
          >
            <RefreshCw size={15} />
            Refresh
          </button>
        </div>
      </div>

      {loading && (
        <div className="review-v1-state">
          <div className="spinner" />

          <span>
            Loading review queue...
          </span>
        </div>
      )}

      {error && (
        <div className="review-v1-error">
          {error}
        </div>
      )}

      {!loading &&
        !error &&
        items.length === 0 && (
          <div className="review-v1-empty">
            <div>
              <Check
                size={27}
              />
            </div>

            <h2>
              Review queue is clear
            </h2>

            <p>
              There are currently no
              suggested activity matches
              waiting for planner review.
            </p>
          </div>
        )}

      <div className="review-v1-list">
        {items.map((item) => (
          <QueueItem
            key={
              item.field_event.id
            }
            item={item}
            refresh={loadQueue}
          />
        ))}
      </div>
    </div>
  );
}
