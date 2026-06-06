import { useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { createWorkout, getWorkouts } from "../api";
import type { Workout } from "../api";

export default function DashboardPage() {
  const [workouts, setWorkouts] = useState<Workout[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [workoutType, setWorkoutType] = useState("strength");
  const [creating, setCreating] = useState(false);

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

  return (
    <div className="page page-dashboard">
      <div className="page-inner">
      <header className="header">
        <div>
          <h1>My Workouts</h1>
          <p className="subtitle">Your training sessions</p>
        </div>
        <button
          type="button"
          className={showForm ? "btn secondary" : "btn primary"}
          onClick={() => setShowForm((value) => !value)}
        >
          {showForm ? "Cancel" : "New Workout"}
        </button>
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
              <Link to={`/workouts/${workout.id}`} className="workout-item card">
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
