import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import {
  createExercise,
  createWorkout,
  generateWorkout,
  getExercises,
  getWorkouts,
  logSet,
} from "../api";
import type { Exercise, GeneratedWorkout, Workout } from "../api";

function getApiErrorMessage(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data;
    if (typeof data === "string") return data;
    if (data && typeof data === "object" && "detail" in data) {
      const { detail } = data as { detail: unknown };
      if (typeof detail === "string") return detail;
    }
  }
  return fallback;
}

function findExerciseByName(
  exercises: Exercise[],
  name: string,
): Exercise | undefined {
  const normalized = name.trim().toLowerCase();
  return exercises.find(
    (exercise) => exercise.name.trim().toLowerCase() === normalized,
  );
}

export default function DashboardPage() {
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [workoutType, setWorkoutType] = useState("strength");
  const [creating, setCreating] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [generatedWorkout, setGeneratedWorkout] =
    useState<GeneratedWorkout | null>(null);
  const [savingGenerated, setSavingGenerated] = useState(false);

  async function loadWorkouts() {
    setLoading(true);
    setError(null);
    try {
      const data = await getWorkouts();
      setWorkouts(data);
    } catch {
      setError("Failed to load workouts.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadWorkouts();
  }, []);

  async function handleCreate(event: FormEvent) {
    event.preventDefault();
    setCreating(true);
    setError(null);

    try {
      await createWorkout(name, workoutType);
      setName("");
      setWorkoutType("strength");
      setShowForm(false);
      await loadWorkouts();
    } catch {
      setError("Failed to create workout.");
    } finally {
      setCreating(false);
    }
  }

  async function handleGenerateWorkout() {
    setGenerating(true);
    setError(null);

    try {
      const workout = await generateWorkout("personalized workout");
      setGeneratedWorkout(workout);
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to generate workout."));
    } finally {
      setGenerating(false);
    }
  }

  async function handleSaveGeneratedWorkout() {
    if (!generatedWorkout) return;

    setSavingGenerated(true);
    setError(null);

    try {
      const savedWorkout = await createWorkout(
        generatedWorkout.workout_name,
        generatedWorkout.workout_type,
      );

      let exercises = await getExercises();

      for (const generatedExercise of generatedWorkout.exercises) {
        let exercise = findExerciseByName(exercises, generatedExercise.name);

        if (!exercise) {
          exercise = await createExercise({
            name: generatedExercise.name,
            muscle_group: "general",
            equipment: "bodyweight",
            difficulty: "intermediate",
          });
          exercises = [...exercises, exercise];
        }

        await logSet(
          savedWorkout.id,
          exercise.id,
          generatedExercise.sets,
          generatedExercise.reps,
          generatedExercise.weight_kg,
        );
      }

      setGeneratedWorkout(null);
      await loadWorkouts();
    } catch (err) {
      setError(getApiErrorMessage(err, "Failed to save workout."));
    } finally {
      setSavingGenerated(false);
    }
  }

  return (
    <div className="page page-dashboard">
      <div className="page-inner">
        <header className="header">
          <div>
            <h1>My Workouts</h1>
            <p className="subtitle">Your training sessions</p>
          </div>
          <div className="header-actions">
            <button
              type="button"
              className={showForm ? "btn secondary" : "btn primary"}
              onClick={() => setShowForm((value) => !value)}
            >
              {showForm ? "Cancel" : "New Workout"}
            </button>
            <button
              type="button"
              className="btn primary"
              onClick={handleGenerateWorkout}
              disabled={generating}
            >
              {generating ? "Generating..." : "Generate Workout with AI"}
            </button>
          </div>
        </header>

        {showForm && (
          <form onSubmit={handleCreate} className="card form inline-form">
            <label>
              Name
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                placeholder="Push Day"
              />
            </label>
            <label>
              Type
              <select
                value={workoutType}
                onChange={(e) => setWorkoutType(e.target.value)}
              >
                <option value="strength">Strength</option>
                <option value="hypertrophy">Hypertrophy</option>
                <option value="endurance">Endurance</option>
              </select>
            </label>
            <button type="submit" className="btn primary" disabled={creating}>
              {creating ? "Creating..." : "Create"}
            </button>
          </form>
        )}

        {generatedWorkout && (
          <section className="card ai-workout-card">
            <div className="ai-workout-header">
              <div>
                <h2 className="ai-workout-title">
                  {generatedWorkout.workout_name}
                </h2>
                <span className="badge">{generatedWorkout.workout_type}</span>
              </div>
              <button
                type="button"
                className="btn secondary btn-compact"
                onClick={() => setGeneratedWorkout(null)}
                disabled={savingGenerated}
              >
                Dismiss
              </button>
            </div>

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
                  {generatedWorkout.exercises.map((exercise) => (
                    <tr key={exercise.name}>
                      <td>{exercise.name}</td>
                      <td>{exercise.sets}</td>
                      <td>{exercise.reps}</td>
                      <td>{exercise.weight_kg}</td>
                      <td>{exercise.notes || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <button
              type="button"
              className="btn primary"
              onClick={handleSaveGeneratedWorkout}
              disabled={savingGenerated}
            >
              {savingGenerated ? "Saving..." : "Save this Workout"}
            </button>
          </section>
        )}

        {error && <p className="error">{error}</p>}

        {loading ? (
          <p className="muted">Loading workouts...</p>
        ) : workouts.length === 0 ? (
          <div className="card empty-state">
            <p>No workouts yet. Create your first one!</p>
          </div>
        ) : (
          <ul className="workout-list">
            {workouts.map((workout) => (
              <li key={workout.id}>
                <Link
                  to={`/workouts/${workout.id}`}
                  className="workout-item card"
                >
                  <div className="workout-item-content">
                    <div className="workout-item-title">
                      <span>{workout.name}</span>
                      <span className="badge">{workout.workout_type}</span>
                    </div>
                  </div>
                  <span className="muted">
                    {new Date(workout.created_at).toLocaleDateString()}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
