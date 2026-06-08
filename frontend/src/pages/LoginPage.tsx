import { useRef, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { getProfile, login, register, setToken } from "../api";

type AuthMode = "login" | "register";

function getApiErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    console.error(err.response?.data);

    const data = err.response?.data;
    if (typeof data === "string") {
      return data;
    }
    if (data && typeof data === "object" && "detail" in data) {
      const { detail } = data as { detail: unknown };
      if (typeof detail === "string") {
        return detail;
      }
      if (Array.isArray(detail)) {
        return detail
          .map((item) => {
            if (typeof item === "string") return item;
            if (item && typeof item === "object" && "msg" in item) {
              return String((item as { msg: string }).msg);
            }
            return JSON.stringify(item);
          })
          .join("; ");
      }
    }
    if (data) {
      return JSON.stringify(data);
    }
  }

  if (err instanceof Error) {
    return err.message;
  }

  return "Authentication failed. Check your credentials.";
}

export default function LoginPage() {
  const navigate = useNavigate();
  const loginSectionRef = useRef<HTMLElement>(null);
  const [mode, setMode] = useState<AuthMode>("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  function scrollToLogin() {
    loginSectionRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "register") {
        await register(email, password, name);
        const tokenResponse = await login(email, password);
        setToken(tokenResponse.access_token);
        navigate("/onboarding");
        return;
      }

      const tokenResponse = await login(email, password);
      setToken(tokenResponse.access_token);

      try {
        const profile = await getProfile();
        navigate(profile.profile_completeness === 0 ? "/onboarding" : "/");
      } catch {
        navigate("/");
      }
    } catch (err: unknown) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="landing-page">
      <div className="landing-main">
      <section className="landing-hero">
        <div className="landing-hero-inner">
          <div className="landing-monogram" aria-hidden="true">
            FS
          </div>

          <h1 className="landing-headline">Train like I programmed it.</h1>
          <p className="landing-subline">Because I did.</p>

          <p className="landing-body">
            FitStack is built on the same methodology behind GleamDiva — now
            personalized to you by AI, available 24/7.
          </p>

          <ul className="landing-props">
            <li>Real coaching methodology. Not generic AI advice.</li>
            <li>Personalized to your body, goals, and experience.</li>
            <li>Medical safety layer. Programming that knows your limits.</li>
          </ul>

          <p className="landing-coming-soon">
            Diet plans · Supplement guidance · Progress analytics
          </p>

          <div className="landing-cta-group">
            <button
              type="button"
              className="landing-scroll-cta"
              onClick={scrollToLogin}
            >
              Get started
            </button>
            <span className="landing-scroll-arrow" aria-hidden="true" />
          </div>
        </div>
      </section>

      <section
        ref={loginSectionRef}
        id="login"
        className="landing-auth-section"
      >
        <div className="landing-auth-card">
          <h2 className="landing-auth-heading">
            {mode === "login" ? "Welcome back" : "Join FitStack"}
          </h2>

          <div className="tabs">
            <button
              type="button"
              className={mode === "login" ? "tab active" : "tab"}
              onClick={() => setMode("login")}
            >
              Login
            </button>
            <button
              type="button"
              className={mode === "register" ? "tab active" : "tab"}
              onClick={() => setMode("register")}
            >
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="form">
            {mode === "register" && (
              <label>
                Name
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="Your name"
                />
              </label>
            )}

            <label>
              Email
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                placeholder="Min 8 characters"
              />
            </label>

            {error && <p className="error">{error}</p>}

            <button type="submit" className="btn primary" disabled={loading}>
              {loading
                ? "Please wait..."
                : mode === "login"
                  ? "Login"
                  : "Register & Login"}
            </button>
          </form>
        </div>
      </section>
      </div>

      <footer className="landing-footer">
        © FitStack · Built by Rajat Joshi
      </footer>
    </div>
  );
}
