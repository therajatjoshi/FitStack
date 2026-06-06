import { Navigate, Route, Routes } from "react-router-dom";
import type { ReactNode } from "react";
import { getToken } from "./api";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import WorkoutPage from "./pages/WorkoutPage";

function ProtectedRoute({ children }: { children: ReactNode }) {
  if (!getToken()) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
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
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
