import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  cleanupStale,
  clearAdminToken,
  deleteUser,
  getAdminUsers,
  getStaleUsers,
} from "../adminApi";
import type { AdminUserSummary } from "../adminApi";

const STALE_LABEL: Record<string, string> = {
  abandoned: "Abandoned",
  inactive: "Inactive",
};

function fmtDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function AdminPage() {
  const navigate = useNavigate();
  const [users, setUsers] = useState<AdminUserSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  const [stalePreview, setStalePreview] = useState<AdminUserSummary[] | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [cleaning, setCleaning] = useState(false);

  async function loadUsers() {
    setLoading(true);
    setError(null);
    try {
      setUsers(await getAdminUsers());
    } catch {
      setError("Failed to load users.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadUsers();
  }, []);

  function handleLogout() {
    clearAdminToken();
    navigate("/admin/login", { replace: true });
  }

  async function handleDelete(user: AdminUserSummary) {
    if (
      !window.confirm(
        `Delete ${user.email}? This permanently removes the account and all its data.`,
      )
    ) {
      return;
    }
    setBusyId(user.id);
    setError(null);
    try {
      await deleteUser(user.id);
      setStalePreview(null);
      await loadUsers();
    } catch {
      setError(`Failed to delete ${user.email}.`);
    } finally {
      setBusyId(null);
    }
  }

  async function handlePreviewStale() {
    setPreviewing(true);
    setError(null);
    try {
      setStalePreview(await getStaleUsers());
    } catch {
      setError("Failed to load stale accounts.");
    } finally {
      setPreviewing(false);
    }
  }

  async function handleCleanup() {
    if (!stalePreview || stalePreview.length === 0) return;
    if (
      !window.confirm(
        `Permanently delete ${stalePreview.length} stale account(s)? This cannot be undone.`,
      )
    ) {
      return;
    }
    setCleaning(true);
    setError(null);
    try {
      const result = await cleanupStale();
      setStalePreview(null);
      await loadUsers();
      window.alert(`Deleted ${result.deleted_count} account(s).`);
    } catch {
      setError("Cleanup failed.");
    } finally {
      setCleaning(false);
    }
  }

  return (
    <div className="page page-dashboard">
      <div className="page-inner">
        <header className="header">
          <div>
            <h1>Admin</h1>
            <p className="subtitle">User management</p>
          </div>
          <div className="header-actions">
            <button type="button" className="btn secondary" onClick={handleLogout}>
              Log out
            </button>
          </div>
        </header>

        {error && <p className="error">{error}</p>}

        <section className="card section-gap">
          <div className="header" style={{ marginBottom: "1rem" }}>
            <h2 className="section-title" style={{ margin: 0 }}>
              Stale accounts
            </h2>
            <div className="header-actions">
              <button
                type="button"
                className="btn secondary"
                onClick={handlePreviewStale}
                disabled={previewing}
              >
                {previewing ? "Loading..." : "Preview stale accounts"}
              </button>
              {stalePreview && stalePreview.length > 0 && (
                <button
                  type="button"
                  className="btn primary"
                  onClick={handleCleanup}
                  disabled={cleaning}
                >
                  {cleaning
                    ? "Deleting..."
                    : `Delete ${stalePreview.length} stale account(s)`}
                </button>
              )}
            </div>
          </div>

          {stalePreview === null ? (
            <p className="muted">
              Abandoned (no consent, &gt;30 days) or inactive (no activity, &gt;90 days)
              accounts. Preview before deleting.
            </p>
          ) : stalePreview.length === 0 ? (
            <p className="muted">No stale accounts found.</p>
          ) : (
            <ul className="log-list">
              {stalePreview.map((u) => (
                <li key={u.id} className="log-item">
                  <strong>{u.email}</strong>
                  <span className="badge">{STALE_LABEL[u.stale_reason ?? ""] ?? "Stale"}</span>
                  <span className="muted">joined {fmtDate(u.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section className="card">
          <h2 className="section-title">All users</h2>
          {loading ? (
            <p className="muted">Loading...</p>
          ) : users.length === 0 ? (
            <p className="muted">No users.</p>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Email</th>
                    <th>Name</th>
                    <th>Joined</th>
                    <th>Consent</th>
                    <th>Workouts</th>
                    <th>Metrics</th>
                    <th>Status</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td>{u.email}</td>
                      <td>{u.name}</td>
                      <td>{fmtDate(u.created_at)}</td>
                      <td>{u.consent_accepted_at ? "✓" : "—"}</td>
                      <td>{u.workout_count}</td>
                      <td>{u.body_metrics_count}</td>
                      <td>
                        {u.is_stale ? (
                          <span className="badge">
                            {STALE_LABEL[u.stale_reason ?? ""] ?? "Stale"}
                          </span>
                        ) : (
                          <span className="muted">Active</span>
                        )}
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn secondary btn-compact"
                          onClick={() => handleDelete(u)}
                          disabled={busyId === u.id}
                        >
                          {busyId === u.id ? "..." : "Delete"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
