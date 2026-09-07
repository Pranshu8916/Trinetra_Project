"use client";

import { createContext, useContext, useState, useEffect, useCallback } from "react";
import {
  getToken,
  getUser,
  setToken,
  setUser,
  clearToken,
  clearUser,
  apiMe,
  subscribeAuthError,
} from "@/lib/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUserState] = useState(null);
  const [token, setTokenState] = useState(null);
  const [loading, setLoading] = useState(true);

  const logout = useCallback(() => {
    clearToken();
    clearUser();
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("trinetra_active_session");
      sessionStorage.removeItem("trinetra_active_session_id");
    }
    setTokenState(null);
    setUserState(null);
  }, []);

  // Initialize auth state and validate token on mount/refresh
  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      const storedToken = getToken();
      const storedUser = getUser();

      if (!storedToken) {
        if (isMounted) {
          setTokenState(null);
          setUserState(null);
          setLoading(false);
        }
        return;
      }

      setTokenState(storedToken);
      if (storedUser) setUserState(storedUser);

      // Validate token with backend /api/protected/me
      try {
        const res = await apiMe();
        if (isMounted) {
          if (res && res.user) {
            setUserState(res.user);
            setUser(res.user);
          }
        }
      } catch (err) {
        // If token is invalid or backend rejected it (401), clear auth
        if (isMounted && err?.status === 401) {
          logout();
        }
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    initAuth();

    // Subscribe to central 401 auth errors from API layer
    const unsubscribe = subscribeAuthError(() => {
      if (isMounted) logout();
    });

    return () => {
      isMounted = false;
      unsubscribe();
    };
  }, [logout]);

  const login = (tokenVal, userVal) => {
    setToken(tokenVal);
    setUser(userVal);
    setTokenState(tokenVal);
    setUserState(userVal);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        logout,
        isAuthenticated: !!token && !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used inside an AuthProvider");
  }
  return ctx;
}
