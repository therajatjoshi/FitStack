import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import {
  completeWorkout,
  getExercises,
  getWorkout,
  getWorkoutLogs,
  logSet,
} from "../api";
import type { Exercise, Workout, WorkoutDifficulty, WorkoutLog } from "../api";

const DIFFICULTY_OPTIONS: { value: WorkoutDifficulty; label: string }[] = [
  { value: "easy", label: "Too easy" },
  { value: "just_right", label: "Just right" },
  { value: "hard", label: "Too hard" },
];

const DIFFICULTY_LABEL: Record<string, string> = {
  easy: "Too easy",
  just_right: "Just right",
  hard: "Too hard",
};

export default function WorkoutPage() {
  const { workoutId } = useParams<{ workoutId: string }>();
  const [workout, setWorkout] = useState<Workout | null>(null);
  const [logs, setLogs] = useState<WorkoutLog[]>([]);
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exerciseId, setExerciseId] = useState("");
  const [sets, setSets] = useState(3);
  const [reps, setReps] = useState(10);
  const [weightKg, setWeightKg] = useState(60);
  const [submitting, setSubmitting] = useState(false);
  const [completing, setCompleting] = useState(false);

  async function loadData() {
    if (!workoutId) return;

    setLoading(true);
    setError(null);

    try {
      const [workoutData, logsData, exercisesData] = await Promise.all([
        getWorkout(workoutId),
        getWorkoutLogs(workoutId),
        getExercises(),
      ]);
      setWorkout(workoutData);
      setLogs(logsData);
      setExercises(exercisesData);
      if (exercisesData.length > 0 && !exerciseId) {
        setExerciseId(exercisesData[0].id);
      }
    } catch {
      setError("Failed to load workout data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, [workoutId]);

  async function handleComplete(difficulty: WorkoutDifficulty) {
    if (!workoutId) return;
    setCompleting(true);
    setError(null);
    try {
      const updated = await completeWorkout(workoutId, difficulty);
      setWorkout(updated);
    } catch {
      setError("Failed to save how the session went.");
    } finally {
      setCompleting(false);
    }
  }

  async function handleLogSet(event: FormEvent) {
    event.preventDefault();
    if (!workoutId || !exerciseId) return;

    setSubmitting(true);
    setError(null);

    try {
      await logSet(workoutId, exerciseId, sets, reps, weightKg);
      await loadData();
    } catch {
      setError("Failed to log set.");
    } finally {
      setSubmitting(false);
    }
  }

  const exerciseMap = Object.fromEntries(
    exercises.map((exercise) => [exercise.id, exercise.name]),
  );

  return (
    <div className="page page-dashboard">
      <div className="page-inner">
      <Link to="/" className="back-link">
        &larr; Back to workouts
      </Link>

      <header className="header">
        <div>
          <h1>{workout?.name ?? "Workout"}</h1>
          <p className="subtitle">Log sets and track progress</p>
        </div>
      </header>

      {workout?.plan && (
        <section className="card section-gap">
          <h2 className="section-title">This session's plan</h2>

          {workout.plan.progression_note && (
            <p className="progression-note">↗ {workout.plan.progression_note}</p>
          )}

          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Exercise</th>
                  <th>Sets</th>
                  <th>Reps</th>
                  <th>Weight (kg)</th>
                  <th>Notes</th>
                </tr>
              </thead>
              <tbody>
                {workout.plan.exercises.map((ex) => (
                  <tr key={ex.name}>
                    <td>{ex.name}</td>
                    <td>{ex.sets}</td>
                    <td>{ex.reps}</td>
                    <td>{ex.weight_kg}</td>
                    <td>{ex.notes || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="how-did-it-go">
            {workout.completed_at ? (
              <p className="muted">
                ✓ Logged as{" "}
                <strong>
                  {DIFFICULTY_LABEL[workout.difficulty ?? ""] ?? "done"}
                </strong>
                . Your next AI plan will adapt to this.
              </p>
            ) : (
              <>
                <span className="how-did-it-go-label">How did it go?</span>
                <div className="seg-group">
                  {DIFFICULTY_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      className="seg-btn"
                      disabled={completing}
                      onClick={() => handleComplete(opt.value)}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>
        </section>
      )}

      <form onSubmit={handleLogSet} className="card form">
        <h2 className="section-title">Log a Set</h2>

        <label>
          Exercise
          <select
            value={exerciseId}
            onChange={(e) => setExerciseId(e.target.value)}
            required
          >
            {exercises.length === 0 ? (
              <option value="">No exercises available</option>
            ) : (
              exercises.map((exercise) => (
                <option key={exercise.id} value={exercise.id}>
                  {exercise.name} ({exercise.muscle_group})
                </option>
              ))
            )}
          </select>
        </label>

        <div className="form-row">
          <label>
            Sets
            <input
              type="number"
              min={1}
              value={sets}
              onChange={(e) => setSets(Number(e.target.value))}
              required
            />
          </label>
          <label>
            Reps
            <input
              type="number"
              min={1}
              value={reps}
              onChange={(e) => setReps(Number(e.target.value))}
              required
            />
          </label>
          <label>
            Weight (kg)
            <input
              type="number"
              min={0}
              step={0.5}
              value={weightKg}
              onChange={(e) => setWeightKg(Number(e.target.value))}
              required
            />
          </label>
        </div>

        <button
          type="submit"
          className="btn primary"
          disabled={submitting || exercises.length === 0}
        >
          {submitting ? "Logging..." : "Log Set"}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      <section className="card">
        <h2 className="section-title">Logged Sets</h2>
        {loading ? (
          <p className="muted">Loading logs...</p>
        ) : logs.length === 0 ? (
          <p className="muted">No sets logged yet.</p>
        ) : (
          <ul className="log-list">
            {logs.map((log) => (
              <li key={log.id} className="log-item">
                <strong>{exerciseMap[log.exercise_id] ?? log.exercise_id}</strong>
                <span className="log-stats">
                  {log.sets} x {log.reps} @ {log.weight_kg} kg
                </span>
                <span className="muted">
                  {new Date(log.logged_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
      </div>
    </div>
  );
}
