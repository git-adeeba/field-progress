import "../styles/exceptions.css";

import {
  AlertCircle,
  AlertTriangle,
  ArrowDownRight,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  Ban,
  CheckCircle2,
  CircleAlert,
  Clock3,
  RefreshCw,
  Search,
  ShieldAlert,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  getProjectExceptions,
  resolveException,
} from "../services/exceptionService";

import {
  getProjects,
} from "../services/projectService";

import type {
  ExceptionType,
  ProjectException,
  ProjectExceptionsResponse,
} from "../types/exception";

import type {
  Project,
} from "../types/project";

import {
  useSearchParams,
} from "react-router-dom";




const PAGE_SIZE = 25;


const exceptionTypeLabels:
Record<ExceptionType, string> = {

  AHEAD_OF_PLAN:
    "Ahead of Plan",

  BEHIND_PLAN:
    "Behind Plan",

  BLOCKED_ACTIVITY:
    "Blocked Activity",

  MISSING_UPDATE:
    "Missing Update",

  UNPLANNED_WORK:
    "Unplanned Work",

  SEQUENCE_DEVIATION:
    "Sequence Deviation",

  PROGRESS_STAGNATION:
    "Progress Stagnation",

  REWORK:
    "Rework",
};


function formatPercent(
  value:
    number | null
) {

  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }


  return `${value.toFixed(2)}%`;
}


function formatVariance(
  value:
    number | null
) {

  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }


  const prefix =
    value > 0
      ? "+"
      : "";


  return `${prefix}${value.toFixed(2)}%`;
}


function formatDate(
  value:
    string | null
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
    return "—";
  }


  return date.toLocaleString(
    "en-IN",
    {
      dateStyle:
        "medium",

      timeStyle:
        "short",
    }
  );
}


function getExceptionIcon(
  type:
    ExceptionType
) {

  if (
    type ===
    "AHEAD_OF_PLAN"
  ) {
    return ArrowUpRight;
  }


  if (
    type ===
    "BEHIND_PLAN"
  ) {
    return ArrowDownRight;
  }


  if (
    type ===
    "BLOCKED_ACTIVITY"
  ) {
    return Ban;
  }


  if (
    type ===
    "MISSING_UPDATE"
  ) {
    return Clock3;
  }


  return AlertTriangle;
}


export default function Exceptions() {

  const [
    searchParams,
  ] =
    useSearchParams();


  const [
    projects,
    setProjects,
  ] =
    useState<Project[]>([]);


  const [
    activeProject,
    setActiveProject,
  ] =
    useState<Project | null>(
      null
    );


  const [
    response,
    setResponse,
  ] =
    useState<ProjectExceptionsResponse | null>(
      null
    );


  const [
    loading,
    setLoading,
  ] =
    useState(true);


  const [
    refreshing,
    setRefreshing,
  ] =
    useState(false);


  const [
    error,
    setError,
  ] =
    useState("");


  const [
    searchTerm,
    setSearchTerm,
  ] =
    useState("");


  const [
    debouncedSearch,
    setDebouncedSearch,
  ] =
    useState("");


  const [
    severityFilter,
    setSeverityFilter,
  ] =
    useState("all");


  const [
    typeFilter,
    setTypeFilter,
  ] =
    useState("all");


  const [
    statusFilter,
    setStatusFilter,
  ] =
    useState("open");


  const [
    page,
    setPage,
  ] =
    useState(1);


  const [
    resolvingId,
    setResolvingId,
  ] =
    useState<string | null>(
      null
    );


  const [
    resolveTarget,
    setResolveTarget,
  ] =
    useState<ProjectException | null>(
      null
    );


  const [
    resolutionNote,
    setResolutionNote,
  ] =
    useState("");


  useEffect(() => {

    const timeout =
      window.setTimeout(
        () => {
          setDebouncedSearch(
            searchTerm
          );

          setPage(1);
        },
        350
      );


    return () => {
      window.clearTimeout(
        timeout
      );
    };

  }, [
    searchTerm,
  ]);


  useEffect(() => {

    loadInitialData();

  }, []);


  useEffect(() => {

    if (
      !activeProject
    ) {
      return;
    }


    loadExceptions(
      activeProject.id,
      false
    );

  }, [
    activeProject?.id,
    statusFilter,
    severityFilter,
    typeFilter,
    debouncedSearch,
    page,
  ]);


  async function loadInitialData() {

    try {

      setLoading(true);

      setError("");


      const result =
        await getProjects();


      setProjects(
        result.projects
      );


      const requestedProjectId =
        searchParams.get(
          "project_id"
        );


      const selected =
        requestedProjectId
          ? (
              result.projects.find(
                (project) =>
                  project.id ===
                  requestedProjectId
              )
              ||
              null
            )
          : null;


      setActiveProject(
        selected
      );

    } catch (err) {

      console.error(err);


      setError(
        err instanceof Error
          ? err.message
          : "Unable to load project data."
      );

    } finally {

      setLoading(false);

    }
  }


  async function loadExceptions(
    projectId: string,
    showRefreshState = true
  ) {

    try {

      if (
        showRefreshState
      ) {
        setRefreshing(true);
      }


      setError("");


      const result =
        await getProjectExceptions(
          projectId,
          {
            status:
              statusFilter ===
              "all"
                ? undefined
                : statusFilter,

            severity:
              severityFilter ===
              "all"
                ? undefined
                : severityFilter,

            exceptionType:
              typeFilter ===
              "all"
                ? undefined
                : typeFilter,

            search:
              debouncedSearch,

            page,

            pageSize:
              PAGE_SIZE,
          }
        );


      setResponse(
        result
      );

    } catch (err) {

      console.error(err);


      setError(
        err instanceof Error
          ? err.message
          : "Unable to load exceptions."
      );

    } finally {

      setRefreshing(false);

      setLoading(false);

    }
  }


  function handleProjectChange(
    projectId: string
  ) {

    const project =
      projects.find(
        (
          item
        ) =>
          item.id ===
          projectId
      )
      ||
      null;


    setPage(1);

    setActiveProject(
      project
    );
  }


  function handleStatusChange(
    value: string
  ) {

    setPage(1);

    setStatusFilter(
      value
    );
  }


  function handleSeverityChange(
    value: string
  ) {

    setPage(1);

    setSeverityFilter(
      value
    );
  }


  function handleTypeChange(
    value: string
  ) {

    setPage(1);

    setTypeFilter(
      value
    );
  }


  async function handleResolve() {

    if (
      !resolveTarget
    ) {
      return;
    }


    try {

      setResolvingId(
        resolveTarget.id
      );


      await resolveException(
        resolveTarget.id,
        resolutionNote.trim()
      );


      setResolveTarget(
        null
      );

      setResolutionNote("");


      if (
        activeProject
      ) {
        await loadExceptions(
          activeProject.id,
          false
        );
      }

    } catch (err) {

      console.error(err);


      setError(
        err instanceof Error
          ? err.message
          : "Unable to resolve exception."
      );

    } finally {

      setResolvingId(
        null
      );

    }
  }


  const summary =
    response?.summary;


  const pagination =
    response?.pagination;


  const exceptions =
    response?.exceptions
    ??
    [];


  const totalCount =
    summary?.total
    ??
    0;


  const criticalCount =
    summary
      ?.severity_counts
      ?.critical
    ??
    0;


  const highCount =
    summary
      ?.severity_counts
      ?.high
    ??
    0;


  const mediumCount =
    summary
      ?.severity_counts
      ?.medium
    ??
    0;


  const startItem =
    pagination &&
    pagination.filtered_total > 0
      ? (
          (
            pagination.page - 1
          )
          *
          pagination.page_size
        )
        + 1
      : 0;


  const endItem =
    pagination
      ? Math.min(
          pagination.page
          *
          pagination.page_size,
          pagination.filtered_total
        )
      : 0;


  return (
    <div className="exceptions-page">

      <section className="exceptions-toolbar">

        <div className="exceptions-project-selector">

          <span>
            Active project
          </span>

          <select
            value={
              activeProject?.id
              ||
              ""
            }
            onChange={(
              event
            ) =>
              handleProjectChange(
                event.target.value
              )
            }
          >

            <option value="">
              Select a project
            </option>

            {projects.map(
              (
                project
              ) => (

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

        </div>


        <button
          className="exceptions-refresh-button"
          disabled={
            refreshing
            ||
            !activeProject
          }
          onClick={() => {

            if (
              activeProject
            ) {
              loadExceptions(
                activeProject.id
              );
            }

          }}
        >

          <RefreshCw
            size={17}
            className={
              refreshing
                ? "spin"
                : ""
            }
          />

          {refreshing
            ? "Refreshing..."
            : "Refresh"}

        </button>

      </section>


      {error && (

        <div className="exceptions-error">

          <AlertCircle
            size={18}
          />

          <span>
            {error}
          </span>

        </div>

      )}


      <section className="exceptions-summary-grid">

        <article className="exception-summary-card">

          <div className="exception-summary-icon total">

            <ShieldAlert
              size={22}
            />

          </div>

          <div>

            <span>
              {statusFilter ===
              "open"
                ? "Active Exceptions"
                : statusFilter ===
                  "resolved"
                  ? "Resolved Exceptions"
                  : "Total Exceptions"}
            </span>

            <strong>
              {loading
                ? "—"
                : totalCount}
            </strong>

            <p>
              Reality-vs-Plan issues
              detected across the
              project schedule.
            </p>

          </div>

        </article>


        <article className="exception-summary-card">

          <div className="exception-summary-icon critical">

            <AlertTriangle
              size={22}
            />

          </div>

          <div>

            <span>
              Critical
            </span>

            <strong>
              {loading
                ? "—"
                : criticalCount}
            </strong>

            <p>
              Highest-priority
              execution deviations.
            </p>

          </div>

        </article>


        <article className="exception-summary-card">

          <div className="exception-summary-icon high">

            <CircleAlert
              size={22}
            />

          </div>

          <div>

            <span>
              High
            </span>

            <strong>
              {loading
                ? "—"
                : highCount}
            </strong>

            <p>
              Significant schedule
              or progress variance.
            </p>

          </div>

        </article>


        <article className="exception-summary-card">

          <div className="exception-summary-icon medium">

            <Clock3
              size={22}
            />

          </div>

          <div>

            <span>
              Medium
            </span>

            <strong>
              {loading
                ? "—"
                : mediumCount}
            </strong>

            <p>
              Conditions requiring
              monitoring or review.
            </p>

          </div>

        </article>

      </section>


      <section className="exceptions-filter-panel">

        <div className="exceptions-search">

          <Search
            size={18}
          />

          <input
            type="text"
            placeholder="Search activity, exception or description..."
            value={
              searchTerm
            }
            onChange={(
              event
            ) =>
              setSearchTerm(
                event.target.value
              )
            }
          />

        </div>


        <select
          value={
            severityFilter
          }
          onChange={(
            event
          ) =>
            handleSeverityChange(
              event.target.value
            )
          }
        >

          <option value="all">
            All severities
          </option>

          <option value="critical">
            Critical
          </option>

          <option value="high">
            High
          </option>

          <option value="medium">
            Medium
          </option>

          <option value="low">
            Low
          </option>

        </select>


        <select
          value={
            typeFilter
          }
          onChange={(
            event
          ) =>
            handleTypeChange(
              event.target.value
            )
          }
        >

          <option value="all">
            All types
          </option>

          {Object.entries(
            exceptionTypeLabels
          ).map(
            ([
              value,
              label,
            ]) => (

              <option
                key={
                  value
                }
                value={
                  value
                }
              >
                {label}
              </option>

            )
          )}

        </select>


        <select
          value={
            statusFilter
          }
          onChange={(
            event
          ) =>
            handleStatusChange(
              event.target.value
            )
          }
        >

          <option value="open">
            Open
          </option>

          <option value="resolved">
            Resolved
          </option>

          <option value="all">
            All statuses
          </option>

        </select>

      </section>


      <section className="exceptions-list-section">

        <div className="exceptions-list-heading">

          <div>

            <span>
              Reality vs Plan
            </span>

            <h2>
              Execution Exceptions
            </h2>

          </div>


          <strong>
            {pagination
              ? `${pagination.filtered_total} matching`
              : "—"}
          </strong>

        </div>


        {loading ? (

          <div className="exceptions-empty-state">

            <RefreshCw
              size={24}
              className="spin"
            />

            <strong>
              Loading exceptions
            </strong>

            <span>
              Reading project
              Reality-vs-Plan data...
            </span>

          </div>

        ) : exceptions.length ===
          0 ? (

          <div className="exceptions-empty-state">

            <CheckCircle2
              size={26}
            />

            <strong>
              No matching exceptions
            </strong>

            <span>
              Try changing your
              search or filters.
            </span>

          </div>

        ) : (

          <>

            <div className="exceptions-table-wrap">

              <table className="exceptions-table">

                <thead>

                  <tr>

                    <th>
                      Exception
                    </th>

                    <th>
                      Severity
                    </th>

                    <th>
                      Planned
                    </th>

                    <th>
                      Actual
                    </th>

                    <th>
                      Variance
                    </th>

                    <th>
                      Detected
                    </th>

                    <th>
                      Status
                    </th>

                    <th>
                      Action
                    </th>

                  </tr>

                </thead>


                <tbody>

                  {exceptions.map(
                    (
                      item
                    ) => {

                      const Icon =
                        getExceptionIcon(
                          item.exception_type
                        );


                      return (

                        <tr
                          key={
                            item.id
                          }
                        >

                          <td>

                            <div className="exception-main-cell">

                              <div
                                className={
                                  `exception-type-icon ${
                                    item.exception_type
                                      .toLowerCase()
                                  }`
                                }
                              >

                                <Icon
                                  size={18}
                                />

                              </div>


                              <div>

                                <strong>
                                  {item.title}
                                </strong>

                                <span>
                                  {
                                    exceptionTypeLabels[
                                      item.exception_type
                                    ]
                                    ??
                                    item.exception_type
                                  }
                                </span>

                                {item.description && (

                                  <p>
                                    {item.description}
                                  </p>

                                )}

                              </div>

                            </div>

                          </td>


                          <td>

                            <span
                              className={
                                `exception-severity-badge ${
                                  item.severity
                                }`
                              }
                            >
                              {item.severity}
                            </span>

                          </td>


                          <td className="exception-progress-cell">

                            {formatPercent(
                              item.planned_progress
                            )}

                          </td>


                          <td className="exception-progress-cell">

                            {formatPercent(
                              item.actual_progress
                            )}

                          </td>


                          <td>

                            <span
                              className={
                                item.variance !==
                                  null &&
                                item.variance > 0
                                  ? "exception-positive-variance"
                                  : "exception-negative-variance"
                              }
                            >

                              {formatVariance(
                                item.variance
                              )}

                            </span>

                          </td>


                          <td className="exception-date-cell">

                            {formatDate(
                              item.detected_at
                            )}

                          </td>


                          <td>

                            <span
                              className={
                                `exception-status-badge ${
                                  item.status
                                }`
                              }
                            >
                              {item.status}
                            </span>

                          </td>


                          <td>

                            {item.status ===
                            "open" ? (

                              <button
                                className="exception-resolve-button"
                                onClick={() =>
                                  setResolveTarget(
                                    item
                                  )
                                }
                              >
                                Resolve
                              </button>

                            ) : (

                              <span className="exception-resolved-label">

                                <CheckCircle2
                                  size={16}
                                />

                                Resolved

                              </span>

                            )}

                          </td>

                        </tr>

                      );

                    }
                  )}

                </tbody>

              </table>

            </div>


            <div className="exceptions-pagination">

              <div>

                Showing{" "}

                <strong>
                  {startItem}
                  –
                  {endItem}
                </strong>

                {" "}of{" "}

                <strong>
                  {pagination
                    ?.filtered_total
                    ??
                    0}
                </strong>

              </div>


              <div className="exceptions-pagination-controls">

                <button
                  disabled={
                    !pagination
                    ?.has_previous
                    ||
                    refreshing
                  }
                  onClick={() =>
                    setPage(
                      (
                        current
                      ) =>
                        Math.max(
                          1,
                          current - 1
                        )
                    )
                  }
                >

                  <ArrowLeft
                    size={16}
                  />

                </button>


                <span>
                  Page{" "}

                  <strong>
                    {pagination
                      ?.page
                      ??
                      1}
                  </strong>

                  {" "}of{" "}

                  <strong>
                    {pagination
                      ?.total_pages
                      ??
                      1}
                  </strong>
                </span>


                <button
                  disabled={
                    !pagination
                    ?.has_next
                    ||
                    refreshing
                  }
                  onClick={() =>
                    setPage(
                      (
                        current
                      ) =>
                        current + 1
                    )
                  }
                >

                  <ArrowRight
                    size={16}
                  />

                </button>

              </div>

            </div>

          </>

        )}

      </section>


      {resolveTarget && (

        <div className="exception-modal-backdrop">

          <div className="exception-modal">

            <div className="exception-modal-icon">

              <CheckCircle2
                size={24}
              />

            </div>


            <div className="exception-modal-copy">

              <span>
                Resolve Exception
              </span>

              <h3>
                {resolveTarget.title}
              </h3>

              <p>
                Mark this exception
                as resolved and add
                an optional planner
                note explaining the
                resolution.
              </p>

            </div>


            <textarea
              placeholder="Resolution note..."
              value={
                resolutionNote
              }
              onChange={(
                event
              ) =>
                setResolutionNote(
                  event.target.value
                )
              }
            />


            <div className="exception-modal-actions">

              <button
                className="exception-modal-cancel"
                onClick={() => {

                  setResolveTarget(
                    null
                  );

                  setResolutionNote(
                    ""
                  );

                }}
              >
                Cancel
              </button>


              <button
                className="exception-modal-confirm"
                onClick={
                  handleResolve
                }
                disabled={
                  resolvingId ===
                  resolveTarget.id
                }
              >

                {resolvingId ===
                resolveTarget.id
                  ? "Resolving..."
                  : "Mark Resolved"}

              </button>

            </div>

          </div>

        </div>

      )}

    </div>
  );
}
