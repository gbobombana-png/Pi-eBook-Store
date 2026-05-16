const API = "https://pi-ebook-store-production.up.railway.app";
const TOKEN_KEY = "sp_token";
const USER_KEY = "sp_user";

export interface AuthUser {
  username: string;
  is_admin: boolean;
}

export async function login(username: string, password: string): Promise<AuthUser> {
  const res = await fetch(`${API}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Erreur réseau" }));
    throw new Error(err.detail || "Connexion échouée");
  }
  const data = await res.json();
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, data.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify({ username: data.username, is_admin: data.is_admin }));
  }
  return { username: data.username, is_admin: data.is_admin };
}

export async function register(username: string, email: string, password: string): Promise<void> {
  const res = await fetch(`${API}/api/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Erreur réseau" }));
    throw new Error(err.detail || "Inscription échouée");
  }
}

export function logout(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getUser(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
