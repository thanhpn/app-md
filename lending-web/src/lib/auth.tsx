import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import * as api from "./api";

const ACCESS_KEY = "lending_access_token";
const REFRESH_KEY = "lending_refresh_token";

type AuthContextValue = {
  account: api.Account | null;
  accessToken: string | null;
  loading: boolean;
  login: (identifier: string, password: string) => Promise<void>;
  register: (input: { email: string; password: string; full_name: string; phone?: string }) => Promise<void>;
  logout: () => Promise<void>;
  /** Calls fn with the current access token; on a 401 it refreshes once and retries. */
  withFreshToken: <T,>(fn: (token: string) => Promise<T>) => Promise<T>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(() => localStorage.getItem(ACCESS_KEY));
  const [account, setAccount] = useState<api.Account | null>(null);
  const [loading, setLoading] = useState(true);

  function persist(pair: api.TokenPair) {
    localStorage.setItem(ACCESS_KEY, pair.access_token);
    localStorage.setItem(REFRESH_KEY, pair.refresh_token);
    setAccessToken(pair.access_token);
  }

  function clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    setAccessToken(null);
    setAccount(null);
  }

  useEffect(() => {
    (async () => {
      const token = localStorage.getItem(ACCESS_KEY);
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        setAccount(await api.getMe(token));
      } catch {
        const rt = localStorage.getItem(REFRESH_KEY);
        if (!rt) {
          clear();
        } else {
          try {
            const pair = await api.refresh(rt);
            persist(pair);
            setAccount(await api.getMe(pair.access_token));
          } catch {
            clear();
          }
        }
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function login(identifier: string, password: string) {
    const pair = await api.login({ identifier, password });
    persist(pair);
    setAccount(await api.getMe(pair.access_token));
  }

  async function register(input: { email: string; password: string; full_name: string; phone?: string }) {
    await api.register(input);
    await login(input.email, input.password);
  }

  async function logout() {
    const rt = localStorage.getItem(REFRESH_KEY);
    if (rt) {
      try {
        await api.logout(rt);
      } catch {
        // already invalid/expired — fine, we're clearing local state regardless.
      }
    }
    clear();
  }

  async function withFreshToken<T>(fn: (token: string) => Promise<T>): Promise<T> {
    if (!accessToken) {
      throw new api.ApiError(401, "UNAUTHORIZED", "Bạn cần đăng nhập trước.");
    }
    try {
      return await fn(accessToken);
    } catch (err) {
      if (err instanceof api.ApiError && err.status === 401) {
        const rt = localStorage.getItem(REFRESH_KEY);
        if (rt) {
          const pair = await api.refresh(rt);
          persist(pair);
          return await fn(pair.access_token);
        }
      }
      throw err;
    }
  }

  return (
    <AuthContext.Provider value={{ account, accessToken, loading, login, register, logout, withFreshToken }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
