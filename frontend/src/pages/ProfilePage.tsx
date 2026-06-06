import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  getProfile,
  updateMedicalFlags,
  updateProfile,
} from "../api";
import type { FullProfile, MedicalFlagsPayload } from "../api";

function Toast({ message }: { message: string }) {
  return <div className="toast">{message}</div>;
}

function CompletenessBar({ pct }: { pct: number }) {
  return (
    <div className="completeness-bar-wrap">
      <div className="completeness-bar-labels">
        <span className="muted">Profile {pct}% complete</span>
        {pct < 100 && (
          <span style={{ color: "var(--accent)", fontSize: "0.85rem" }}>
            Complete for smarter AI plans ✨
          </span>
        )}
      </div>
      <div className="completeness-bar-track">
        <div
          className="completeness-bar-fill"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

/* ─── Goal-adaptive targets (reused from Onboarding) ─── */
function GoalTargets({
  goal,
  targets,
  onChange,
}: {
  goal: string;
  targets: Record<string, unknown>;
  onChange: (t: Record<string, unknown>) => void;
}) {
  function set(key: string, value: unknown) {
    onChange({ ...targets, [key]: value });
  }

  function setNested(parent: string, key: string, value: unknown) {
    const existing = (targets[parent] as Record<string, unknown>) ?? {};
    onChange({ ...targets, [parent]: { ...existing, [key]: value } });
  }

  if (goal === "fat_loss" || goal === "recomp") {
    return (
      <>
        <label>
          Target weight (kg)
          <input
            type="number"
            value={(targets.target_weight_kg as string) ?? ""}
            onChange={(e) => set("target_weight_kg", e.target.value ? parseFloat(e.target.value) : undefined)}
            placeholder="70"
            min={20}
            max={300}
            step={0.1}
          />
        </label>
        <label>
          Target body fat (%)
          <input
            type="number"
            value={(targets.target_body_fat_pct as string) ?? ""}
            onChange={(e) => set("target_body_fat_pct", e.target.value ? parseFloat(e.target.value) : undefined)}
            placeholder="15"
            min={3}
            max={60}
            step={0.1}
          />
        </label>
      </>
    );
  }

  if (goal === "muscle_gain" || goal === "strength") {
    const lifts = (targets.target_lifts as Record<string, unknown>) ?? {};
    const meas = (targets.target_measurements as Record<string, unknown>) ?? {};
    return (
      <>
        <p className="muted" style={{ marginBottom: "0.5rem" }}>Target lifts (kg)</p>
        <div className="form-row">
          <label>
            Bench press
            <input type="number" value={(lifts.bench as string) ?? ""} onChange={(e) => setNested("target_lifts", "bench", e.target.value ? parseFloat(e.target.value) : undefined)} placeholder="100" min={0} />
          </label>
          <label>
            Squat
            <input type="number" value={(lifts.squat as string) ?? ""} onChange={(e) => setNested("target_lifts", "squat", e.target.value ? parseFloat(e.target.value) : undefined)} placeholder="120" min={0} />
          </label>
          <label>
            Deadlift
            <input type="number" value={(lifts.deadlift as string) ?? ""} onChange={(e) => setNested("target_lifts", "deadlift", e.target.value ? parseFloat(e.target.value) : undefined)} placeholder="140" min={0} />
          </label>
        </div>
        <p className="muted" style={{ margin: "0.75rem 0 0.5rem" }}>Key measurements (cm)</p>
        <div className="form-row">
          <label>
            Chest
            <input type="number" value={(meas.chest_cm as string) ?? ""} onChange={(e) => setNested("target_measurements", "chest_cm", e.target.value ? parseFloat(e.target.value) : undefined)} placeholder="100" min={0} />
          </label>
          <label>
            Waist
            <input type="number" value={(meas.waist_cm as string) ?? ""} onChange={(e) => setNested("target_measurements", "waist_cm", e.target.value ? parseFloat(e.target.value) : undefined)} placeholder="80" min={0} />
          </label>
          <label>
            Hip
            <input type="number" value={(meas.hip_cm as string) ?? ""} onChange={(e) => setNested("target_measurements", "hip_cm", e.target.value ? parseFloat(e.target.value) : undefined)} placeholder="95" min={0} />
          </label>
        </div>
      </>
    );
  }

  if (goal === "physique_pageant") {
    return (
      <>
        <label>
          Target date
          <input
            type="date"
            value={(targets.target_date as string) ?? ""}
            onChange={(e) => set("target_date", e.target.value)}
          />
        </label>
        <label>
          Condition notes
          <textarea
            value={(targets.condition_notes as string) ?? ""}
            onChange={(e) => set("condition_notes", e.target.value)}
            placeholder="e.g. competing in classic physique division…"
            rows={3}
            style={{ width: "100%", background: "var(--input-bg)", border: "1px solid var(--input-border)", borderRadius: "12px", color: "var(--input-text)", padding: "12px 16px", font: "inherit", resize: "vertical" }}
          />
        </label>
      </>
    );
  }

  if (goal === "general_fitness") {
    return (
      <p className="muted" style={{ padding: "0.5rem 0" }}>
        No specific targets needed — we'll program for overall health.
      </p>
    );
  }

  return null;
}

/* ─── Basics Card ─── */
function BasicsCard({ profile, onSaved }: { profile: FullProfile; onSaved: () => void }) {
  const [sex, setSex] = useState(profile.sex ?? "");
  const [dob, setDob] = useState(profile.date_of_birth ?? "");
  const [heightCm, setHeightCm] = useState(profile.height_cm?.toString() ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {};
      if (heightCm) payload.height_cm = parseFloat(heightCm);
      // TODO: sex and date_of_birth require a PUT /users/me endpoint (not yet implemented)
      await updateProfile(payload);
      onSaved();
    } catch {
      setError("Failed to save.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card form section-gap">
      <h2>Basics</h2>

      <label>
        Sex
        <div className="seg-group" style={{ marginTop: "0.5rem" }}>
          {["Male", "Female", "Other"].map((s) => (
            <button
              key={s}
              type="button"
              className={sex === s.toLowerCase() ? "seg-btn active" : "seg-btn"}
              onClick={() => setSex(s.toLowerCase())}
            >
              {s}
            </button>
          ))}
        </div>
      </label>

      <label>
        Date of birth
        <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
      </label>

      <label>
        Height (cm)
        <input
          type="number"
          value={heightCm}
          onChange={(e) => setHeightCm(e.target.value)}
          placeholder="175"
          min={100}
          max={250}
        />
      </label>

      {error && <p className="error">{error}</p>}

      <button type="button" className="btn primary" disabled={saving} onClick={handleSave}>
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  );
}

/* ─── Goal & Targets Card ─── */
function GoalCard({ profile, onSaved }: { profile: FullProfile; onSaved: () => void }) {
  const [primaryGoal, setPrimaryGoal] = useState(profile.primary_goal ?? "");
  const [secondaryConstraint, setSecondaryConstraint] = useState(profile.secondary_constraint ?? "");
  const [experienceLevel, setExperienceLevel] = useState(profile.experience_level ?? "");
  const [goalTimelineWeeks, setGoalTimelineWeeks] = useState(profile.goal_timeline_weeks?.toString() ?? "");
  const [goalTargets, setGoalTargets] = useState<Record<string, unknown>>(
    (profile.goal_targets as Record<string, unknown>) ?? {}
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {};
      if (primaryGoal) payload.primary_goal = primaryGoal;
      if (secondaryConstraint.trim()) payload.secondary_constraint = secondaryConstraint.trim();
      if (experienceLevel) payload.experience_level = experienceLevel;
      if (goalTimelineWeeks) payload.goal_timeline_weeks = parseInt(goalTimelineWeeks, 10);
      if (Object.keys(goalTargets).length > 0) payload.goal_targets = goalTargets;
      await updateProfile(payload);
      onSaved();
    } catch {
      setError("Failed to save.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card form section-gap">
      <h2>Goal &amp; Targets</h2>

      <label>
        Primary goal
        <select value={primaryGoal} onChange={(e) => setPrimaryGoal(e.target.value)}>
          <option value="">Select…</option>
          <option value="fat_loss">Fat loss</option>
          <option value="muscle_gain">Muscle gain</option>
          <option value="strength">Strength</option>
          <option value="recomp">Recomp</option>
          <option value="physique_pageant">Physique &amp; Pageant</option>
          <option value="general_fitness">General fitness</option>
        </select>
      </label>

      <label>
        Secondary constraint
        <textarea
          value={secondaryConstraint}
          onChange={(e) => setSecondaryConstraint(e.target.value)}
          placeholder="e.g. keep strength while cutting"
          rows={2}
          style={{ width: "100%", background: "var(--input-bg)", border: "1px solid var(--input-border)", borderRadius: "12px", color: "var(--input-text)", padding: "12px 16px", font: "inherit", resize: "vertical" }}
        />
      </label>

      <label>
        Experience level
        <div className="exp-cards" style={{ marginTop: "0.5rem" }}>
          {[
            { value: "novice", label: "Novice", sub: "Less than 2 years" },
            { value: "intermediate", label: "Intermediate", sub: "2–5 years" },
            { value: "advanced", label: "Advanced", sub: "5+ years" },
          ].map(({ value, label, sub }) => (
            <div
              key={value}
              className={experienceLevel === value ? "exp-card active" : "exp-card"}
              onClick={() => setExperienceLevel(value)}
            >
              <div className="exp-card-title">{label}</div>
              <div className="exp-card-sub">{sub}</div>
            </div>
          ))}
        </div>
      </label>

      <label>
        Goal timeline (weeks)
        <input
          type="number"
          value={goalTimelineWeeks}
          onChange={(e) => setGoalTimelineWeeks(e.target.value)}
          placeholder="12"
          min={1}
          max={104}
        />
      </label>

      {primaryGoal && (
        <GoalTargets goal={primaryGoal} targets={goalTargets} onChange={setGoalTargets} />
      )}

      {error && <p className="error">{error}</p>}

      <button type="button" className="btn primary" disabled={saving} onClick={handleSave}>
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  );
}

/* ─── Training Card ─── */
function TrainingCard({ profile, onSaved }: { profile: FullProfile; onSaved: () => void }) {
  const [activityLevel, setActivityLevel] = useState(profile.activity_level ?? "");
  const [trainingDays, setTrainingDays] = useState(profile.training_days_per_week ?? 3);
  const [equipment, setEquipment] = useState(profile.equipment ?? "");
  const [injuriesNotes, setInjuriesNotes] = useState(profile.injuries_notes ?? "");
  const [liftCompetency, setLiftCompetency] = useState<Record<string, string>>(
    (profile.lift_competency as Record<string, string>) ?? {}
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function setLift(lift: string, level: string) {
    setLiftCompetency((prev) => ({ ...prev, [lift]: level }));
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        training_days_per_week: trainingDays,
      };
      if (activityLevel) payload.activity_level = activityLevel;
      if (equipment) payload.equipment = equipment;
      if (injuriesNotes.trim()) payload.injuries_notes = injuriesNotes.trim();
      if (Object.keys(liftCompetency).length > 0) payload.lift_competency = liftCompetency;
      await updateProfile(payload);
      onSaved();
    } catch {
      setError("Failed to save.");
    } finally {
      setSaving(false);
    }
  }

  const liftOptions = [
    { key: "squat", label: "Squat" },
    { key: "bench", label: "Bench press" },
    { key: "deadlift", label: "Deadlift" },
  ];

  return (
    <div className="card form section-gap">
      <h2>Training</h2>

      <label>
        Activity level
        <select value={activityLevel} onChange={(e) => setActivityLevel(e.target.value)}>
          <option value="">Select…</option>
          <option value="sedentary">Sedentary</option>
          <option value="light">Light</option>
          <option value="moderate">Moderate</option>
          <option value="very_active">Very active</option>
        </select>
      </label>

      <label>
        Training days per week
        <div className="slider-wrap">
          <span className="slider-value">{trainingDays} days</span>
          <input
            type="range"
            min={1}
            max={7}
            value={trainingDays}
            onChange={(e) => setTrainingDays(Number(e.target.value))}
          />
        </div>
      </label>

      <label>
        Equipment
        <select value={equipment} onChange={(e) => setEquipment(e.target.value)}>
          <option value="">Select…</option>
          <option value="full_gym">Full gym</option>
          <option value="home_basic">Home basic</option>
          <option value="minimal">Minimal</option>
          <option value="bodyweight">Bodyweight only</option>
        </select>
      </label>

      <label>
        Injuries or limitations
        <textarea
          value={injuriesNotes}
          onChange={(e) => setInjuriesNotes(e.target.value)}
          placeholder="Describe any injuries, surgeries, or limitations…"
          rows={3}
          style={{ width: "100%", background: "var(--input-bg)", border: "1px solid var(--input-border)", borderRadius: "12px", color: "var(--input-text)", padding: "12px 16px", font: "inherit", resize: "vertical" }}
        />
      </label>

      <p className="muted" style={{ marginBottom: "0.5rem" }}>Lift competency</p>
      <div className="form-row">
        {liftOptions.map(({ key, label }) => (
          <label key={key}>
            {label}
            <select
              value={liftCompetency[key] ?? ""}
              onChange={(e) => setLift(key, e.target.value)}
            >
              <option value="">Select…</option>
              <option value="novice">Novice</option>
              <option value="intermediate">Intermediate</option>
              <option value="advanced">Advanced</option>
            </select>
          </label>
        ))}
      </div>

      {error && <p className="error">{error}</p>}

      <button type="button" className="btn primary" disabled={saving} onClick={handleSave}>
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  );
}

/* ─── Medical Card ─── */
function MedicalCard({ profile, onSaved }: { profile: FullProfile; onSaved: () => void }) {
  const mf = profile.medical_flags;
  const [flags, setFlags] = useState<Record<string, boolean>>({
    heart_condition: mf?.heart_condition ?? false,
    diabetes: mf?.diabetes ?? false,
    asthma: mf?.asthma ?? false,
    joint_or_back_issues: mf?.joint_or_back_issues ?? false,
    pregnant: mf?.pregnant ?? false,
    other: mf?.other ?? false,
    none: mf?.none ?? false,
  });
  const [otherNotes, setOtherNotes] = useState(mf?.other_notes ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const hasAnyCondition = Object.entries(flags)
    .filter(([k]) => k !== "none")
    .some(([, v]) => v);

  function toggle(key: string) {
    if (key === "none") {
      const newNone = !flags.none;
      const reset: Record<string, boolean> = {};
      Object.keys(flags).forEach((k) => { reset[k] = false; });
      reset.none = newNone;
      setFlags(reset);
    } else {
      setFlags((prev) => ({ ...prev, [key]: !prev[key], none: false }));
    }
  }

  async function handleSave() {
    setSaving(true);
    setError(null);
    try {
      const payload: MedicalFlagsPayload = {
        heart_condition: flags.heart_condition,
        diabetes: flags.diabetes,
        asthma: flags.asthma,
        joint_or_back_issues: flags.joint_or_back_issues,
        pregnant: flags.pregnant,
        other: flags.other,
        other_notes: flags.other ? otherNotes || null : null,
        none: flags.none,
      };
      await updateMedicalFlags(payload);
      onSaved();
    } catch {
      setError("Failed to save.");
    } finally {
      setSaving(false);
    }
  }

  const checkItems = [
    { key: "heart_condition", label: "Heart condition" },
    { key: "diabetes", label: "Diabetes" },
    { key: "asthma", label: "Asthma" },
    { key: "joint_or_back_issues", label: "Joint or back issues" },
    { key: "pregnant", label: "Pregnant" },
    { key: "other", label: "Other" },
    { key: "none", label: "None of these" },
  ];

  return (
    <div className="card form section-gap">
      <h2>Medical</h2>

      {hasAnyCondition && (
        <div className="amber-note" style={{ marginBottom: "0.75rem" }}>
          ⚠️ We'll keep your programming conservative and recommend you check
          with a professional first.
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
        {checkItems.map(({ key, label }) => (
          <label
            key={key}
            className={flags[key] ? "check-row checked" : "check-row"}
          >
            <input
              type="checkbox"
              checked={flags[key]}
              onChange={() => toggle(key)}
            />
            <span>{label}</span>
          </label>
        ))}
      </div>

      {flags.other && (
        <label style={{ marginTop: "0.75rem" }}>
          Notes
          <textarea
            value={otherNotes}
            onChange={(e) => setOtherNotes(e.target.value)}
            placeholder="Briefly describe…"
            rows={3}
            style={{ width: "100%", background: "var(--input-bg)", border: "1px solid var(--input-border)", borderRadius: "12px", color: "var(--input-text)", padding: "12px 16px", font: "inherit", resize: "vertical" }}
          />
        </label>
      )}

      {error && <p className="error">{error}</p>}

      <button type="button" className="btn primary" disabled={saving} onClick={handleSave} style={{ marginTop: "0.5rem" }}>
        {saving ? "Saving…" : "Save"}
      </button>
    </div>
  );
}

/* ─── Main ProfilePage ─── */
export default function ProfilePage() {
  const [profile, setProfile] = useState<FullProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState<string | null>(null);

  async function load() {
    try {
      const data = await getProfile();
      setProfile(data);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  function showToast(msg: string) {
    setToast(msg);
    setTimeout(() => setToast(null), 2000);
  }

  function handleSaved() {
    showToast("Saved successfully!");
    load();
  }

  return (
    <div className="page page-dashboard">
      {toast && <Toast message={toast} />}
      <div className="page-inner">
        <Link to="/" className="back-link">
          &larr; Back to workouts
        </Link>

        <header className="header">
          <div>
            <h1>My Profile</h1>
          </div>
        </header>

        {loading ? (
          <p className="muted">Loading…</p>
        ) : profile ? (
          <>
            <CompletenessBar pct={profile.profile_completeness} />
            <BasicsCard profile={profile} onSaved={handleSaved} />
            <GoalCard profile={profile} onSaved={handleSaved} />
            <TrainingCard profile={profile} onSaved={handleSaved} />
            <MedicalCard profile={profile} onSaved={handleSaved} />
          </>
        ) : (
          <p className="error">Failed to load profile.</p>
        )}
      </div>
    </div>
  );
}
