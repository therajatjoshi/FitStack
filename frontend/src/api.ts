import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "https://rajatjoshi.fit";
const TOKEN_KEY = "fitstack_token";

export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
}

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// On 401, the session has expired or the token is invalid. Clear it and send
// the user back to login — but never for the auth endpoints themselves, where a
// 401 is a "wrong credentials" message the form should display inline.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const url = error.config?.url ?? "";
      const isAuthCall =
        url.includes("/auth/login") || url.includes("/auth/register");
      if (!isAuthCall) {
        clearToken();
        if (window.location.pathname !== "/login") {
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(error);
  },
);

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

export interface WorkoutPlan {
  exercises: GeneratedExercise[];
  progression_note: string;
}

export type WorkoutDifficulty = "easy" | "just_right" | "hard";

export interface Workout {
  id: string;
  user_id: string;
  name: string;
  workout_type: string;
  source: string;
  plan: WorkoutPlan | null;
  completed_at: string | null;
  difficulty: WorkoutDifficulty | null;
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
  progression_note: string;
  consult_recommended: boolean;
  disclaimer: string;
}

export interface MedicalFlags {
  heart_condition: boolean;
  diabetes: boolean;
  asthma: boolean;
  joint_or_back_issues: boolean;
  pregnant: boolean;
  other: boolean;
  other_notes: string | null;
  none: boolean;
  updated_at: string;
}

export interface FullProfile {
  id: string;
  email: string;
  name: string;
  sex: string | null;
  date_of_birth: string | null;
  consent_accepted_at: string | null;
  consent_version: string | null;
  height_cm: number | null;
  primary_goal: string | null;
  secondary_constraint: string | null;
  experience_level: string | null;
  lift_competency: Record<string, string> | null;
  activity_level: string | null;
  training_days_per_week: number | null;
  equipment: string | null;
  injuries_notes: string | null;
  goal_targets: Record<string, unknown> | null;
  goal_timeline_weeks: number | null;
  latest_weight_kg: number | null;
  latest_body_fat_pct: number | null;
  latest_waist_cm: number | null;
  latest_hip_cm: number | null;
  medical_flags: MedicalFlags | null;
  profile_completeness: number;
}

export interface BodyMetricsEntry {
  id: string;
  user_id: string;
  weight_kg: number | null;
  body_fat_pct: number | null;
  waist_cm: number | null;
  hip_cm: number | null;
  recorded_at: string;
}

export interface ConsentText {
  version: string;
  text: string;
}

export interface UserUpdatePayload {
  sex?: string | null;
  date_of_birth?: string | null;
}

export interface ProfileUpdatePayload {
  height_cm?: number | null;
  primary_goal?: string | null;
  secondary_constraint?: string | null;
  experience_level?: string | null;
  lift_competency?: Record<string, string> | null;
  activity_level?: string | null;
  training_days_per_week?: number | null;
  equipment?: string | null;
  injuries_notes?: string | null;
  goal_targets?: Record<string, unknown> | null;
  goal_timeline_weeks?: number | null;
}

export interface MedicalFlagsPayload {
  heart_condition: boolean;
  diabetes: boolean;
  asthma: boolean;
  joint_or_back_issues: boolean;
  pregnant: boolean;
  other: boolean;
  other_notes: string | null;
  none: boolean;
}

export interface BodyMetricsPayload {
  weight_kg?: number | null;
  body_fat_pct?: number | null;
  waist_cm?: number | null;
  hip_cm?: number | null;
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

export async function getWorkout(workoutId: string): Promise<Workout> {
  const { data } = await api.get<Workout>(`/workouts/${workoutId}`);
  return data;
}

export async function saveGeneratedWorkout(
  plan: GeneratedWorkout,
): Promise<Workout> {
  const { data } = await api.post<Workout>("/workouts/generated", {
    workout_name: plan.workout_name,
    workout_type: plan.workout_type,
    exercises: plan.exercises,
    progression_note: plan.progression_note,
  });
  return data;
}

export async function completeWorkout(
  workoutId: string,
  difficulty: WorkoutDifficulty,
): Promise<Workout> {
  const { data } = await api.post<Workout>(`/workouts/${workoutId}/complete`, {
    difficulty,
  });
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

export async function getConsentText(): Promise<ConsentText> {
  const { data } = await api.get<ConsentText>("/consent-text");
  return data;
}

export async function getProfile(): Promise<FullProfile> {
  const { data } = await api.get<FullProfile>("/profile/me");
  return data;
}

export async function updateUser(
  payload: UserUpdatePayload,
): Promise<unknown> {
  const { data } = await api.put("/users/me", payload);
  return data;
}

export async function updateProfile(
  payload: Partial<ProfileUpdatePayload>,
): Promise<unknown> {
  const { data } = await api.put("/profile/me", payload);
  return data;
}

export async function updateMedicalFlags(
  payload: MedicalFlagsPayload,
): Promise<unknown> {
  const { data } = await api.put("/profile/me/medical", payload);
  return data;
}

export async function postConsent(consent_version: string): Promise<unknown> {
  const { data } = await api.post("/profile/me/consent", { consent_version });
  return data;
}

export async function addBodyMetrics(
  payload: BodyMetricsPayload,
): Promise<BodyMetricsEntry> {
  const { data } = await api.post<BodyMetricsEntry>("/body-metrics", payload);
  return data;
}

export async function getBodyMetrics(): Promise<BodyMetricsEntry[]> {
  const { data } = await api.get<BodyMetricsEntry[]>("/body-metrics");
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
