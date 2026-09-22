"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { SESSION_EXPIRED_EVENT, User } from "./api";
import { api } from "./api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    full_name: string;
    email: string;
    password: string;
    phone?: string;
    role: "farmer" | "officer";
    district?: string;
    preferred_language: string;
  }) => Promise<void>;
  logout: () => void;
  loading: boolean;
  setRedirectPath: (path: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);
const PROTECTED_PATHS = ["/farmer", "/officer", "/admin", "/predict"];

function isProtectedPath(pathname: string) {
  return PROTECTED_PATHS.some((path) => pathname === path || pathname.startsWith(`${path}/`));
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [redirectPath, setRedirectPath] = useState<string>("");

  useEffect(() => {
    let cancelled = false;

    const validateStoredToken = async () => {
      const storedToken = localStorage.getItem("auth_token");
      const storedRedirect = localStorage.getItem("redirect_path");
      const validRedirect = storedRedirect && isProtectedPath(storedRedirect) ? storedRedirect : "";

      setRedirectPath(validRedirect);

      if (!storedToken) {
        if (!cancelled) {
          setUser(null);
          setLoading(false);
        }
        return;
      }

      setToken(storedToken);

      try {
        const backendUser = await api.getMe();
        if (!cancelled) {
          setUser(backendUser);
          localStorage.setItem("auth_user", JSON.stringify(backendUser));
        }
      } catch {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("auth_user");
        if (!cancelled) {
          setToken(null);
          setUser(null);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    void validateStoredToken();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    const handleSessionExpired = () => {
      setToken(null);
      setUser(null);
      setLoading(false);
    };

    window.addEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, handleSessionExpired);
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await api.login({ username: email, password });
      setToken(response.access_token);
      setUser(response.user);
      localStorage.setItem("auth_token", response.access_token);
      localStorage.setItem("auth_user", JSON.stringify(response.user));

      const defaultPath = response.user.role === "farmer" ? "/farmer" : "/officer";
      const targetPath = isProtectedPath(redirectPath) ? redirectPath : defaultPath;
      localStorage.removeItem("redirect_path");
      router.push(targetPath);
    } catch (error) {
      throw error;
    }
  };

  const register = async (data: {
    full_name: string;
    email: string;
    password: string;
    phone?: string;
    role: "farmer" | "officer";
    district?: string;
    preferred_language: string;
  }) => {
    try {
      const response = await api.register(data);
      setToken(response.access_token);
      setUser(response.user);
      localStorage.setItem("auth_token", response.access_token);
      localStorage.setItem("auth_user", JSON.stringify(response.user));

      const targetPath = redirectPath || (data.role === "farmer" ? "/farmer" : "/officer");
      localStorage.removeItem("redirect_path");
      router.push(targetPath);
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("auth_token");
    localStorage.removeItem("auth_user");
    router.push("/login");
  };

  const saveRedirectPath = (path: string) => {
    setRedirectPath(path);
    localStorage.setItem("redirect_path", path);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading, setRedirectPath: saveRedirectPath }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}