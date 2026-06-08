import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL ?? "https://rajatjoshi.fit";
const ADMIN_TOKEN_KEY = "fitstack_admin_token";

export function setAdminToken(token: string): void {
  sessionStorage.setItem(ADMIN_TOKEN_KEY, token);
}

export function clearAdminToken(): void {
  sessionStorage.removeItem(ADMIN_TOKEN_KEY);
}

export function getAdminToken(): string | null {
  return sessionStorage.getItem(ADMIN_TOKEN_KEY);
}

// Separate axios instance + token from the user session, so an admin and a user
// can be signed in at once without their bearer tokens colliding.
const adminApi = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

adminApi.interceptors.request.use((config) => {
  const token = getAdminToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

adminApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      const url = error.config?.url ?? "";
      if (!url.includes("/admin/auth/login")) {
        clearAdminToken();
        if (window.location.pathname !== "/admin/login") {
          window.location.href = "/admin/login";
        }
      }
    }
    return Promise.reject(error);
  },
);

export interface AdminUserSummary {
  id: string;
  email: string;
  name: string;
  created_at: string;
  consent_accepted_at: string | null;
  workout_count: number;
  body_metrics_count: number;
  is_stale: boolean;
  stale_reason: string | null;
}

export interface CleanupResult {
  deleted_count: number;
  deleted_emails: string[];
}

export async function adminLogin(
  email: string,
  password: string,
): Promise<string> {
  const { data } = await adminApi.post<{ access_token: string }>(
    "/admin/auth/login",
    { email, password },
  );
  return data.access_token;
}

export async function getAdminUsers(): Promise<AdminUserSummary[]> {
  const { data } = await adminApi.get<AdminUserSummary[]>("/admin/users");
  return data;
}

export async function getStaleUsers(): Promise<AdminUserSummary[]> {
  const { data } = await adminApi.get<AdminUserSummary[]>("/admin/users/stale");
  return data;
}

export async function deleteUser(userId: string): Promise<void> {
  await adminApi.delete(`/admin/users/${userId}`);
}

export async function cleanupStale(): Promise<CleanupResult> {
  const { data } = await adminApi.post<CleanupResult>("/admin/users/cleanup");
  return data;
}
