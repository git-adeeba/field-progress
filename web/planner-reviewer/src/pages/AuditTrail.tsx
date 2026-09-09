import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useSearchParams,
} from "react-router-dom";

import {
  getProjects,
} from "../services/projectService";

import {
  getProjectAuditTrail,
} from "../services/auditTrailService";

import type {
  Project,
} from "../types/project";

import type {
  AuditLog,
  AuditTrailResponse,
} from "../types/auditTrail";

import "../styles/audit-trail.css";


const PAGE_SIZE = 25;


function formatAction(
  action: string,
) {
  const labels: Record<
    string,
    string
  > = {
    activity_match_approved:
      "Activity Match Approved",

    activity_match_rejected:
      "Activity Match Rejected",

    activity_match_auto_verified:
      "Activity Auto-Verified",

    exception_resolved:
      "Exception Resolved",

    schedule_imported:
      "Schedule Imported",

    schedule_cleared:
      "Schedule Cleared",
  };

  return (
    labels[action]
    || action
      .replaceAll("_", " ")
      .replace(
        /\b\w/g,
        (character) =>
          character.toUpperCase(),
      )
  );
}


function formatEntityType(
  value: string,
) {
  return value
    .replaceAll("_", " ")
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}


function formatDateTime(
  value: string,
) {
  const date = new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "en-IN",
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(date);
}


function formatPercent(
  value: unknown,
) {
  const numberValue =
    Number(value);

  if (
    Number.isNaN(numberValue)
  ) {
    return null;
  }

  return `${numberValue.toFixed(0)}%`;
}


function stringifyValue(
  value: unknown,
) {
  if (
    value === null
    || value === undefined
  ) {
    return "—";
  }

  if (
    typeof value
    === "string"
  ) {
    return value;
  }

  if (
    typeof value
    === "number"
    || typeof value
      === "boolean"
  ) {
    return String(value);
  }

  try {
    return JSON.stringify(
      value,
      null,
      2,
    );
  } catch {
    return String(value);
  }
}


function getProgressChange(
  log: AuditLog,
) {
  const next = (
    log.new_value
    || {}
  ) as Record<
    string,
    unknown
  >;

  const progress = (
    next.physical_progress
    || null
  ) as Record<
    string,
    unknown
  > | null;

  if (!progress) {
    return null;
  }

  const previous =
    formatPercent(
      progress.previous_progress,
    );

  const current =
    formatPercent(
      progress.new_progress,
    );

  if (
    !previous
    || !current
  ) {
    return null;
  }

  return {
    previous,
    current,
    method:
      String(
        progress.method
        || "",
      ),
  };
}


function getPrimaryDetail(
  log: AuditLog,
) {
  const newValue = (
    log.new_value
    || {}
  ) as Record<
    string,
    unknown
  >;

  if (
    log.action
    === "schedule_imported"
  ) {
    const filename =
      String(
        newValue.filename
        || "Schedule file",
      );

    const summary = (
      newValue.summary
      || {}
    ) as Record<
      string,
      unknown
    >;

    return {
      title: filename,
      subtitle:
        `${summary.activities_inserted ?? 0} activities • `
        + `${summary.dependencies_inserted ?? 0} dependencies`,
    };
  }

  if (
    log.action
    === "schedule_cleared"
  ) {
    const summary = (
      newValue.summary
      || {}
    ) as Record<
      string,
      unknown
    >;

    return {
      title:
        "Project schedule removed",

      subtitle:
        `${summary.activities_deleted ?? 0} activities • `
        + `${summary.dependencies_deleted ?? 0} dependencies`,
    };
  }

  if (
    log.action
    === "exception_resolved"
  ) {
    return {
      title:
        String(
          newValue.exception_type
          || "Exception",
        )
        .replaceAll(
          "_",
          " ",
        ),

      subtitle:
        String(
          newValue.resolution_note
          || "Resolved",
        ),
    };
  }

  if (
    log.activity
  ) {
    return {
      title:
        `${log.activity.activity_code || "Activity"}`
        + (
          log.activity.activity_name
          ? ` • ${log.activity.activity_name}`
          : ""
        ),

      subtitle:
        getProgressChange(log)
          ? null
          : formatEntityType(
              log.entity_type,
            ),
    };
  }

  return {
    title:
      formatEntityType(
        log.entity_type,
      ),

    subtitle:
      log.entity_id,
  };
}


function actionToneClass(
  action: string,
) {
  if (
    action.includes(
      "resolved",
    )
    || action.includes(
      "approved",
    )
    || action.includes(
      "verified",
    )
    || action.includes(
      "imported",
    )
  ) {
    return "audit-tone-positive";
  }

  if (
    action.includes(
      "rejected",
    )
    || action.includes(
      "cleared",
    )
  ) {
    return "audit-tone-warning";
  }

  return "audit-tone-neutral";
}


export default function AuditTrail() {
  const [
    searchParams,
  ] = useSearchParams();

  const requestedProjectId =
    searchParams.get(
      "project_id",
    );

  const [
    projects,
    setProjects,
  ] = useState<Project[]>([]);

  const [
    selectedProjectId,
    setSelectedProjectId,
  ] = useState("");

  const [
    data,
    setData,
  ] = useState<
    AuditTrailResponse | null
  >(null);

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    projectsLoading,
    setProjectsLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    debouncedSearch,
    setDebouncedSearch,
  ] = useState("");

  const [
    action,
    setAction,
  ] = useState("");

  const [
    entityType,
    setEntityType,
  ] = useState("");

  const [
    page,
    setPage,
  ] = useState(1);

  const [
    expandedId,
    setExpandedId,
  ] = useState<
    string | null
  >(null);


  useEffect(() => {
    const timer =
      window.setTimeout(
        () => {
          setDebouncedSearch(
            search.trim(),
          );
        },
        300,
      );

    return () => {
      window.clearTimeout(
        timer,
      );
    };
  }, [search]);


  useEffect(() => {
    async function loadProjects() {
      try {
        setProjectsLoading(
          true,
        );

        const response =
          await getProjects();

        const rows =
          response.projects
          || [];

        setProjects(rows);

        if (
          requestedProjectId
        ) {
          const requested =
            rows.find(
              (project) =>
                project.id
                === requestedProjectId,
            );

          setSelectedProjectId(
            requested
              ? requested.id
              : "",
          );
        } else {
          setSelectedProjectId(
            "",
          );
        }
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught.message
            : "Failed to load projects.",
        );
      } finally {
        setProjectsLoading(
          false,
        );
      }
    }

    void loadProjects();
  }, [requestedProjectId]);


  useEffect(() => {
    if (
      !selectedProjectId
    ) {
      setData(null);
      setPage(1);
      return;
    }

    async function loadAuditTrail() {
      try {
        setLoading(true);
        setError("");

        const response =
          await getProjectAuditTrail(
            selectedProjectId,
            {
              action:
                action || undefined,

              entityType:
                entityType
                || undefined,

              search:
                debouncedSearch
                || undefined,

              page,

              pageSize:
                PAGE_SIZE,
            },
          );

        setData(response);
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught.message
            : "Failed to load audit trail.",
        );
      } finally {
        setLoading(false);
      }
    }

    void loadAuditTrail();
  }, [
    selectedProjectId,
    action,
    entityType,
    debouncedSearch,
    page,
  ]);


  useEffect(() => {
    setPage(1);
  }, [
    selectedProjectId,
    action,
    entityType,
    debouncedSearch,
  ]);


  const actionOptions =
    useMemo(
      () => {
        const fromSummary =
          Object.keys(
            data?.summary
              .action_counts
            || {},
          );

        const defaults = [
          "activity_match_approved",
          "activity_match_rejected",
          "activity_match_auto_verified",
          "exception_resolved",
          "schedule_imported",
          "schedule_cleared",
        ];

        return Array.from(
          new Set([
            ...defaults,
            ...fromSummary,
          ]),
        );
      },
      [data],
    );


  const visibleLogs =
    data?.audit_logs
    || [];


  return (
    <div className="audit-page">
      <div className="audit-page-header">
        <div>
          <h1>
            Audit Trail
          </h1>

          <p className="page-subtitle">
            Trace schedule changes,
            AI decisions, planner reviews,
            progress updates, and exception
            resolution across the project.
          </p>
        </div>
      </div>

      <section className="audit-project-card">
        <div className="audit-project-field">
          <label
            htmlFor="audit-project-select"
          >
            Project
          </label>

          <select
            id="audit-project-select"
            value={
              selectedProjectId
            }
            disabled={
              projectsLoading
            }
            onChange={
              (event) => {
                setSelectedProjectId(
                  event.target.value,
                );
              }
            }
          >
            <option value="">
              Select project
            </option>

            {projects.map(
              (project) => (
                <option
                  key={project.id}
                  value={project.id}
                >
                  {project.name}
                </option>
              ),
            )}
          </select>
        </div>

        {data && (
          <div className="audit-project-meta">
            <span>
              {data.project.name}
            </span>

            <span className="audit-project-status">
              {data.project.status}
            </span>
          </div>
        )}
      </section>

      {!selectedProjectId && (
        <section className="audit-empty-shell">
          <div className="audit-empty-icon">
            ⎇
          </div>

          <h2>
            Select a project to view
            its audit history
          </h2>

          <p>
            Every important project action
            will appear here in
            chronological order.
          </p>
        </section>
      )}

      {selectedProjectId && (
        <>
          <section className="audit-summary-grid">
            <article className="audit-summary-card">
              <span className="audit-summary-label">
                Total Events
              </span>

              <strong>
                {
                  data?.summary
                    .total_events
                  ?? 0
                }
              </strong>

              <small>
                Recorded project actions
              </small>
            </article>

            <article className="audit-summary-card">
              <span className="audit-summary-label">
                Planner Decisions
              </span>

              <strong>
                {
                  (
                    data?.summary
                      .action_counts[
                        "activity_match_approved"
                      ]
                    ?? 0
                  )
                  +
                  (
                    data?.summary
                      .action_counts[
                        "activity_match_rejected"
                      ]
                    ?? 0
                  )
                }
              </strong>

              <small>
                Reviewed AI matches
              </small>
            </article>

            <article className="audit-summary-card">
              <span className="audit-summary-label">
                Auto-Verified
              </span>

              <strong>
                {
                  data?.summary
                    .action_counts[
                      "activity_match_auto_verified"
                    ]
                  ?? 0
                }
              </strong>

              <small>
                Guardrail-approved matches
              </small>
            </article>

            <article className="audit-summary-card">
              <span className="audit-summary-label">
                Exceptions Resolved
              </span>

              <strong>
                {
                  data?.summary
                    .action_counts[
                      "exception_resolved"
                    ]
                  ?? 0
                }
              </strong>

              <small>
                Closed by planner/reviewer
              </small>
            </article>
          </section>

          <section className="audit-filter-bar">
            <div className="audit-search-wrap">
              <input
                type="search"
                value={search}
                placeholder={
                  "Search activity, actor, action..."
                }
                onChange={
                  (event) => {
                    setSearch(
                      event.target.value,
                    );
                  }
                }
              />
            </div>

            <select
              value={action}
              onChange={
                (event) => {
                  setAction(
                    event.target.value,
                  );
                }
              }
            >
              <option value="">
                All actions
              </option>

              {actionOptions.map(
                (option) => (
                  <option
                    key={option}
                    value={option}
                  >
                    {formatAction(
                      option,
                    )}
                  </option>
                ),
              )}
            </select>

            <select
              value={entityType}
              onChange={
                (event) => {
                  setEntityType(
                    event.target.value,
                  );
                }
              }
            >
              <option value="">
                All entity types
              </option>

              <option value="activity_match">
                Activity Match
              </option>

              <option value="exception">
                Exception
              </option>

              <option value="schedule">
                Schedule
              </option>
            </select>
          </section>

          {error && (
            <div className="audit-error">
              {error}
            </div>
          )}

          <section className="audit-timeline-shell">
            <div className="audit-timeline-header">
              <div>
                <h2>
                  Project History
                </h2>

                <p>
                  {
                    data?.pagination
                      .filtered_total
                    ?? 0
                  } matching events
                </p>
              </div>
            </div>

            {loading && (
              <div className="audit-loading">
                Loading audit history...
              </div>
            )}

            {!loading
              && visibleLogs.length
                === 0
              && (
                <div className="audit-empty-list">
                  No audit events match
                  the current filters.
                </div>
              )}

            {!loading
              && visibleLogs.length
                > 0
              && (
                <div className="audit-timeline">
                  {visibleLogs.map(
                    (log) => {
                      const detail =
                        getPrimaryDetail(
                          log,
                        );

                      const progress =
                        getProgressChange(
                          log,
                        );

                      const isExpanded =
                        expandedId
                        === log.id;

                      return (
                        <article
                          key={log.id}
                          className="audit-event"
                        >
                          <div
                            className={
                              `audit-event-marker `
                              + actionToneClass(
                                log.action,
                              )
                            }
                          />

                          <div className="audit-event-card">
                            <div className="audit-event-top">
                              <div className="audit-event-heading">
                                <div className="audit-event-action-row">
                                  <span
                                    className={
                                      `audit-action-badge `
                                      + actionToneClass(
                                        log.action,
                                      )
                                    }
                                  >
                                    {formatAction(
                                      log.action,
                                    )}
                                  </span>

                                  <span className="audit-entity-badge">
                                    {formatEntityType(
                                      log.entity_type,
                                    )}
                                  </span>
                                </div>

                                <h3>
                                  {detail.title}
                                </h3>

                                {detail.subtitle && (
                                  <p>
                                    {detail.subtitle}
                                  </p>
                                )}

                                {progress && (
                                  <div className="audit-progress-change">
                                    <span>
                                      {progress.previous}
                                    </span>

                                    <span className="audit-progress-arrow">
                                      →
                                    </span>

                                    <strong>
                                      {progress.current}
                                    </strong>

                                    {progress.method && (
                                      <small>
                                        {formatEntityType(
                                          progress.method,
                                        )}
                                      </small>
                                    )}
                                  </div>
                                )}
                              </div>

                              <div className="audit-event-time">
                                {formatDateTime(
                                  log.created_at,
                                )}
                              </div>
                            </div>

                            <div className="audit-event-footer">
                              <div className="audit-actor">
                                <div className="audit-avatar">
                                  {
                                    (
                                      log.actor
                                        ?.full_name
                                      || "S"
                                    )
                                      .charAt(0)
                                      .toUpperCase()
                                  }
                                </div>

                                <div>
                                  <strong>
                                    {
                                      log.actor
                                        ?.full_name
                                      || (
                                        log.user_id
                                          ? "Project User"
                                          : "System / Historical"
                                      )
                                    }
                                  </strong>

                                  <span>
                                    {
                                      log.actor
                                        ?.role
                                      || (
                                        log.user_id
                                          ? "user"
                                          : "legacy record"
                                      )
                                    }
                                  </span>
                                </div>
                              </div>

                              <button
                                type="button"
                                className="audit-details-button"
                                onClick={
                                  () => {
                                    setExpandedId(
                                      isExpanded
                                        ? null
                                        : log.id,
                                    );
                                  }
                                }
                              >
                                {
                                  isExpanded
                                    ? "Hide details"
                                    : "View details"
                                }
                              </button>
                            </div>

                            {isExpanded && (
                              <div className="audit-details-panel">
                                <div className="audit-detail-block">
                                  <span>
                                    Entity ID
                                  </span>

                                  <code>
                                    {log.entity_id}
                                  </code>
                                </div>

                                <div className="audit-json-grid">
                                  <div>
                                    <span className="audit-json-title">
                                      Before
                                    </span>

                                    <pre>
                                      {stringifyValue(
                                        log.old_value,
                                      )}
                                    </pre>
                                  </div>

                                  <div>
                                    <span className="audit-json-title">
                                      After
                                    </span>

                                    <pre>
                                      {stringifyValue(
                                        log.new_value,
                                      )}
                                    </pre>
                                  </div>
                                </div>
                              </div>
                            )}
                          </div>
                        </article>
                      );
                    },
                  )}
                </div>
              )}

            {data
              && data.pagination
                .total_pages
                > 1
              && (
                <div className="audit-pagination">
                  <button
                    type="button"
                    disabled={
                      !data.pagination
                        .has_previous
                      || loading
                    }
                    onClick={
                      () => {
                        setPage(
                          (current) =>
                            Math.max(
                              1,
                              current - 1,
                            ),
                        );
                      }
                    }
                  >
                    Previous
                  </button>

                  <span>
                    Page {
                      data.pagination.page
                    } of {
                      data.pagination
                        .total_pages
                    }
                  </span>

                  <button
                    type="button"
                    disabled={
                      !data.pagination
                        .has_next
                      || loading
                    }
                    onClick={
                      () => {
                        setPage(
                          (current) =>
                            current + 1,
                        );
                      }
                    }
                  >
                    Next
                  </button>
                </div>
              )}
          </section>
        </>
      )}
    </div>
  );
}
