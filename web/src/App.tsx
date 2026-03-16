import { Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "@/components/Layout";
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import { Home } from "@/pages/Home";
import { Profile } from "@/pages/Profile";
import { EditProfile } from "@/pages/EditProfile";
import { ChangePassword } from "@/pages/ChangePassword";
import { SetUsername } from "@/pages/SetUsername";
import { DeleteAccount } from "@/pages/DeleteAccount";
import { MembershipList } from "@/pages/MembershipList";
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
        <Route
          path="/me/"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/me/update/"
          element={
            <ProtectedRoute>
              <EditProfile />
            </ProtectedRoute>
          }
        />
        <Route
          path="/me/update/username/"
          element={
            <ProtectedRoute>
              <SetUsername />
            </ProtectedRoute>
          }
        />
        <Route
          path="/me/delete/"
          element={
            <ProtectedRoute>
              <DeleteAccount />
            </ProtectedRoute>
          }
        />
        <Route
          path="/memberships/"
          element={
            <ProtectedRoute>
              <MembershipList />
            </ProtectedRoute>
          }
        />
        <Route
          path="/auth/password_change/"
          element={
            <ProtectedRoute>
              <ChangePassword />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  );
}
