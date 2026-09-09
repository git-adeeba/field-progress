import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Activity,
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle2,
  CircleDashed,
  Clock3,
  Database,
  GitCompareArrows,
  RefreshCw,
  Search,
  ShieldCheck,
  Target,
} from "lucide-react";

import {
  useSearchParams,
} from "react-router-dom";

import {
  getProjects,
} from "../services/projectService";

import {
  getFieldTwin,
} from "../services/fieldTwinService";

import type {
  FieldTwinResponse,
  PlanState,
  TwinActivity,
} from "../types/fieldTwin";

import type {
  Project,
} from "../types/project";


type FilterState =
  | "all"
  | PlanState;


function formatDate(
  value?: string | null
) {
  if (!value) {
    return "—";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleDateString(
    undefined,
    {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }
  );
}


function formatFieldState(
  state?: string | null
) {
  const normalized =
    state?.trim().toLowerCase() || "";

  switch (normalized) {
    case "completed":
      return "Completed";

    case "in_progress":
      return "In Progress";

    case "started":
      return "Started";

    case "blocked":
      return "Blocked";

    case "unverified":
      return "Unverified";

    case "field_activity_detected":
      return "Activity Detected";

    case "no_field_evidence":
      return "No Evidence";

    case "":
      return "No Evidence";

    default:
      return normalized
        .replaceAll("_", " ")
        .replace(
          /\b\w/g,
          (letter) =>
            letter.toUpperCase()
        );
  }
}


function formatPlanState(
  state: PlanState
) {
  switch (state) {
    case "ahead":
      return "Ahead";

    case "behind":
      return "Behind";

    case "on_track":
      return "On Track";

    case "no_field_evidence":
      return "No Field Evidence";
  }
}


function getPlanIcon(
  state: PlanState
) {
  switch (state) {
    case "ahead":
      return (
        <ArrowUpRight size={15} />
      );

    case "behind":
      return (
        <ArrowDownRight size={15} />
      );

    case "on_track":
      return (
        <CheckCircle2 size={15} />
      );

    case "no_field_evidence":
      return (
        <CircleDashed size={15} />
      );
  }
}


export default function FieldTwin() {
  const [
    searchParams,
  ] = useSearchParams();

  const requestedProjectId =
    searchParams.get(
      "project_id"
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
    twin,
    setTwin,
  ] =
    useState<FieldTwinResponse | null>(
      null
    );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    twinLoading,
    setTwinLoading,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    search,
    setSearch,
  ] = useState("");

  const [
    filter,
    setFilter,
  ] =
    useState<FilterState>(
      "all"
    );


  async function loadProjects() {
    try {
      setLoading(true);
      setError("");

      const response =
        await getProjects();

      const rows =
        response.projects || [];

      setProjects(rows);

      if (requestedProjectId) {
        const requestedProject =
          rows.find(
            (project) =>
              project.id ===
              requestedProjectId
          );

        if (requestedProject) {
          setSelectedProjectId(
            requestedProject.id
          );
        } else {
          setSelectedProjectId("");
        }
      } else {
        setSelectedProjectId("");
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load projects"
      );
    } finally {
      setLoading(false);
    }
  }


  async function loadTwin(
    projectId: string
  ) {
    if (!projectId) {
      return;
    }

    try {
      setTwinLoading(true);
      setError("");

      const response =
        await getFieldTwin(
          projectId
        );

      setTwin(response);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load Field Twin"
      );

      setTwin(null);
    } finally {
      setTwinLoading(false);
    }
  }


  useEffect(() => {
    loadProjects();
  }, [requestedProjectId]);


  useEffect(() => {
    if (
      selectedProjectId
    ) {
      loadTwin(
        selectedProjectId
      );
    }
  }, [
    selectedProjectId,
  ]);


  const filteredActivities =
    useMemo(() => {
      if (!twin) {
        return [];
      }

      const query =
        search
          .trim()
          .toLowerCase();

      return (twin.activities || []).filter(
        (activity) => {
          const matchesFilter =
            filter === "all"
              ? true
              : activity.plan_state ===
                filter;

          const searchable =
            [
              activity.activity_code,
              activity.activity_name,
              activity.discipline,
              activity.area,
              activity.field_state,
              activity.plan_state,
            ]
              .filter(Boolean)
              .join(" ")
              .toLowerCase();

          const matchesSearch =
            !query ||
            searchable.includes(
              query
            );

          return (
            matchesFilter &&
            matchesSearch
          );
        }
      );
    }, [
      twin,
      search,
      filter,
    ]);


  if (loading) {
    return (
      <div className="twin-loading-page">
        <RefreshCw
          size={22}
          className="spin"
        />

        <span>
          Loading Field Execution Twin...
        </span>
      </div>
    );
  }


  return (
    <div className="field-twin-page">
      <section className="twin-hero">
        <div>
          <div className="twin-eyebrow">
            <GitCompareArrows
              size={15}
            />

            LIVE EXECUTION INTELLIGENCE
          </div>

          <h1>
            Field Execution Twin
          </h1>

          <p>
            Compare what was planned
            with what is actually
            happening on the field,
            using verified execution
            evidence.
          </p>
        </div>

        <div className="twin-hero-actions">
          <label>
            Project
          </label>

          <select
            value={
              selectedProjectId
            }
            onChange={(event) =>
              setSelectedProjectId(
                event.target.value
              )
            }
          >
            <option value="">
              Select project
            </option>

            {projects.map(
              (project) => (
                <option
                  key={
                    project.id
                  }
                  value={
                    project.id
                  }
                >
                  {project.name}
                </option>
              )
            )}
          </select>

          <button
            className="twin-refresh-button"
            onClick={() =>
              loadTwin(
                selectedProjectId
              )
            }
            disabled={
              twinLoading ||
              !selectedProjectId
            }
          >
            <RefreshCw
              size={16}
              className={
                twinLoading
                  ? "spin"
                  : ""
              }
            />

            Refresh
          </button>
        </div>
      </section>


      {error && (
        <div className="twin-error">
          <AlertTriangle
            size={18}
          />

          {error}
        </div>
      )}


      {twin && (
        <>
          <section className="twin-project-bar">
            <div>
              <span>
                Active Project
              </span>

              <strong>
                {twin.project.name}
              </strong>
            </div>

            <div>
              <span>
                Project Status
              </span>

              <strong>
                {twin.project.status ||
                  "—"}
              </strong>
            </div>

            <div>
              <span>
                Timeline
              </span>

              <strong>
                {formatDate(
                  twin.project
                    .start_date
                )}
                {" → "}
                {formatDate(
                  twin.project
                    .end_date
                )}
              </strong>
            </div>

            <div>
              <span>
                Twin Generated
              </span>

              <strong>
                {formatDate(
                  twin.generated_at
                )}
              </strong>
            </div>
          </section>


          <section className="twin-summary-grid">
            <article className="twin-stat-card">
              <div className="twin-stat-icon">
                <Database
                  size={20}
                />
              </div>

              <div>
                <span>
                  Total Activities
                </span>

                <strong>
                  {
                    twin.summary
                      .total_activities
                  }
                </strong>

                <small>
                  Imported schedule
                  activities
                </small>
              </div>
            </article>


            <article className="twin-stat-card">
              <div className="twin-stat-icon">
                <ShieldCheck
                  size={20}
                />
              </div>

              <div>
                <span>
                  Field Evidence
                </span>

                <strong>
                  {
                    twin.summary
                      .activities_with_field_evidence
                  }
                </strong>

                <small>
                  Activities with
                  execution evidence
                </small>
              </div>
            </article>


            <article className="twin-stat-card twin-ahead">
              <div className="twin-stat-icon">
                <ArrowUpRight
                  size={20}
                />
              </div>

              <div>
                <span>
                  Ahead
                </span>

                <strong>
                  {
                    twin.summary
                      .ahead
                  }
                </strong>

                <small>
                  Actual ahead of
                  planned progress
                </small>
              </div>
            </article>


            <article className="twin-stat-card twin-track">
              <div className="twin-stat-icon">
                <Target
                  size={20}
                />
              </div>

              <div>
                <span>
                  On Track
                </span>

                <strong>
                  {
                    twin.summary
                      .on_track
                  }
                </strong>

                <small>
                  Within plan
                  tolerance
                </small>
              </div>
            </article>


            <article className="twin-stat-card twin-behind">
              <div className="twin-stat-icon">
                <AlertTriangle
                  size={20}
                />
              </div>

              <div>
                <span>
                  Behind
                </span>

                <strong>
                  {
                    twin.summary
                      .behind
                  }
                </strong>

                <small>
                  Actual behind
                  planned progress
                </small>
              </div>
            </article>
          </section>


          <section className="twin-progress-comparison">
            <div className="twin-comparison-heading">
              <div>
                <span className="section-kicker">
                  PROJECT EXECUTION STATE
                </span>

                <h2>
                  Planned vs Actual
                </h2>
              </div>

              <Activity
                size={23}
              />
            </div>

            <div className="twin-progress-columns">
              <div className="twin-progress-block">
                <div className="twin-progress-label">
                  <span>
                    Planned Progress
                  </span>

                  <strong>
                    {
                      twin.summary
                        .average_planned_progress
                    }
                    %
                  </strong>
                </div>

                <div className="twin-progress-track">
                  <div
                    className="twin-progress-fill planned"
                    style={{
                      width: `${Math.min(
                        twin.summary
                          .average_planned_progress,
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>


              <div className="twin-progress-block">
                <div className="twin-progress-label">
                  <span>
                    Actual Progress
                  </span>

                  <strong>
                    {
                      twin.summary
                        .average_actual_progress
                    }
                    %
                  </strong>
                </div>

                <div className="twin-progress-track">
                  <div
                    className="twin-progress-fill actual"
                    style={{
                      width: `${Math.min(
                        twin.summary
                          .average_actual_progress,
                        100
                      )}%`,
                    }}
                  />
                </div>
              </div>
            </div>
          </section>


          <section className="twin-workspace">
            <div className="twin-workspace-header">
              <div>
                <span className="section-kicker">
                  ACTIVITY-LEVEL TWIN
                </span>

                <h2>
                  Schedule vs Field Reality
                </h2>

                <p>
                  Every schedule activity
                  compared against its
                  verified field evidence.
                </p>
              </div>

              <div className="twin-result-count">
                {
                  filteredActivities.length
                }
                {" "}
                activities
              </div>
            </div>


            <div className="twin-toolbar">
              <div className="twin-search">
                <Search
                  size={17}
                />

                <input
                  value={search}
                  onChange={(event) =>
                    setSearch(
                      event.target.value
                    )
                  }
                  placeholder="Search activity, discipline, area..."
                />
              </div>


              <div className="twin-filter-tabs">
                {[
                  ["all", "All"],
                  ["ahead", "Ahead"],
                  [
                    "on_track",
                    "On Track",
                  ],
                  [
                    "behind",
                    "Behind",
                  ],
                  [
                    "no_field_evidence",
                    "No Evidence",
                  ],
                ].map(
                  ([
                    value,
                    label,
                  ]) => (
                    <button
                      key={
                        value
                      }
                      className={
                        filter ===
                        value
                          ? "active"
                          : ""
                      }
                      onClick={() =>
                        setFilter(
                          value as FilterState
                        )
                      }
                    >
                      {label}
                    </button>
                  )
                )}
              </div>
            </div>


            <div className="twin-activity-list">
              {filteredActivities.length ===
              0 ? (
                <div className="twin-empty">
                  <CircleDashed
                    size={30}
                  />

                  <strong>
                    No activities found
                  </strong>

                  <span>
                    Try changing the
                    search or filter.
                  </span>
                </div>
              ) : (
                filteredActivities.map(
                  (
                    activity: TwinActivity
                  ) => (
                    <article
                      className="twin-activity-card"
                      key={
                        activity.activity_id
                      }
                    >
                      <div className="twin-activity-head">
                        <div>
                          <div className="twin-activity-meta">
                            <span className="twin-code">
                              {activity.activity_code ||
                                "NO CODE"}
                            </span>

                            {activity.discipline && (
                              <span>
                                {
                                  activity.discipline
                                }
                              </span>
                            )}

                            {activity.area && (
                              <span>
                                {
                                  activity.area
                                }
                              </span>
                            )}
                          </div>

                          <h3>
                            {activity.activity_name ||
                              "Unnamed Activity"}
                          </h3>
                        </div>

                        <div
                          className={`twin-plan-badge ${activity.plan_state}`}
                        >
                          {getPlanIcon(
                            activity.plan_state
                          )}

                          {formatPlanState(
                            activity.plan_state
                          )}
                        </div>
                      </div>


                      <div className="twin-activity-body">
                        <div className="twin-side planned-side">
                          <div className="twin-side-label">
                            PLANNED
                          </div>

                          <div className="twin-side-progress">
                            <strong>
                              {
                                activity.planned_progress
                              }
                              %
                            </strong>

                            <span>
                              Schedule Progress
                            </span>
                          </div>

                          <div className="twin-mini-track">
                            <div
                              style={{
                                width: `${Math.min(
                                  activity.planned_progress,
                                  100
                                )}%`,
                              }}
                            />
                          </div>

                          <div className="twin-side-dates">
                            <span>
                              Start
                              <strong>
                                {formatDate(
                                  activity.planned_start
                                )}
                              </strong>
                            </span>

                            <span>
                              Finish
                              <strong>
                                {formatDate(
                                  activity.planned_finish
                                )}
                              </strong>
                            </span>
                          </div>
                        </div>


                        <div className="twin-link-column">
                          <div className="twin-link-line" />

                          <GitCompareArrows
                            size={20}
                          />

                          <div className="twin-link-line" />
                        </div>


                        <div className="twin-side actual-side">
                          <div className="twin-side-label">
                            FIELD REALITY
                          </div>

                          <div className="twin-side-progress">
                            <strong>
                              {
                                activity.actual_progress
                              }
                              %
                            </strong>

                            <span>
                              Verified Actual
                            </span>
                          </div>

                          <div className="twin-mini-track">
                            <div
                              style={{
                                width: `${Math.min(
                                  activity.actual_progress,
                                  100
                                )}%`,
                              }}
                            />
                          </div>

                          <div className="twin-field-info">
                            <div>
                              <Clock3
                                size={15}
                              />

                              <span>
                                {formatFieldState(
                                  activity.field_state
                                )}
                              </span>
                            </div>

                            <div>
                              <Database
                                size={15}
                              />

                              <span>
                                {
                                  activity.execution_event_count
                                }
                                {" "}
                                evidence event
                                {activity.execution_event_count ===
                                1
                                  ? ""
                                  : "s"}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>


                      <div className="twin-activity-footer">
                        <div>
                          Progress Difference
                          <strong
                            className={
                              activity.progress_difference >
                              0
                                ? "positive"
                                : activity.progress_difference <
                                  0
                                ? "negative"
                                : ""
                            }
                          >
                            {activity.progress_difference >
                            0
                              ? "+"
                              : ""}
                            {
                              activity.progress_difference
                            }
                            %
                          </strong>
                        </div>


                        {activity.latest_execution_event ? (
                          <div className="twin-latest-event">
                            <ShieldCheck
                              size={15}
                            />

                            <span>
                              Latest evidence:
                            </span>

                            <strong>
                              {activity
                                .latest_execution_event
                                .execution_name ||
                                activity
                                  .latest_execution_event
                                  .execution_type ||
                                "Verified field event"}
                            </strong>
                          </div>
                        ) : (
                          <div className="twin-no-event">
                            No verified field
                            evidence yet
                          </div>
                        )}
                      </div>
                    </article>
                  )
                )
              )}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
