import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Eye,
  EyeOff,
  Layers3,
  Sparkles,
} from "lucide-react";

import {
  getStoredProfile,
  login,
  logout,
} from "../services/authService";

export default function Login() {
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault();

    setError("");
    setLoading(true);

    try {
      await login(email, password);

      const profile = getStoredProfile();

      if (
        profile?.role !== "planner" &&
        profile?.role !== "reviewer"
      ) {
        logout();

        setError(
          "This portal is available only to planners and reviewers.",
        );

        return;
      }

      sessionStorage.removeItem(
        "field-progress-dashboard-project-id",
      );

      navigate("/dashboard");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to sign in. Please check your credentials.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <section className="login-visual">
        <div className="login-visual-glow login-glow-one" />
        <div className="login-visual-glow login-glow-two" />

        <div className="login-brand">
          <div className="login-brand-mark">
            <Layers3 size={24} strokeWidth={2.2} />
          </div>

          <div>
            <strong>Field Progress</strong>
            <span>Execution Intelligence Platform</span>
          </div>
        </div>

        <div className="login-hero">
          <div className="login-eyebrow">
            <Sparkles size={14} />
            AI-POWERED FIELD INTELLIGENCE
          </div>

          <h1>
            From Field Reality
            <br />
            to{" "}
            <span>
              Measurable
              <br />
              Progress.
            </span>
          </h1>

          <p>
            Bridge real on-site execution with the official
            project schedule through intelligent evidence
            capture, matching and validation.
          </p>

          <div className="login-capabilities">
            <div className="login-capability">
              <div>
                <Layers3 size={18} />
              </div>

              <span>
                <strong>Capture</strong>
                Field evidence
              </span>
            </div>

            <div className="login-capability">
              <div>
                <Sparkles size={18} />
              </div>

              <span>
                <strong>Interpret</strong>
                With AI
              </span>
            </div>

            <div className="login-capability">
              <div>
                <BarChart3 size={18} />
              </div>

              <span>
                <strong>Track</strong>
                Real progress
              </span>
            </div>
          </div>
        </div>

        <div className="login-visual-footer">
          Real sites. Real data. Real progress.
        </div>
      </section>

      <section className="login-form-side">
        <div className="login-form-wrapper">
          <div className="login-mobile-brand">
            <div className="login-brand-mark">
              <Layers3 size={21} />
            </div>

            <strong>Field Progress</strong>
          </div>

          <div className="login-form-heading">
            <div className="login-form-icon">
              <Sparkles size={18} />
            </div>

            <h2>Welcome back</h2>

            <p>
              Sign in to your planner or reviewer workspace.
            </p>
          </div>

          <form
            className="login-form"
            onSubmit={handleSubmit}
          >
            <label>
              <span>Email address</span>

              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@company.com"
                autoComplete="email"
                required
              />
            </label>

            <label>
              <span>Password</span>

              <div className="login-password-field">
                <input
                  type={
                    showPassword
                      ? "text"
                      : "password"
                  }
                  value={password}
                  onChange={(event) =>
                    setPassword(event.target.value)
                  }
                  placeholder="Enter your password"
                  autoComplete="current-password"
                  required
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword(
                      (current) => !current,
                    )
                  }
                  aria-label={
                    showPassword
                      ? "Hide password"
                      : "Show password"
                  }
                >
                  {showPassword ? (
                    <EyeOff size={17} />
                  ) : (
                    <Eye size={17} />
                  )}
                </button>
              </div>
            </label>

            {error && (
              <div className="login-error">
                {error}
              </div>
            )}

            <button
              className="login-submit"
              type="submit"
              disabled={loading}
            >
              {loading ? (
                "Signing in..."
              ) : (
                <>
                  Sign in
                  <ArrowRight size={17} />
                </>
              )}
            </button>
          </form>

          <div className="login-security-note">
            <CheckCircle2 size={14} />

            <span>
              Authorized project stakeholders only
            </span>
          </div>
        </div>
      </section>
    </div>
  );
}
