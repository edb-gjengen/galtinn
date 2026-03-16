import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import { Home } from "@/pages/Home";
import { NotFound } from "@/pages/NotFound";
import { useAuth } from "@/hooks/useAuth";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login/" replace />;
  }

  return <>{children}</>;
}

function GuestRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return null;
  }

  if (isAuthenticated) {
    return <Navigate to="/home/" replace />;
  }

  return <>{children}</>;
}

export function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route
          path="/login/"
          element={
            <GuestRoute>
              <Login />
            </GuestRoute>
          }
        />
        <Route
          path="/register/"
          element={
            <GuestRoute>
              <Register />
            </GuestRoute>
          }
        />
        <Route
          path="/home/"
          element={
            <ProtectedRoute>
              <Home />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
