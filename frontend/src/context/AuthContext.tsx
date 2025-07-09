import React, { createContext, useState, useEffect, ReactNode } from 'react';
import axios from 'axios';

interface User {
  id: number;
  role: string;
  organization_id: number;
}

interface AuthContextType {
  user: User | null;
  accessToken: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  register: (data: { email: string; password: string; organizationName?: string }) => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const api = axios.create({ baseURL: import.meta.env.VITE_AUTH_API_URL || 'http://localhost:4000/api', withCredentials: true });

  api.interceptors.request.use((config) => {
    if (accessToken) config.headers['Authorization'] = `Bearer ${accessToken}`;
    return config;
  });

  api.interceptors.response.use(
    (res) => res,
    async (error) => {
      const original = error.config;
      if (error.response?.status === 403 && !original._retry) {
        original._retry = true;
        try {
          const { data } = await api.post('/auth/refresh');
          setAccessToken(data.accessToken);
          original.headers['Authorization'] = `Bearer ${data.accessToken}`;
          return api(original);
        } catch (err) {
          setUser(null);
          setAccessToken(null);
        }
      }
      return Promise.reject(error);
    }
  );

  async function login(email: string, password: string) {
    const { data } = await api.post('/auth/login', { email, password });
    setAccessToken(data.accessToken);
    const decoded = JSON.parse(atob(data.accessToken.split('.')[1]));
    setUser(decoded);
  }

  async function register({ email, password, organizationName }: { email: string; password: string; organizationName?: string }) {
    await api.post('/auth/register', { email, password, organizationName });
  }

  async function logout() {
    await api.post('/auth/logout');
    setUser(null);
    setAccessToken(null);
  }

  useEffect(() => {
    // Optionally try refresh on mount
    (async () => {
      try {
        const { data } = await api.post('/auth/refresh');
        setAccessToken(data.accessToken);
        const decoded = JSON.parse(atob(data.accessToken.split('.')[1]));
        setUser(decoded);
      } catch {}
    })();
  }, []);

  return <AuthContext.Provider value={{ user, accessToken, login, logout, register }}>{children}</AuthContext.Provider>;
}
