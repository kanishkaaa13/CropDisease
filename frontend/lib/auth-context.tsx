"use client";

import { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { User, AuthResponse } from "./api";
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [redirectPath, setRedirectPath] = useState<string>("");

  useEffect(() => {
    // Check for existing token on mount
    const storedToken = localStorage.getItem("auth_token");
    const storedUser = localStorage.getItem("auth_user");
    const storedRedirect = localStorage.getItem("redirect_path");
    
    if (storedToken && storedUser) {
      setToken(storedToken);
      setUser(JSON.parse(storedUser));
    }
    if (storedRedirect) {
      setRedirectPath(storedRedirect);
    }
    setLoading(false);
  }, []);

  const login = async (email: string, password: string) => {
    try {
      const response = await api.login({ username: email, password });
      setToken(response.access_token);
      setUser(response.user);
      localStorage.setItem("auth_token", response.access_token);
      localStorage.setItem("auth_user", JSON.stringify(response.user));
      
      // Redirect to stored path or default based on role
      const targetPath = redirectPath || (response.user.role === "farmer" ? "/farmer" : "/officer");
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
      
      // Redirect to stored path or default based on role
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
