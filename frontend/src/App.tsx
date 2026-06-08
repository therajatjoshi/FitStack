import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { getToken } from "./api";
import { getAdminToken } from "./adminApi";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import WorkoutPage from "./pages/WorkoutPage";
import OnboardingPage from "./pages/OnboardingPage";
import ProfilePage from "./pages/ProfilePage";
import MetricsPage from "./pages/MetricsPage";
import AdminLoginPage from "./pages/AdminLoginPage";
import AdminPage from "./pages/AdminPage";

function ProtectedRoute({ children }: { children: ReactNode }) {
  // Restored from sessionStorage on each render — survives page refresh within the tab.
  if (!getToken()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

function LoginRoute() {
  if (getToken()) {
    return <Navigate to="/" replace />;
  }
  return <LoginPage />;
}

function ProtectedAdminRoute({ children }: { children: ReactNode }) {
  if (!getAdminToken()) {
    return <Navigate to="/admin/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/workouts/:workoutId"
        element={
          <ProtectedRoute>
            <WorkoutPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <OnboardingPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/metrics"
        element={
          <ProtectedRoute>
            <MetricsPage />
          </ProtectedRoute>
        }
      />
      <Route path="/admin/login" element={<AdminLoginPage />} />
      <Route
        path="/admin"
        element={
          <ProtectedAdminRoute>
            <AdminPage />
          </ProtectedAdminRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
