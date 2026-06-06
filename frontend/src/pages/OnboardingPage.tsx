import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  addBodyMetrics,
  getConsentText,
  postConsent,
  updateMedicalFlags,
  updateProfile,
} from "../api";
import type { ConsentText, MedicalFlagsPayload } from "../api";

const TOTAL_STEPS = 4;

function ProgressDots({ current }: { current: number }) {
  return (
    <div className="progress-dots">
      {Array.from({ length: TOTAL_STEPS }, (_, i) => (
        <div
          key={i}
          className={
            i + 1 === current
              ? "progress-dot active"
              : i + 1 < current
                ? "progress-dot done"
                : "progress-dot"
          }
        />
      ))}
    </div>
  );
}

/* ─── Step 1: About You ─── */
function StepAboutYou({ onNext }: { onNext: (goal: string) => void }) {
  const [sex, setSex] = useState("");
  const [dateOfBirth, setDateOfBirth] = useState("");
  const [heightCm, setHeightCm] = useState("");
  const [currentWeightKg, setCurrentWeightKg] = useState("");
  const [primaryGoal, setPrimaryGoal] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canContinue =
    sex && dateOfBirth && heightCm && currentWeightKg && primaryGoal && experienceLevel;

  async function handleNext() {
    setSaving(true);
    setError(null);
    try {
      await updateProfile({
        height_cm: parseFloat(heightCm),
        primary_goal: primaryGoal,
        experience_level: experienceLevel,
      });
      await addBodyMetrics({ weight_kg: parseFloat(currentWeightKg) });
      // TODO: sex and date_of_birth require a PUT /users/me endpoint (not yet implemented)
      onNext(primaryGoal);
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card form">
      <h2>About You</h2>

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
        <input
          type="date"
          value={dateOfBirth}
          onChange={(e) => setDateOfBirth(e.target.value)}
        />
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

      <label>
        Current weight (kg)
        <input
          type="number"
          value={currentWeightKg}
          onChange={(e) => setCurrentWeightKg(e.target.value)}
          placeholder="80"
          min={20}
          max={300}
          step={0.1}
        />
      </label>

      <label>
        Primary goal
        <select value={primaryGoal} onChange={(e) => setPrimaryGoal(e.target.value)}>
          <option value="">Select a goal…</option>
          <option value="fat_loss">Fat loss</option>
          <option value="muscle_gain">Muscle gain</option>
          <option value="strength">Strength</option>
          <option value="recomp">Recomp</option>
          <option value="physique_pageant">Physique &amp; Pageant</option>
          <option value="general_fitness">General fitness</option>
        </select>
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

      {error && <p className="error">{error}</p>}

      <button
        type="button"
        className="btn primary"
        disabled={!canContinue || saving}
        onClick={handleNext}
      >
        {saving ? "Saving…" : "Continue"}
      </button>
    </div>
  );
}

/* ─── Step 2: Health ─── */
function StepHealth({ onNext }: { onNext: () => void }) {
  const [flags, setFlags] = useState<Record<string, boolean>>({
    heart_condition: false,
    diabetes: false,
    asthma: false,
    joint_or_back_issues: false,
    pregnant: false,
    other: false,
    none: false,
  });
  const [otherNotes, setOtherNotes] = useState("");
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

  async function handleNext() {
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
      onNext();
    } catch {
      setError("Failed to save. Please try again.");
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
    <div className="card form">
      <h2>Your Health</h2>
      <p className="subtitle" style={{ marginBottom: "1.25rem" }}>
        This helps us keep your program safe. One tap is all it takes.
      </p>

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
            style={{
              width: "100%",
              background: "var(--input-bg)",
              border: "1px solid var(--input-border)",
              borderRadius: "12px",
              color: "var(--input-text)",
              padding: "12px 16px",
              font: "inherit",
              resize: "vertical",
            }}
          />
        </label>
      )}

      {hasAnyCondition && (
        <div className="amber-note" style={{ marginTop: "0.75rem" }}>
          ⚠️ We'll keep your programming conservative and recommend you check
          with a professional first.
        </div>
      )}

      {error && <p className="error">{error}</p>}

      <button
        type="button"
        className="btn primary"
        disabled={saving}
        onClick={handleNext}
        style={{ marginTop: "0.5rem" }}
      >
        {saving ? "Saving…" : "Continue"}
      </button>
    </div>
  );
}

/* ─── Step 3: Consent ─── */
function StepConsent({ onNext }: { onNext: () => void }) {
  const [consentData, setConsentData] = useState<ConsentText | null>(null);
  const [agreed, setAgreed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getConsentText()
      .then(setConsentData)
      .catch(() => setError("Could not load consent text."));
  }, []);

  async function handleNext() {
    if (!consentData) return;
    setSaving(true);
    setError(null);
    try {
      await postConsent(consentData.version);
      onNext();
    } catch {
      setError("Failed to record consent. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card form">
      <h2>Privacy &amp; Terms</h2>

      {consentData ? (
        <div className="consent-text-box">{consentData.text}</div>
      ) : error ? (
        <p className="error">{error}</p>
      ) : (
        <p className="muted">Loading…</p>
      )}

      <label style={{ flexDirection: "row", alignItems: "center", gap: "0.75rem", cursor: "pointer" }}>
        <input
          type="checkbox"
          checked={agreed}
          onChange={(e) => setAgreed(e.target.checked)}
          style={{ width: "18px", height: "18px", accentColor: "var(--accent)", flexShrink: 0 }}
        />
        <span style={{ color: "var(--text-primary)", fontSize: "0.9rem" }}>
          I understand and agree
        </span>
      </label>

      {error && <p className="error">{error}</p>}

      <button
        type="button"
        className="btn primary"
        disabled={!agreed || !consentData || saving}
        onClick={handleNext}
      >
        {saving ? "Saving…" : "Continue"}
      </button>
    </div>
  );
}

/* ─── Goal-adaptive targets ─── */
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
    const measurements = (targets.target_measurements as Record<string, unknown>) ?? {};
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
            <input type="number" value={(measurements.chest_cm as string) ?? ""} onChange={(e) => setNested("target_measurements", "chest_cm", e.target.value ? parseFloat(e.target.value) : undefined)} placeholder="100" min={0} />
          </label>
          <label>
            Waist
            <input type="number" value={(measurements.waist_cm as string) ?? ""} onChange={(e) => setNested("target_measurements", "waist_cm", e.target.value ? parseFloat(e.target.value) : undefined)} placeholder="80" min={0} />
          </label>
          <label>
            Hip
            <input type="number" value={(measurements.hip_cm as string) ?? ""} onChange={(e) => setNested("target_measurements", "hip_cm", e.target.value ? parseFloat(e.target.value) : undefined)} placeholder="95" min={0} />
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

/* ─── Step 4: Optional ─── */
function StepOptional({ primaryGoal, onFinish }: { primaryGoal: string; onFinish: () => void }) {
  const navigate = useNavigate();
  const [goalTargets, setGoalTargets] = useState<Record<string, unknown>>({});
  const [activityLevel, setActivityLevel] = useState("");
  const [trainingDays, setTrainingDays] = useState(3);
  const [equipment, setEquipment] = useState("");
  const [injuriesNotes, setInjuriesNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFinish() {
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        training_days_per_week: trainingDays,
      };
      if (activityLevel) payload.activity_level = activityLevel;
      if (equipment) payload.equipment = equipment;
      if (injuriesNotes.trim()) payload.injuries_notes = injuriesNotes.trim();
      if (Object.keys(goalTargets).length > 0) payload.goal_targets = goalTargets;

      await updateProfile(payload);
      onFinish();
    } catch {
      setError("Failed to save. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card form">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
        <h2 style={{ margin: 0 }}>Make Your Plan Smarter</h2>
        <button
          type="button"
          onClick={() => navigate("/")}
          style={{ background: "none", border: "none", color: "rgba(255,255,255,0.4)", cursor: "pointer", fontSize: "0.875rem", padding: 0 }}
          onMouseEnter={(e) => (e.currentTarget.style.color = "#fff")}
          onMouseLeave={(e) => (e.currentTarget.style.color = "rgba(255,255,255,0.4)")}
        >
          Skip for now →
        </button>
      </div>

      {primaryGoal && (
        <GoalTargets goal={primaryGoal} targets={goalTargets} onChange={setGoalTargets} />
      )}

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

      {error && <p className="error">{error}</p>}

      <button
        type="button"
        className="btn primary"
        disabled={saving}
        onClick={handleFinish}
      >
        {saving ? "Saving…" : "Finish →"}
      </button>
    </div>
  );
}

/* ─── Main OnboardingPage ─── */
export default function OnboardingPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [primaryGoal, setPrimaryGoal] = useState("");

  function advance() {
      setStep((s) => s + 1);
  }

  return (
    <div className="page-onboarding">
      <ProgressDots current={step} />

      {step === 1 && (
        <StepAboutYou
          onNext={(goal) => {
            setPrimaryGoal(goal);
            advance();
          }}
        />
      )}
      {step === 2 && <StepHealth onNext={advance} />}
      {step === 3 && <StepConsent onNext={advance} />}
      {step === 4 && (
        <StepOptional
          primaryGoal={primaryGoal}
          onFinish={() => navigate("/")}
        />
      )}
    </div>
  );
}
