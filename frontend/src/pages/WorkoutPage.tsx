import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { getExercises, getWorkoutLogs, logSet } from "../api";
import type { Exercise, WorkoutLog } from "../api";

export default function WorkoutPage() {
  const { workoutId } = useParams<{ workoutId: string }>();
  const [logs, setLogs] = useState<WorkoutLog[]>([]);
  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [exerciseId, setExerciseId] = useState("");
  const [sets, setSets] = useState(3);
  const [reps, setReps] = useState(10);
  const [weightKg, setWeightKg] = useState(60);
  const [submitting, setSubmitting] = useState(false);

  async function loadData() {
    if (!workoutId) return;

    setLoading(true);
    setError(null);

    try {
      const [logsData, exercisesData] = await Promise.all([
        getWorkoutLogs(workoutId),
        getExercises(),
      ]);
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
          <h1>Workout Logs</h1>
          <p className="subtitle">Log sets and track progress</p>
        </div>
      </header>

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
