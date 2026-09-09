import {
    AlertTriangle,
    Bell,
    ClipboardCheck,
    FileClock,
    LayoutDashboard,
    LogOut,
    Menu,
    Network,
    Route,
    Search,
    Sparkles,
    X,
  } from "lucide-react";
  
  import {
    NavLink,
    Outlet,
    useLocation,
    useNavigate,
  } from "react-router-dom";
  
  import { useState } from "react";
  
  import {
    getStoredProfile,
    logout,
  } from "../services/authService";
  
  const navigation = [
    {
      name: "Dashboard",
      path: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Schedule",
      path: "/schedule",
      icon: Route,
    },
    {
      name: "Field Twin",
      path: "/field-twin",
      icon: Network,
    },
    {
      name: "Review Queue",
      path: "/review-queue",
      icon: ClipboardCheck,
    },
    {
      name: "Exceptions",
      path: "/exceptions",
      icon: AlertTriangle,
    },
    {
      name: "Audit Trail",
      path: "/audit-trail",
      icon: FileClock,
    },
  ];
  
  const pageMeta: Record<
    string,
    {
      title: string;
      subtitle: string;
    }
  > = {
    "/dashboard": {
      title: "Project Overview",
      subtitle: "Monitor execution health and field progress.",
    },
  
    "/schedule": {
      title: "Schedule Intelligence",
      subtitle: "Track planned and actual execution across L5/L6 activities.",
    },
  
    "/field-twin": {
      title: "Field Execution Twin",
      subtitle: "Visualize real-world execution against the project schedule.",
    },
  
    "/review-queue": {
      title: "AI Review Queue",
      subtitle: "Validate field evidence before updating official progress.",
    },
  
    "/exceptions": {
      title: "Exceptions",
      subtitle: "Identify execution deviations, risks and unresolved issues.",
    },
  
    "/audit-trail": {
      title: "Audit Trail",
      subtitle: "Trace every decision, update and approval.",
    },
  };
  
  export default function AppLayout() {
    const navigate = useNavigate();
    const location = useLocation();
  
    const profile = getStoredProfile();
  
    const [mobileOpen, setMobileOpen] = useState(false);
  
    const currentMeta =
      pageMeta[location.pathname] ?? {
        title: "Field Progress",
        subtitle: "Execution Intelligence Platform",
      };
  
    function handleLogout() {
      logout();
      navigate("/login");
    }
  
    const initials =
      profile?.full_name
        ?.split(" ")
        .map((part: string) => part[0])
        .join("")
        .slice(0, 2)
        .toUpperCase() || "FP";
  
    return (
      <div className="app-shell">
        {mobileOpen && (
          <button
            className="sidebar-overlay"
            onClick={() => setMobileOpen(false)}
            aria-label="Close navigation"
          />
        )}
  
        <aside
          className={`app-sidebar ${mobileOpen ? "sidebar-open" : ""}`}
        >
          <div className="sidebar-brand">
            <div className="brand-mark">
              <Sparkles size={22} strokeWidth={2.1} />
            </div>
  
            <div className="brand-copy">
              <span className="brand-name">Field Progress</span>
              <span className="brand-subtitle">
                Execution Intelligence
              </span>
            </div>
  
            <button
              className="mobile-sidebar-close"
              onClick={() => setMobileOpen(false)}
            >
              <X size={20} />
            </button>
          </div>
  
          <div className="sidebar-project-label">
            WORKSPACE
          </div>
  
          <nav className="sidebar-navigation">
            {navigation.map((item) => {
              const Icon = item.icon;
  
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setMobileOpen(false)}
                  className={({ isActive }) =>
                    `sidebar-nav-item ${
                      isActive ? "sidebar-nav-active" : ""
                    }`
                  }
                >
                  <span className="sidebar-icon">
                    <Icon size={18} strokeWidth={2} />
                  </span>
  
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>
  
          <div className="sidebar-ai-panel">
            <div className="sidebar-ai-icon">
              <Sparkles size={17} />
            </div>
  
            <div>
              <strong>AI Intelligence</strong>
              <span>
                Field evidence → schedule insight
              </span>
            </div>
          </div>
  
          <div className="sidebar-user">
            <div className="sidebar-avatar">
              {initials}
            </div>
  
            <div className="sidebar-user-info">
              <strong>{profile?.full_name || "User"}</strong>
              <span>{profile?.role || "Planner"}</span>
            </div>
  
            <button
              className="sidebar-logout"
              onClick={handleLogout}
              title="Logout"
            >
              <LogOut size={17} />
            </button>
          </div>
        </aside>
  
        <main className="app-main">
          <header className="app-topbar">
            <div className="topbar-left">
              <button
                className="mobile-menu-button"
                onClick={() => setMobileOpen(true)}
              >
                <Menu size={21} />
              </button>
  
              <div>
                <div className="page-heading-row">
                  <h1>{currentMeta.title}</h1>
  
                  <span className="live-status-pill">
                    <span className="live-status-dot" />
                    Live
                  </span>
                </div>
  
                <p>{currentMeta.subtitle}</p>
              </div>
            </div>
  
            <div className="topbar-actions">
              <div className="topbar-search">
                <Search size={17} />
  
                <input
                  type="text"
                  placeholder="Search workspace..."
                />
              </div>
  
              <button
                className="topbar-icon-button"
                aria-label="Notifications"
              >
                <Bell size={18} />
                <span className="notification-dot" />
              </button>
  
              <div className="topbar-profile">
                <div className="topbar-profile-avatar">
                  {initials}
                </div>
  
                <div className="topbar-profile-copy">
                  <strong>
                    {profile?.full_name || "User"}
                  </strong>
  
                  <span>
                    {profile?.role || "Planner"}
                  </span>
                </div>
              </div>
            </div>
          </header>
  
          <div className="app-content">
            <Outlet />
          </div>
        </main>
      </div>
    );
  }