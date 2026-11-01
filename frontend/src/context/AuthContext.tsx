import React, { createContext, useState, useEffect, type ReactNode } from "react";
import { api } from "../api/client";
import type { User, LoginPayload, RegisterPayload } from "../types/api";
import { useAuth } from "./useAuth";

export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: LoginPayload) => Promise<User>;
  register: (payload: RegisterPayload) => Promise<User>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize session on mount via httpOnly cookie checks
  useEffect(() => {
    let mounted = true;

    async function initAuth() {
      try {
        const currentUser = await api.me();
        if (mounted) {
          setUser(currentUser);
        }
      } catch {
        // Access token might be expired; attempt silent refresh with refresh cookie
        try {
          const refreshedUser = await api.refresh();
          if (mounted) {
            setUser(refreshedUser);
          }
        } catch {
          if (mounted) {
            setUser(null);
          }
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    }

    initAuth();

    return () => {
      mounted = false;
    };
  }, []);

  const login = async (payload: LoginPayload): Promise<User> => {
    const loggedInUser = await api.login(payload);
    setUser(loggedInUser);
    return loggedInUser;
  };

  const register = async (payload: RegisterPayload): Promise<User> => {
    const registeredUser = await api.register(payload);
    setUser(registeredUser);
    return registeredUser;
  };

  const logout = async (): Promise<void> => {
    try {
      await api.logout();
    } catch {
      // Ignore network errors on logout
    } finally {
      setUser(null);
    }
  };

  const refreshUser = async (): Promise<void> => {
    try {
      const u = await api.me();
      setUser(u);
    } catch {
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export { useAuth };
