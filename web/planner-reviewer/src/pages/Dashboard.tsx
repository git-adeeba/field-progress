import "../styles/dashboard.css";

import {
  AlertTriangle,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Ban,
  CheckCircle2,
  CircleAlert,
  ClipboardCheck,
  Clock3,
  Database,
  FolderKanban,
  Network,
  RefreshCw,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  getProjects,
} from "../services/projectService";

import {
  getProjectExceptions,
} from "../services/exceptionService";

import type {
  Project,
} from "../types/project";

import type {
  ProjectExceptionsResponse,
} from "../types/exception";


const DASHBOARD_PROJECT_STORAGE_KEY =
  "field-progress-dashboard-project-id";


function getProjectHealth(
  critical: number,
  high: number,
  open: number
) {

  if (critical > 0) {
    return {
      label:
        "Critical Attention",
      description:
        `${critical} critical execution exceptions require planner attention.`,
      className:
        "critical",
    };
  }


  if (high > 0) {
    return {
      label:
        "Attention Required",
      description:
        `${high} high-severity execution exceptions remain open.`,
      className:
        "warning",
    };
  }


  if (open > 0) {
    return {
      label:
        "Monitoring",
      description:
        `${open} execution exceptions are currently being monitored.`,
      className:
        "monitoring",
    };
  }


  return {
    label:
      "Healthy",
    description:
      "No open Reality-vs-Plan exceptions detected.",
    className:
      "healthy",
  };
}


export default function Dashboard() {

  const navigate =
    useNavigate();


  function navigateForActiveProject(
    path: string
  ) {
    if (!activeProject) {
      navigate(path);
      return;
    }

    const params =
      new URLSearchParams({
        project_id:
          activeProject.id,
      });

    navigate(
      `${path}?${params.toString()}`
    );
  }


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
    exceptionData,
    setExceptionData,
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


  useEffect(() => {

    loadInitialData();

  }, []);


  async function loadInitialData() {

    try {

      setLoading(true);

      setError("");


      const projectResponse =
        await getProjects();


      const loadedProjects =
        projectResponse.projects
        ??
        [];


      setProjects(
        loadedProjects
      );


      const savedProjectId =
        sessionStorage.getItem(
          DASHBOARD_PROJECT_STORAGE_KEY
        );


      const savedProject =
        savedProjectId
          ? (
              loadedProjects.find(
                (project) =>
                  project.id ===
                  savedProjectId
              )
              ||
              null
            )
          : null;


      setActiveProject(
        savedProject
      );


      if (savedProject) {

        await loadDashboardData(
          savedProject.id,
          false
        );

      } else {

        setExceptionData(
          null
        );

      }

    } catch (err) {

      console.error(err);


      setError(
        err instanceof Error
          ? err.message
          : "Unable to load dashboard."
      );

    } finally {

      setLoading(false);

    }
  }


  async function loadDashboardData(
    projectId: string,
    showRefreshState = true
  ) {

    try {

      if (showRefreshState) {
        setRefreshing(true);
      }


      setError("");


      const response =
        await getProjectExceptions(
          projectId,
          {
            status:
              "open",

            page:
              1,

            pageSize:
              1,
          }
        );


      setExceptionData(
        response
      );

    } catch (err) {

      console.error(err);


      setError(
        err instanceof Error
          ? err.message
          : "Unable to load project intelligence."
      );

    } finally {

      setRefreshing(false);

    }
  }


  async function handleProjectChange(
    projectId: string
  ) {

    const selected =
      projects.find(
        (
          project
        ) =>
          project.id ===
          projectId
      )
      ||
      null;


    setActiveProject(
      selected
    );


    if (!selected) {

      sessionStorage.removeItem(
        DASHBOARD_PROJECT_STORAGE_KEY
      );


      setExceptionData(
        null
      );


      setError("");


      return;
    }


    sessionStorage.setItem(
      DASHBOARD_PROJECT_STORAGE_KEY,
      selected.id
    );


    setLoading(true);


    await loadDashboardData(
      selected.id,
      false
    );


    setLoading(false);
  }


  const summary =
    exceptionData?.summary;


  const openExceptions =
    summary?.open
    ??
    summary?.total
    ??
    0;


  const criticalExceptions =
    summary
      ?.severity_counts
      ?.critical
    ??
    0;


  const highExceptions =
    summary
      ?.severity_counts
      ?.high
    ??
    0;


  const mediumExceptions =
    summary
      ?.severity_counts
      ?.medium
    ??
    0;


  const aheadOfPlan =
    summary
      ?.type_counts
      ?.AHEAD_OF_PLAN
    ??
    0;


  const behindPlan =
    summary
      ?.type_counts
      ?.BEHIND_PLAN
    ??
    0;


  const missingUpdates =
    summary
      ?.type_counts
      ?.MISSING_UPDATE
    ??
    0;


  const blockedActivities =
    summary
      ?.type_counts
      ?.BLOCKED_ACTIVITY
    ??
    0;


  const projectHealth =
    useMemo(
      () =>
        getProjectHealth(
          criticalExceptions,
          highExceptions,
          openExceptions
        ),
      [
        criticalExceptions,
        highExceptions,
        openExceptions,
      ]
    );


  return (
    <div className="dashboard-v2">

      <section className="dashboard-v2-header">

        <div>

          <div className="dashboard-v2-eyebrow">

            <Sparkles
              size={14}
            />

            EXECUTION INTELLIGENCE

          </div>


          <h2>
            Project Reality
            <span>
              {" "}vs Plan
            </span>
          </h2>


          <p>
            Live execution intelligence
            generated from validated
            field evidence, schedule
            progress and Reality-vs-Plan
            analysis.
          </p>

        </div>


        <div className="dashboard-v2-header-actions">

          <label>

            <span>
              Active project
            </span>


            <select
              value={
                activeProject?.id
                ??
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

          </label>


          <button
            className="dashboard-v2-refresh"
            disabled={
              refreshing
              ||
              !activeProject
            }
            onClick={() => {

              if (activeProject) {

                loadDashboardData(
                  activeProject.id
                );

              }

            }}
          >

            <RefreshCw
              size={16}
              className={
                refreshing
                  ? "spin"
                  : ""
              }
            />

            {refreshing
              ? "Refreshing"
              : "Refresh"}

          </button>

        </div>

      </section>


      {error && (

        <div className="dashboard-v2-error">

          <AlertTriangle
            size={17}
          />

          {error}

        </div>

      )}


      <section className="dashboard-health-section">

        <div
          className={
            `dashboard-health-card ${
              projectHealth.className
            }`
          }
        >

          <div className="dashboard-health-icon">

            <ShieldAlert
              size={25}
            />

          </div>


          <div className="dashboard-health-copy">

            <span>
              PROJECT HEALTH
            </span>

            <h3>
              {loading
                ? "Loading..."
                : activeProject
                  ? projectHealth.label
                  : "Select a Project"}
            </h3>

            <p>
              {loading
                ? "Loading available projects."
                : activeProject
                  ? projectHealth.description
                  : "Choose a project to load its execution intelligence."}
            </p>

          </div>


          <button
            disabled={!activeProject}
            onClick={() =>
              navigateForActiveProject(
                "/exceptions"
              )
            }
          >
            View Exceptions

            <ArrowRight
              size={15}
            />
          </button>

        </div>


        <div className="dashboard-health-context">

          <div>

            <span>
              Project
            </span>

            <strong>
              {activeProject?.name
              ??
              "—"}
            </strong>

          </div>


          <div>

            <span>
              Project status
            </span>

            <strong className="dashboard-status-live">

              <span />

              {activeProject?.status
                ??
                "—"}

            </strong>

          </div>


          <div>

            <span>
              Intelligence layer
            </span>

            <strong className="dashboard-status-live">

              <span />

              {activeProject
                ? "Live"
                : "—"}

            </strong>

          </div>


          <div>

            <span>
              Execution Twin
            </span>

            <strong className="dashboard-status-live">

              <span />

              {activeProject
                ? "Active"
                : "—"}

            </strong>

          </div>

        </div>

      </section>


      <section className="dashboard-metric-grid">

        <article
          className="dashboard-metric-card danger"
          onClick={() =>
            navigateForActiveProject(
              "/exceptions"
            )
          }
        >

          <div className="dashboard-metric-icon">

            <ShieldAlert
              size={20}
            />

          </div>


          <div>

            <span>
              Open Exceptions
            </span>

            <strong>
              {loading
                ? "—"
                : openExceptions}
            </strong>

            <p>
              Active Reality-vs-Plan
              deviations.
            </p>

          </div>

        </article>


        <article
          className="dashboard-metric-card critical"
          onClick={() =>
            navigateForActiveProject(
              "/exceptions"
            )
          }
        >

          <div className="dashboard-metric-icon">

            <AlertTriangle
              size={20}
            />

          </div>


          <div>

            <span>
              Critical
            </span>

            <strong>
              {loading
                ? "—"
                : criticalExceptions}
            </strong>

            <p>
              Highest-priority issues
              requiring attention.
            </p>

          </div>

        </article>


        <article
          className="dashboard-metric-card high"
          onClick={() =>
            navigateForActiveProject(
              "/exceptions"
            )
          }
        >

          <div className="dashboard-metric-icon">

            <CircleAlert
              size={20}
            />

          </div>


          <div>

            <span>
              High Severity
            </span>

            <strong>
              {loading
                ? "—"
                : highExceptions}
            </strong>

            <p>
              Significant execution
              or schedule variance.
            </p>

          </div>

        </article>


        <article className="dashboard-metric-card medium">

          <div className="dashboard-metric-icon">

            <Clock3
              size={20}
            />

          </div>


          <div>

            <span>
              Medium Severity
            </span>

            <strong>
              {loading
                ? "—"
                : mediumExceptions}
            </strong>

            <p>
              Conditions requiring
              monitoring.
            </p>

          </div>

        </article>

      </section>


      <section className="dashboard-reality-grid">

        <article className="dashboard-reality-panel">

          <div className="dashboard-panel-heading">

            <div>

              <span>
                REALITY VS PLAN
              </span>

              <h3>
                Execution Deviation
              </h3>

            </div>


            <button
              onClick={() =>
                navigateForActiveProject(
                  "/exceptions"
                )
              }
            >

              View all

              <ArrowRight
                size={14}
              />

            </button>

          </div>


          <div className="dashboard-deviation-grid">

            <div className="dashboard-deviation-item behind">

              <div>

                <ArrowDownRight
                  size={18}
                />

              </div>


              <section>

                <span>
                  Behind Plan
                </span>

                <strong>
                  {loading
                    ? "—"
                    : behindPlan}
                </strong>

                <p>
                  Activities whose actual
                  progress trails planned
                  progress.
                </p>

              </section>

            </div>


            <div className="dashboard-deviation-item missing">

              <div>

                <Clock3
                  size={18}
                />

              </div>


              <section>

                <span>
                  Missing Updates
                </span>

                <strong>
                  {loading
                    ? "—"
                    : missingUpdates}
                </strong>

                <p>
                  Planned work without
                  sufficient field evidence.
                </p>

              </section>

            </div>


            <div className="dashboard-deviation-item blocked">

              <div>

                <Ban
                  size={18}
                />

              </div>


              <section>

                <span>
                  Blocked Activities
                </span>

                <strong>
                  {loading
                    ? "—"
                    : blockedActivities}
                </strong>

                <p>
                  Execution currently
                  reported as blocked.
                </p>

              </section>

            </div>


            <div className="dashboard-deviation-item ahead">

              <div>

                <ArrowUpRight
                  size={18}
                />

              </div>


              <section>

                <span>
                  Ahead of Plan
                </span>

                <strong>
                  {loading
                    ? "—"
                    : aheadOfPlan}
                </strong>

                <p>
                  Activities progressing
                  beyond planned position.
                </p>

              </section>

            </div>

          </div>

        </article>


        <article className="dashboard-intelligence-panel">

          <div className="dashboard-panel-heading">

            <div>

              <span>
                INTELLIGENCE PIPELINE
              </span>

              <h3>
                System State
              </h3>

            </div>

          </div>


          <div className="dashboard-system-list">

            <div>

              <section className="dashboard-system-icon blue">

                <Database
                  size={17}
                />

              </section>


              <article>

                <strong>
                  Field Data
                </strong>

                <span>
                  Supervisor evidence
                  captured
                </span>

              </article>


              <CheckCircle2
                size={17}
              />

            </div>


            <div>

              <section className="dashboard-system-icon violet">

                <Sparkles
                  size={17}
                />

              </section>


              <article>

                <strong>
                  AI Reconciliation
                </strong>

                <span>
                  Extraction and matching
                  operational
                </span>

              </article>


              <CheckCircle2
                size={17}
              />

            </div>


            <div>

              <section className="dashboard-system-icon green">

                <ClipboardCheck
                  size={17}
                />

              </section>


              <article>

                <strong>
                  Planner Validation
                </strong>

                <span>
                  Review workflow active
                </span>

              </article>


              <CheckCircle2
                size={17}
              />

            </div>


            <div>

              <section className="dashboard-system-icon orange">

                <Network
                  size={17}
                />

              </section>


              <article>

                <strong>
                  Field Execution Twin
                </strong>

                <span>
                  Actual execution state
                  connected to plan
                </span>

              </article>


              <CheckCircle2
                size={17}
              />

            </div>


            <div>

              <section className="dashboard-system-icon red">

                <ShieldAlert
                  size={17}
                />

              </section>


              <article>

                <strong>
                  Reality-vs-Plan
                </strong>

                <span>
                  Exception detection
                  operational
                </span>

              </article>


              <CheckCircle2
                size={17}
              />

            </div>

          </div>

        </article>

      </section>


      <section className="dashboard-quick-section">

        <div className="dashboard-panel-heading">

          <div>

            <span>
              WORKSPACE
            </span>

            <h3>
              Continue Working
            </h3>

          </div>

        </div>


        <div className="dashboard-quick-grid">

          <button
            onClick={() =>
              navigateForActiveProject(
                "/review-queue"
              )
            }
          >

            <div className="dashboard-quick-icon violet">

              <ClipboardCheck
                size={19}
              />

            </div>


            <section>

              <strong>
                Review Queue
              </strong>

              <span>
                Validate AI schedule
                matches
              </span>

            </section>


            <ArrowRight
              size={16}
            />

          </button>


          <button
            onClick={() =>
              navigateForActiveProject(
                "/schedule"
              )
            }
          >

            <div className="dashboard-quick-icon blue">

              <FolderKanban
                size={19}
              />

            </div>


            <section>

              <strong>
                Schedule
              </strong>

              <span>
                Inspect L5/L6 project
                activities
              </span>

            </section>


            <ArrowRight
              size={16}
            />

          </button>


          <button
            onClick={() =>
              navigateForActiveProject(
                "/field-twin"
              )
            }
          >

            <div className="dashboard-quick-icon green">

              <Network
                size={19}
              />

            </div>


            <section>

              <strong>
                Execution Twin
              </strong>

              <span>
                Compare planned and actual
                execution
              </span>

            </section>


            <ArrowRight
              size={16}
            />

          </button>


          <button
            onClick={() =>
              navigateForActiveProject(
                "/exceptions"
              )
            }
          >

            <div className="dashboard-quick-icon red">

              <ShieldAlert
                size={19}
              />

            </div>


            <section>

              <strong>
                Exceptions
              </strong>

              <span>
                Investigate execution
                deviations
              </span>

            </section>


            <ArrowRight
              size={16}
            />

          </button>

        </div>

      </section>

    </div>
  );
}