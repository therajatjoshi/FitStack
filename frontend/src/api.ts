import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "https://rajatjoshi.fit";

let accessToken: string | null = null;

export function setToken(token: string): void {
  accessToken = token;
}

export function clearToken(): void {
  accessToken = null;
}

export function getToken(): string | null {
  return accessToken;
}

export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

export interface User {
  id: string;
  email: string;
  name: string;
  training_years: number;
  goal: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Workout {
  id: string;
  user_id: string;
  name: string;
  workout_type: string;
  created_at: string;
}

export interface Exercise {
  id: string;
  name: string;
  muscle_group: string;
  equipment: string;
}

export interface WorkoutLog {
  id: string;
  user_id: string;
  exercise_id: string;
  workout_id: string;
  sets: number;
  reps: number;
  weight_kg: number;
  logged_at: string;
}

export interface GeneratedExercise {
  name: string;
  sets: number;
  reps: number;
  weight_kg: number;
  notes: string;
}

export interface GeneratedWorkout {
  workout_name: string;
  workout_type: string;
  exercises: GeneratedExercise[];
}

export interface ExerciseCreatePayload {
  name: string;
  muscle_group: string;
  equipment: string;
  difficulty: string;
}

export async function register(
  email: string,
  password: string,
  name: string,
): Promise<User> {
  const { data } = await api.post<User>("/auth/register", {
    email,
    password,
    name,
  });
  return data;
}

export async function login(
  email: string,
  password: string,
): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", {
    email,
    password,
  });
  return data;
}

export async function getWorkouts(): Promise<Workout[]> {
  const { data } = await api.get<Workout[]>("/workouts");
  return data;
}

export async function createWorkout(
  name: string,
  workout_type: string,
): Promise<Workout> {
  const { data } = await api.post<Workout>("/workouts", { name, workout_type });
  return data;
}

export async function getExercises(): Promise<Exercise[]> {
  const { data } = await api.get<Exercise[]>("/exercises");
  return data;
}

export async function createExercise(
  payload: ExerciseCreatePayload,
): Promise<Exercise> {
  const { data } = await api.post<Exercise>("/exercises", payload);
  return data;
}

export async function generateWorkout(
  prompt?: string,
): Promise<GeneratedWorkout> {
  const { data } = await api.post<GeneratedWorkout>("/ai/generate-workout", {
    prompt,
  });
  return data;
}

export async function getWorkoutLogs(workoutId: string): Promise<WorkoutLog[]> {
  const { data } = await api.get<WorkoutLog[]>(`/workouts/${workoutId}/logs`);
  return data;
}

export async function logSet(
  workoutId: string,
  exercise_id: string,
  sets: number,
  reps: number,
  weight_kg: number,
): Promise<WorkoutLog> {
  const { data } = await api.post<WorkoutLog>(`/workouts/${workoutId}/log`, {
    exercise_id,
    sets,
    reps,
    weight_kg,
  });
  return data;
}
