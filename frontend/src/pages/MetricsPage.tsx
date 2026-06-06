import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { addBodyMetrics, getBodyMetrics } from "../api";
import type { BodyMetricsEntry } from "../api";

function fmt(value: number | null, suffix: string): string {
  if (value === null || value === undefined) return "—";
  return `${value}${suffix}`;
}

export default function MetricsPage() {
  const [history, setHistory] = useState<BodyMetricsEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const [weightKg, setWeightKg] = useState("");
  const [bodyFatPct, setBodyFatPct] = useState("");
  const [waistCm, setWaistCm] = useState("");
  const [hipCm, setHipCm] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  async function loadHistory() {
    try {
      const data = await getBodyMetrics();
      setHistory(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadHistory();
  }, []);

  const hasAnyInput = weightKg || bodyFatPct || waistCm || hipCm;

  function validate(): string | null {
    const w = parseFloat(weightKg);
    const bf = parseFloat(bodyFatPct);
    const wa = parseFloat(waistCm);
    const h = parseFloat(hipCm);
    if (weightKg && (w < 20 || w > 300)) return "Weight must be 20–300 kg.";
    if (bodyFatPct && (bf < 3 || bf > 60)) return "Body fat must be 3–60%.";
    if (waistCm && (wa < 30 || wa > 250)) return "Waist must be 30–250 cm.";
    if (hipCm && (h < 30 || h > 250)) return "Hip must be 30–250 cm.";
    return null;
  }

  async function handleSubmit() {
    const vErr = validate();
    if (vErr) { setValidationError(vErr); return; }
    setValidationError(null);
    setError(null);
    setSubmitting(true);
    try {
      await addBodyMetrics({
        weight_kg: weightKg ? parseFloat(weightKg) : undefined,
        body_fat_pct: bodyFatPct ? parseFloat(bodyFatPct) : undefined,
        waist_cm: waistCm ? parseFloat(waistCm) : undefined,
        hip_cm: hipCm ? parseFloat(hipCm) : undefined,
      });
      setWeightKg("");
      setBodyFatPct("");
      setWaistCm("");
      setHipCm("");
      await loadHistory();
    } catch {
      setError("Failed to log entry. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="page page-dashboard">
      <div className="page-inner">
        <Link to="/" className="back-link">
          &larr; Back
        </Link>

        <header className="header">
          <div>
            <h1>Body Metrics</h1>
            <p className="subtitle">Track your measurements over time</p>
          </div>
        </header>

        <div className="card form section-gap">
          <h2>Log Weigh-In</h2>

          <div className="form-row">
            <label>
              Weight (kg)
              <input
                type="number"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                placeholder="82.5"
                min={20}
                max={300}
                step={0.1}
              />
            </label>
            <label>
              Body fat (%)
              <input
                type="number"
                value={bodyFatPct}
                onChange={(e) => setBodyFatPct(e.target.value)}
                placeholder="17"
                min={3}
                max={60}
                step={0.1}
              />
            </label>
          </div>

          <div className="form-row">
            <label>
              Waist (cm)
              <input
                type="number"
                value={waistCm}
                onChange={(e) => setWaistCm(e.target.value)}
                placeholder="80"
                min={30}
                max={250}
                step={0.1}
              />
            </label>
            <label>
              Hip (cm)
              <input
                type="number"
                value={hipCm}
                onChange={(e) => setHipCm(e.target.value)}
                placeholder="95"
                min={30}
                max={250}
                step={0.1}
              />
            </label>
          </div>

          {validationError && <p className="error">{validationError}</p>}
          {error && <p className="error">{error}</p>}

          <button
            type="button"
            className="btn primary"
            disabled={!hasAnyInput || submitting}
            onClick={handleSubmit}
          >
            {submitting ? "Logging…" : "Log Entry"}
          </button>
        </div>

        <div className="card">
          <h2 className="section-title">History</h2>

          {loading ? (
            <p className="muted">Loading…</p>
          ) : history.length === 0 ? (
            <p className="muted">No entries yet. Log your first weigh-in above.</p>
          ) : (
            <div>
              {history.map((entry) => {
                const parts: string[] = [];
                if (entry.weight_kg !== null) parts.push(fmt(entry.weight_kg, " kg"));
                if (entry.body_fat_pct !== null) parts.push(fmt(entry.body_fat_pct, "%"));
                if (entry.waist_cm !== null || entry.hip_cm !== null) {
                  parts.push(`${fmt(entry.waist_cm, " cm")} waist`);
                  parts.push(`${fmt(entry.hip_cm, " cm")} hip`);
                }
                const display = parts.length > 0 ? parts.join(" · ") : "—";

                return (
                  <div key={entry.id} className="metrics-row">
                    <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                      {new Date(entry.recorded_at).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                    <span className="metrics-values">{display}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
