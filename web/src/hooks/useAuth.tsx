import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { fetchApi, ApiError } from "@/lib/api";
import type { User } from "@/types";

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  refreshUser: () => Promise<void>;
}

interface RegisterData {
  first_name: string;
  last_name: string;
  email: string;
  phone_number: string;
  password: string;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refreshUser = useCallback(async () => {
    try {
      const data = await fetchApi<User>("/api/auth/session/");
      setUser(data);
    } catch {
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const initialize = async () => {
      await refreshUser().finally(() => setIsLoading(false));
    };
    initialize();
  }, [refreshUser]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await fetchApi<User>("/api/auth/login/", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setUser(data);
  }, []);

  const logout = useCallback(async () => {
    await fetchApi("/api/auth/logout/", { method: "POST" });
    setUser(null);
  }, []);

  const register = useCallback(
    async (data: RegisterData) => {
      try {
        await fetchApi("/api/user/register/", {
          method: "POST",
          body: JSON.stringify(data),
        });
        // Auto-login after registration
        await login(data.email, data.password);
      } catch (err) {
        if (err instanceof ApiError) {
          throw err;
        }
        throw err;
      }
    },
    [login],
  );

  const value = useMemo(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      logout,
      register,
      refreshUser,
    }),
    [user, isLoading, login, logout, register, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
