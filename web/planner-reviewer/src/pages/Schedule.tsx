import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  Activity,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  FileSpreadsheet,
  Layers3,
  Search,
  SlidersHorizontal,
  UploadCloud,
  Trash2,
  AlertTriangle,
  X,
} from "lucide-react";

import {
  useSearchParams,
} from "react-router-dom";

import { getProjects } from "../services/projectService";
import { getProjectActivities } from "../services/activityService";
import {
  clearProjectSchedule,
  confirmScheduleImport,
  previewScheduleImport,
} from "../services/scheduleImportService";

import type { Project } from "../types/project";
import type { Activity as ProjectActivity } from "../types/activity";
import type {
  ScheduleImportResponse,
  SchedulePreviewResponse,
} from "../types/scheduleImport";

import "../styles/schedule-import.css";

const ITEMS_PER_PAGE = 25;

const ALLOWED_EXTENSIONS = [".xer", ".xlsx", ".csv"];
const MAX_FILE_SIZE = 50 * 1024 * 1024;

function getErrorMessage(error: unknown) {
  if (error instanceof Error) {
    return error.message;
  }

  return "Something went wrong.";
}

export default function Schedule() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [
    searchParams,
  ] = useSearchParams();

  const requestedProjectId =
    searchParams.get(
      "project_id"
    );

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");

  const [activities, setActivities] = useState<ProjectActivity[]>([]);

  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingActivities, setLoadingActivities] = useState(false);

  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [disciplineFilter, setDisciplineFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [wbsFilter, setWbsFilter] = useState("all");

  const [currentPage, setCurrentPage] = useState(1);

  const [importOpen, setImportOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const [preview, setPreview] =
    useState<SchedulePreviewResponse | null>(null);

  const [importResult, setImportResult] =
    useState<ScheduleImportResponse | null>(null);

  const [previewing, setPreviewing] = useState(false);
  const [importing, setImporting] = useState(false);
  const [importError, setImportError] = useState("");

  const [clearOpen, setClearOpen] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [clearError, setClearError] = useState("");

  useEffect(() => {
    async function loadProjects() {
      try {
        setLoadingProjects(true);
        setError("");

        const response = await getProjects();

        const loadedProjects =
          response.projects || [];

        setProjects(
          loadedProjects
        );

        if (requestedProjectId) {
          const requestedProject =
            loadedProjects.find(
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
        console.error(err);

        setError("Unable to load projects from the backend.");
      } finally {
        setLoadingProjects(false);
      }
    }

    void loadProjects();
  }, [requestedProjectId]);

  async function refreshActivities(
    projectId: string,
    resetFilters = false
  ) {
    if (!projectId) {
      setActivities([]);
      return;
    }

    try {
      setLoadingActivities(true);
      setError("");

      if (resetFilters) {
        setSearch("");
        setDisciplineFilter("all");
        setStatusFilter("all");
        setWbsFilter("all");
        setCurrentPage(1);
      }

      const response = await getProjectActivities(projectId);

      setActivities(response.activities);
    } catch (err) {
      console.error(err);

      setActivities([]);
      setError("Unable to load schedule activities.");
    } finally {
      setLoadingActivities(false);
    }
  }

  useEffect(() => {
    if (!selectedProjectId) {
      setActivities([]);
      return;
    }

    void refreshActivities(selectedProjectId, true);
  }, [selectedProjectId]);

  const disciplines = useMemo(() => {
    return Array.from(
      new Set(
        activities
          .map((activity) => activity.discipline)
          .filter((value): value is string => Boolean(value))
      )
    ).sort();
  }, [activities]);

  const statuses = useMemo(() => {
    return Array.from(
      new Set(
        activities
          .map((activity) => activity.status)
          .filter((value): value is string => Boolean(value))
      )
    ).sort();
  }, [activities]);

  const wbsLevels = useMemo(() => {
    return Array.from(
      new Set(
        activities
          .map((activity) => activity.wbs_level)
          .filter((value): value is string => Boolean(value))
      )
    ).sort();
  }, [activities]);

  const filteredActivities = useMemo(() => {
    const query = search.trim().toLowerCase();

    return activities.filter((activity) => {
      const matchesSearch =
        !query ||
        activity.activity_code?.toLowerCase().includes(query) ||
        activity.activity_name?.toLowerCase().includes(query) ||
        activity.discipline?.toLowerCase().includes(query) ||
        activity.area?.toLowerCase().includes(query);

      const matchesDiscipline =
        disciplineFilter === "all" ||
        activity.discipline === disciplineFilter;

      const matchesStatus =
        statusFilter === "all" || activity.status === statusFilter;

      const matchesWbs =
        wbsFilter === "all" || activity.wbs_level === wbsFilter;

      return (
        matchesSearch &&
        matchesDiscipline &&
        matchesStatus &&
        matchesWbs
      );
    });
  }, [
    activities,
    search,
    disciplineFilter,
    statusFilter,
    wbsFilter,
  ]);

  useEffect(() => {
    setCurrentPage(1);
  }, [
    search,
    disciplineFilter,
    statusFilter,
    wbsFilter,
  ]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredActivities.length / ITEMS_PER_PAGE)
  );

  const safeCurrentPage = Math.min(currentPage, totalPages);

  const paginatedActivities = useMemo(() => {
    const start =
      (safeCurrentPage - 1) * ITEMS_PER_PAGE;

    return filteredActivities.slice(
      start,
      start + ITEMS_PER_PAGE
    );
  }, [filteredActivities, safeCurrentPage]);

  const selectedProject = projects.find(
    (project) => project.id === selectedProjectId
  );

  const completedCount = activities.filter(
    (activity) => activity.status === "completed"
  ).length;

  const inProgressCount = activities.filter(
    (activity) => activity.status === "in_progress"
  ).length;

  const averageProgress =
    activities.length > 0
      ? activities.reduce(
          (sum, activity) =>
            sum +
            Math.min(
              Math.max(
                activity.actual_progress ?? 0,
                0
              ),
              100
            ),
          0
        ) / activities.length
      : 0;

  function formatDate(value: string | null | undefined) {
    if (!value) {
      return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return value;
    }

    return new Intl.DateTimeFormat("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    }).format(date);
  }

  function formatStatus(status: string) {
    return status
      .replaceAll("_", " ")
      .replace(/\b\w/g, (letter) => letter.toUpperCase());
  }

  function statusClass(status: string) {
    const normalized = status.toLowerCase();

    if (normalized === "completed") {
      return "schedule-v1-completed";
    }

    if (normalized === "in_progress") {
      return "schedule-v1-progress";
    }

    if (normalized === "not_started") {
      return "schedule-v1-not-started";
    }

    if (
      normalized.includes("delay") ||
      normalized.includes("risk")
    ) {
      return "schedule-v1-danger";
    }

    return "schedule-v1-default";
  }

  function clearFilters() {
    setSearch("");
    setDisciplineFilter("all");
    setStatusFilter("all");
    setWbsFilter("all");
  }

  const hasFilters =
    search !== "" ||
    disciplineFilter !== "all" ||
    statusFilter !== "all" ||
    wbsFilter !== "all";

  function getExtension(filename: string) {
    const index = filename.lastIndexOf(".");

    if (index === -1) {
      return "";
    }

    return filename.slice(index).toLowerCase();
  }

  function formatFileSize(bytes: number) {
    if (bytes < 1024) {
      return `${bytes} B`;
    }

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  function resetImport() {
    setSelectedFile(null);
    setPreview(null);
    setImportResult(null);
    setImportError("");
    setIsDragging(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function openImporter() {
    resetImport();
    setImportOpen(true);
  }

  function closeImporter() {
    resetImport();
    setImportOpen(false);
  }

  function selectScheduleFile(file: File) {
    setImportError("");
    setPreview(null);
    setImportResult(null);

    const extension = getExtension(file.name);

    if (!ALLOWED_EXTENSIONS.includes(extension)) {
      setSelectedFile(null);
      setImportError(
        "Unsupported file format. Upload Primavera P6 (.xer), Excel (.xlsx), or CSV (.csv)."
      );
      return;
    }

    if (file.size > MAX_FILE_SIZE) {
      setSelectedFile(null);
      setImportError(
        "The selected file exceeds the 50 MB limit."
      );
      return;
    }

    setSelectedFile(file);
  }

  async function handlePreview() {
    if (!selectedProjectId || !selectedFile) {
      return;
    }

    try {
      setPreviewing(true);
      setImportError("");
      setImportResult(null);

      const response = await previewScheduleImport(
        selectedProjectId,
        selectedFile
      );

      setPreview(response);
    } catch (err) {
      console.error(err);
      setPreview(null);
      setImportError(getErrorMessage(err));
    } finally {
      setPreviewing(false);
    }
  }

  async function handleClearSchedule() {
    if (!selectedProjectId) {
      return;
    }

    try {
      setClearing(true);
      setClearError("");

      await clearProjectSchedule(
        selectedProjectId
      );

      setClearOpen(false);

      await refreshActivities(
        selectedProjectId,
        true
      );
    } catch (err) {
      console.error(err);
      setClearError(
        getErrorMessage(err)
      );
    } finally {
      setClearing(false);
    }
  }

  async function handleConfirmImport() {
    if (
      !selectedProjectId ||
      !selectedFile ||
      !preview ||
      !preview.valid
    ) {
      return;
    }

    try {
      setImporting(true);
      setImportError("");

      const response = await confirmScheduleImport(
        selectedProjectId,
        selectedFile
      );

      setImportResult(response);

      await refreshActivities(
        selectedProjectId,
        false
      );
    } catch (err) {
      console.error(err);
      setImportError(getErrorMessage(err));
    } finally {
      setImporting(false);
    }
  }

  return (
    <div className="schedule-v1-page">
      <section className="schedule-v1-toolbar">
        <div className="schedule-v1-project">
          <span>PROJECT</span>

          <select
            value={selectedProjectId}
            onChange={(event) =>
              setSelectedProjectId(
                event.target.value
              )
            }
            disabled={loadingProjects}
          >
            <option value="">
              {loadingProjects
                ? "Loading projects..."
                : "Select project"}
            </option>

            {projects.map((project) => (
              <option
                key={project.id}
                value={project.id}
              >
                {project.name}
              </option>
            ))}
          </select>
        </div>

        <div className="schedule-v1-toolbar-actions">
          {selectedProject && (
            <div className="schedule-v1-project-state">
              <span className="schedule-v1-live-dot" />
              Schedule loaded
              <strong>
                {activities.length.toLocaleString()}
              </strong>
              activities
            </div>
          )}

          {selectedProjectId &&
            activities.length > 0 && (
            <button
              type="button"
              className="schedule-v1-import-button"
              onClick={() => {
                setClearError("");
                setClearOpen(true);
              }}
            >
              <Trash2 size={16} />
              Clear Schedule
            </button>
          )}

          <button
            type="button"
            className="schedule-v1-import-button"
            disabled={!selectedProjectId}
            onClick={openImporter}
          >
            <UploadCloud size={16} />
            Import Schedule
          </button>
        </div>
      </section>

      {error && (
        <div className="schedule-v1-error">
          {error}
        </div>
      )}

      {!selectedProjectId && !error && (
        <div className="schedule-v1-empty">
          <div>
            <Layers3 size={25} />
          </div>

          <h3>Select a project</h3>

          <p>
            Choose a project above to open its
            planning and schedule workspace.
          </p>
        </div>
      )}

      {selectedProjectId &&
        loadingActivities && (
          <div className="schedule-v1-empty">
            <div className="spinner" />

            <h3>Loading schedule</h3>

            <p>
              Fetching project activities from
              the backend.
            </p>
          </div>
        )}

      {selectedProjectId &&
        !loadingActivities &&
        !error &&
        activities.length === 0 && (
          <div className="schedule-v1-empty">
            <Layers3 size={25} />

            <h3>No activities found</h3>

            <p>
              This project currently has no
              schedule activities.
            </p>

            <button
              type="button"
              className="schedule-v1-import-empty-button"
              onClick={openImporter}
            >
              <UploadCloud size={16} />
              Import First Schedule
            </button>
          </div>
        )}

      {selectedProjectId &&
        !loadingActivities &&
        !error &&
        activities.length > 0 && (
          <>
            <section className="schedule-v1-summary">
              <div>
                <span className="schedule-summary-icon blue">
                  <Layers3 size={17} />
                </span>

                <section>
                  <span>Total activities</span>
                  <strong>
                    {activities.length.toLocaleString()}
                  </strong>
                </section>
              </div>

              <div>
                <span className="schedule-summary-icon green">
                  <CheckCircle2 size={17} />
                </span>

                <section>
                  <span>Completed</span>
                  <strong>
                    {completedCount.toLocaleString()}
                  </strong>
                </section>
              </div>

              <div>
                <span className="schedule-summary-icon violet">
                  <Activity size={17} />
                </span>

                <section>
                  <span>In progress</span>
                  <strong>
                    {inProgressCount.toLocaleString()}
                  </strong>
                </section>
              </div>

              <div>
                <span className="schedule-summary-icon orange">
                  <Clock3 size={17} />
                </span>

                <section>
                  <span>
                    Average actual progress
                  </span>

                  <strong>
                    {averageProgress.toFixed(1)}%
                  </strong>
                </section>
              </div>
            </section>

            <section className="schedule-v1-workspace">
              <div className="schedule-v1-workspace-head">
                <div>
                  <span>PLANNING WORKSPACE</span>
                  <h2>
                    {selectedProject?.name}
                  </h2>
                </div>

                <div className="schedule-v1-result-count">
                  Showing{" "}
                  <strong>
                    {filteredActivities.length.toLocaleString()}
                  </strong>{" "}
                  activities
                </div>
              </div>

              <div className="schedule-v1-filters">
                <div className="schedule-v1-search">
                  <Search size={16} />

                  <input
                    value={search}
                    onChange={(event) =>
                      setSearch(
                        event.target.value
                      )
                    }
                    placeholder="Search activity, code, area..."
                  />
                </div>

                <div className="schedule-v1-filter-control">
                  <SlidersHorizontal size={14} />

                  <select
                    value={disciplineFilter}
                    onChange={(event) =>
                      setDisciplineFilter(
                        event.target.value
                      )
                    }
                  >
                    <option value="all">
                      All disciplines
                    </option>

                    {disciplines.map(
                      (discipline) => (
                        <option
                          key={discipline}
                          value={discipline}
                        >
                          {discipline}
                        </option>
                      )
                    )}
                  </select>
                </div>

                <div className="schedule-v1-filter-control">
                  <select
                    value={wbsFilter}
                    onChange={(event) =>
                      setWbsFilter(
                        event.target.value
                      )
                    }
                  >
                    <option value="all">
                      All WBS
                    </option>

                    {wbsLevels.map((level) => (
                      <option
                        key={level}
                        value={level}
                      >
                        WBS {level}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="schedule-v1-filter-control">
                  <select
                    value={statusFilter}
                    onChange={(event) =>
                      setStatusFilter(
                        event.target.value
                      )
                    }
                  >
                    <option value="all">
                      All statuses
                    </option>

                    {statuses.map((status) => (
                      <option
                        key={status}
                        value={status}
                      >
                        {formatStatus(status)}
                      </option>
                    ))}
                  </select>
                </div>

                {hasFilters && (
                  <button
                    className="schedule-v1-clear"
                    onClick={clearFilters}
                  >
                    Clear
                  </button>
                )}
              </div>

              <div className="schedule-v1-table-wrap">
                <table className="schedule-v1-table">
                  <thead>
                    <tr>
                      <th>Activity</th>
                      <th>WBS</th>
                      <th>Discipline</th>
                      <th>Area</th>
                      <th>Planned window</th>
                      <th>Actual progress</th>
                      <th>Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {paginatedActivities.map(
                      (activity) => {
                        const progress =
                          Math.min(
                            Math.max(
                              activity.actual_progress ?? 0,
                              0
                            ),
                            100
                          );

                        return (
                          <tr key={activity.id}>
                            <td>
                              <div className="schedule-v1-activity">
                                <strong>
                                  {activity.activity_code}
                                </strong>

                                <span>
                                  {activity.activity_name}
                                </span>
                              </div>
                            </td>

                            <td>
                              <span className="schedule-v1-wbs">
                                {activity.wbs_level ||
                                  "—"}
                              </span>
                            </td>

                            <td>
                              {activity.discipline ||
                                "—"}
                            </td>

                            <td>
                              {activity.area || "—"}
                            </td>

                            <td>
                              <div className="schedule-v1-dates">
                                <span>
                                  {formatDate(
                                    activity.planned_start
                                  )}
                                </span>

                                <small>→</small>

                                <span>
                                  {formatDate(
                                    activity.planned_finish
                                  )}
                                </span>
                              </div>
                            </td>

                            <td>
                              <div className="schedule-v1-progress-wrap">
                                <div>
                                  <span>
                                    {progress.toFixed(1)}%
                                  </span>
                                </div>

                                <div className="schedule-v1-progress-track">
                                  <div
                                    className="schedule-v1-progress-fill"
                                    style={{
                                      width: `${progress}%`,
                                    }}
                                  />
                                </div>
                              </div>
                            </td>

                            <td>
                              <span
                                className={`schedule-v1-status ${statusClass(
                                  activity.status
                                )}`}
                              >
                                {formatStatus(
                                  activity.status
                                )}
                              </span>
                            </td>
                          </tr>
                        );
                      }
                    )}
                  </tbody>
                </table>

                {filteredActivities.length ===
                  0 && (
                  <div className="schedule-v1-no-results">
                    No activities match the
                    selected filters.
                  </div>
                )}
              </div>

              {filteredActivities.length >
                0 && (
                <div className="schedule-v1-pagination">
                  <span>
                    Showing{" "}
                    <strong>
                      {(safeCurrentPage - 1) *
                        ITEMS_PER_PAGE +
                        1}
                    </strong>{" "}
                    –{" "}
                    <strong>
                      {Math.min(
                        safeCurrentPage *
                          ITEMS_PER_PAGE,
                        filteredActivities.length
                      )}
                    </strong>{" "}
                    of{" "}
                    <strong>
                      {filteredActivities.length}
                    </strong>
                  </span>

                  <div>
                    <button
                      onClick={() =>
                        setCurrentPage((page) =>
                          Math.max(1, page - 1)
                        )
                      }
                      disabled={
                        safeCurrentPage === 1
                      }
                    >
                      <ChevronLeft size={16} />
                    </button>

                    <span>
                      Page {safeCurrentPage} /{" "}
                      {totalPages}
                    </span>

                    <button
                      onClick={() =>
                        setCurrentPage((page) =>
                          Math.min(
                            totalPages,
                            page + 1
                          )
                        )
                      }
                      disabled={
                        safeCurrentPage ===
                        totalPages
                      }
                    >
                      <ChevronRight size={16} />
                    </button>
                  </div>
                </div>
              )}
            </section>
          </>
        )}

      {clearOpen && (
        <div
          className="schedule-v1-import-backdrop"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget &&
              !clearing
            ) {
              setClearOpen(false);
              setClearError("");
            }
          }}
        >
          <div className="schedule-v1-import-modal">
            <div className="schedule-v1-import-head">
              <div>
                <span>SCHEDULE MANAGEMENT</span>

                <h2>Clear Project Schedule</h2>

                <p>
                  Remove the schedule activities
                  and activity relationships from
                  this project.
                </p>
              </div>

              <button
                type="button"
                className="schedule-v1-import-close"
                disabled={clearing}
                onClick={() => {
                  setClearOpen(false);
                  setClearError("");
                }}
              >
                <X size={18} />
              </button>
            </div>

            <div className="schedule-v1-import-project">
              <div>
                <span>SELECTED PROJECT</span>

                <strong>
                  {selectedProject?.name ||
                    "Selected project"}
                </strong>
              </div>

              <div className="schedule-v1-import-formats">
                <span>
                  <AlertTriangle size={14} />
                  {activities.length.toLocaleString()} activities
                </span>
              </div>
            </div>

            <div className="schedule-v1-import-error">
              <strong>
                This action is permanent.
              </strong>

              <span>
                The backend will refuse to clear
                the schedule if field execution
                history or exception records
                already depend on it.
              </span>
            </div>

            {clearError && (
              <div className="schedule-v1-import-error">
                <strong>
                  Unable to clear schedule
                </strong>

                <span>
                  {clearError}
                </span>
              </div>
            )}

            <div className="schedule-v1-import-actions">
              <button
                type="button"
                className="secondary"
                disabled={clearing}
                onClick={() => {
                  setClearOpen(false);
                  setClearError("");
                }}
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary"
                disabled={clearing}
                onClick={handleClearSchedule}
              >
                {clearing
                  ? "Clearing..."
                  : "Clear Schedule"}
              </button>
            </div>
          </div>
        </div>
      )}

      {importOpen && (
        <div
          className="schedule-v1-import-backdrop"
          onMouseDown={(event) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              closeImporter();
            }
          }}
        >
          <div className="schedule-v1-import-modal">
            <div className="schedule-v1-import-head">
              <div>
                <span>SCHEDULE INGESTION</span>

                <h2>
                  Import Project Schedule
                </h2>

                <p>
                  Import a planning schedule
                  and normalize it into the
                  execution model.
                </p>
              </div>

              <button
                type="button"
                onClick={closeImporter}
                className="schedule-v1-import-close"
              >
                <X size={18} />
              </button>
            </div>

            <div className="schedule-v1-import-project">
              <div>
                <span>IMPORTING INTO</span>

                <strong>
                  {selectedProject?.name ||
                    "Selected project"}
                </strong>
              </div>

              <div className="schedule-v1-import-formats">
                <span>
                  Primavera P6
                  <strong>.XER</strong>
                </span>

                <span>
                  Excel
                  <strong>.XLSX</strong>
                </span>

                <span>
                  CSV
                  <strong>.CSV</strong>
                </span>
              </div>
            </div>

            {!importResult && (
              <>
                <div
                  className={`schedule-v1-import-drop ${
                    isDragging
                      ? "dragging"
                      : ""
                  }`}
                  onDragOver={(event) => {
                    event.preventDefault();
                    setIsDragging(true);
                  }}
                  onDragLeave={() =>
                    setIsDragging(false)
                  }
                  onDrop={(event) => {
                    event.preventDefault();
                    setIsDragging(false);

                    const file =
                      event.dataTransfer.files?.[0];

                    if (file) {
                      selectScheduleFile(file);
                    }
                  }}
                  onClick={() =>
                    fileInputRef.current?.click()
                  }
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".xer,.xlsx,.csv"
                    hidden
                    onChange={(event) => {
                      const file =
                        event.target.files?.[0];

                      if (file) {
                        selectScheduleFile(file);
                      }
                    }}
                  />

                  <div className="schedule-v1-import-upload-icon">
                    <UploadCloud size={25} />
                  </div>

                  <strong>
                    Drop your schedule file here
                  </strong>

                  <p>
                    or click to browse from your
                    computer
                  </p>

                  <small>
                    Primavera P6 XER, Excel XLSX
                    or CSV • Max 50 MB
                  </small>
                </div>

                {selectedFile && (
                  <div className="schedule-v1-import-file">
                    <div>
                      <FileSpreadsheet
                        size={20}
                      />
                    </div>

                    <section>
                      <strong>
                        {selectedFile.name}
                      </strong>

                      <span>
                        {formatFileSize(
                          selectedFile.size
                        )}
                      </span>
                    </section>

                    <button
                      type="button"
                      onClick={(event) => {
                        event.stopPropagation();
                        resetImport();
                      }}
                    >
                      Remove
                    </button>
                  </div>
                )}

                {importError && (
                  <div className="schedule-v1-import-error">
                    <strong>
                      Import error
                    </strong>

                    <span>
                      {importError}
                    </span>
                  </div>
                )}

                {selectedFile && !preview && (
                  <div className="schedule-v1-import-actions">
                    <button
                      type="button"
                      className="secondary"
                      onClick={resetImport}
                    >
                      Choose Another
                    </button>

                    <button
                      type="button"
                      className="primary"
                      disabled={previewing}
                      onClick={handlePreview}
                    >
                      {previewing
                        ? "Analyzing..."
                        : "Preview Schedule"}
                    </button>
                  </div>
                )}

                {preview && (
                  <div className="schedule-v1-preview">
                    <div className="schedule-v1-preview-title">
                      <div>
                        <span>
                          VALIDATION RESULT
                        </span>

                        <h3>
                          Schedule Preview
                        </h3>
                      </div>

                      <div
                        className={
                          preview.valid
                            ? "schedule-v1-preview-valid"
                            : "schedule-v1-preview-invalid"
                        }
                      >
                        {preview.valid
                          ? "Ready to import"
                          : "Validation failed"}
                      </div>
                    </div>

                    <div className="schedule-v1-preview-stats">
                      <div>
                        <span>Activities</span>
                        <strong>
                          {preview.summary.activities}
                        </strong>
                      </div>

                      <div>
                        <span>New</span>
                        <strong>
                          {preview.summary.new_activities}
                        </strong>
                      </div>

                      <div>
                        <span>Existing</span>
                        <strong>
                          {preview.summary.existing_activities}
                        </strong>
                      </div>

                      <div>
                        <span>Relationships</span>
                        <strong>
                          {preview.summary.dependencies}
                        </strong>
                      </div>

                      <div>
                        <span>Errors</span>
                        <strong>
                          {preview.summary.errors}
                        </strong>
                      </div>

                      <div>
                        <span>Warnings</span>
                        <strong>
                          {preview.summary.warnings}
                        </strong>
                      </div>
                    </div>

                    {preview.errors.length >
                      0 && (
                      <div className="schedule-v1-preview-issues error">
                        <strong>
                          Validation Errors
                        </strong>

                        {preview.errors.map(
                          (issue, index) => (
                            <p key={index}>
                              {issue.row
                                ? `Row ${issue.row}: `
                                : ""}
                              {issue.message}
                            </p>
                          )
                        )}
                      </div>
                    )}

                    {preview.warnings.length >
                      0 && (
                      <div className="schedule-v1-preview-issues warning">
                        <strong>
                          Warnings
                        </strong>

                        {preview.warnings.map(
                          (issue, index) => (
                            <p key={index}>
                              {issue.row
                                ? `Row ${issue.row}: `
                                : ""}
                              {issue.message}
                            </p>
                          )
                        )}
                      </div>
                    )}

                    <div className="schedule-v1-preview-table-wrap">
                      <table className="schedule-v1-preview-table">
                        <thead>
                          <tr>
                            <th>Activity</th>
                            <th>WBS</th>
                            <th>Discipline</th>
                            <th>Start</th>
                            <th>Finish</th>
                            <th>Quantity</th>
                          </tr>
                        </thead>

                        <tbody>
                          {preview.activities_preview.map(
                            (activity, index) => (
                              <tr
                                key={`${activity.activity_code}-${index}`}
                              >
                                <td>
                                  <strong>
                                    {activity.activity_code}
                                  </strong>

                                  <span>
                                    {activity.activity_name}
                                  </span>
                                </td>

                                <td>
                                  {activity.wbs_level ||
                                    "—"}
                                </td>

                                <td>
                                  {activity.discipline ||
                                    "—"}
                                </td>

                                <td>
                                  {formatDate(
                                    activity.planned_start
                                  )}
                                </td>

                                <td>
                                  {formatDate(
                                    activity.planned_finish
                                  )}
                                </td>

                                <td>
                                  {activity.planned_quantity ??
                                    "—"}

                                  {activity.quantity_unit
                                    ? ` ${activity.quantity_unit}`
                                    : ""}
                                </td>
                              </tr>
                            )
                          )}
                        </tbody>
                      </table>
                    </div>

                    {preview
                      .dependencies_preview
                      .length > 0 && (
                      <details className="schedule-v1-preview-relations">
                        <summary>
                          View{" "}
                          {preview.summary.dependencies}{" "}
                          activity relationships
                        </summary>

                        <div>
                          {preview.dependencies_preview.map(
                            (
                              dependency,
                              index
                            ) => (
                              <section
                                key={index}
                              >
                                <strong>
                                  {dependency.predecessor_code}
                                </strong>

                                <span>
                                  {dependency.dependency_type}

                                  {dependency.lag_days !==
                                    0 &&
                                    ` ${
                                      dependency.lag_days >
                                      0
                                        ? "+"
                                        : ""
                                    }${dependency.lag_days}d`}
                                </span>

                                <strong>
                                  {dependency.successor_code}
                                </strong>
                              </section>
                            )
                          )}
                        </div>
                      </details>
                    )}

                    <div className="schedule-v1-import-actions">
                      <button
                        type="button"
                        className="secondary"
                        disabled={importing}
                        onClick={resetImport}
                      >
                        Choose Another
                      </button>

                      <button
                        type="button"
                        className="primary"
                        disabled={
                          !preview.valid ||
                          importing
                        }
                        onClick={
                          handleConfirmImport
                        }
                      >
                        {importing
                          ? "Importing..."
                          : `Confirm Import (${preview.summary.new_activities} New)`}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}

            {importResult && (
              <div className="schedule-v1-import-success">
                <div>
                  <CheckCircle2 size={30} />
                </div>

                <span>IMPORT COMPLETE</span>

                <h3>
                  Schedule synchronized
                </h3>

                <p>
                  The planning schedule has
                  been normalized into the
                  project execution model.
                </p>

                <section className="schedule-v1-import-result">
                  <div>
                    <strong>
                      {
                        importResult.summary
                          .activities_inserted
                      }
                    </strong>

                    <span>
                      Activities added
                    </span>
                  </div>

                  <div>
                    <strong>
                      {
                        importResult.summary
                          .activities_skipped_existing
                      }
                    </strong>

                    <span>
                      Existing protected
                    </span>
                  </div>

                  <div>
                    <strong>
                      {
                        importResult.summary
                          .dependencies_inserted
                      }
                    </strong>

                    <span>
                      Relationships added
                    </span>
                  </div>

                  <div>
                    <strong>
                      {
                        importResult.summary
                          .dependencies_unresolved
                      }
                    </strong>

                    <span>
                      Unresolved
                    </span>
                  </div>
                </section>

                <button
                  type="button"
                  className="schedule-v1-import-success-button"
                  onClick={closeImporter}
                >
                  View Updated Schedule
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}