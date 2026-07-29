"use client";

/** Client-side authentication store and API helpers.
 *
 * A single module-level store holds the JWT (mirrored to localStorage) and the
 * current user. Components subscribe through {@link useAuth} via
 * `useSyncExternalStore`, so updates never rely on `setState` inside effects.
 */
import { useEffect } from "react";
import { useSyncExternalStore } from "react";

import { ApiError } from "./api";
import type {
  AlertSubscription,
  AuthToken,
  AuthUser,
  PortfolioAnalysis,
  WatchlistItem,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const TOKEN_KEY = "psx-auth-token";

export type AuthStatus = "loading" | "ready";

export interface AuthState {
  token: string | null;
  user: AuthUser | null;
  status: AuthStatus;
}

const SERVER_STATE: AuthState = { token: null, user: null, status: "loading" };

let state: AuthState = SERVER_STATE;
const listeners = new Set<() => void>();

function emit(): void {
  for (const listener of listeners) listener();
}

function setState(patch: Partial<AuthState>): void {
  state = { ...state, ...patch };
  emit();
}

function subscribe(callback: () => void): () => void {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
}

function getSnapshot(): AuthState {
  return state;
}

function getServerSnapshot(): AuthState {
  return SERVER_STATE;
}

async function request<T>(
  path: string,
  init: RequestInit & { token?: string | null } = {}
): Promise<T> {
  const { token, headers, ...rest } = init;
  const authToken = token ?? state.token;
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
      ...rest,
      headers: {
        Accept: "application/json",
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...headers,
      },
    });
  } catch {
    throw new ApiError("Unable to reach the API. Is the backend running?", 503);
  }

  if (response.status === 204) {
    return undefined as T;
  }
  if (!response.ok) {
    let detail = `Request failed (${response.status}).`;
    try {
      const body = (await response.json()) as { detail?: unknown };
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      // Keep the generic message.
    }
    throw new ApiError(detail, response.status);
  }
  return (await response.json()) as T;
}

function fetchMe(token: string): Promise<AuthUser> {
  return request<AuthUser>("/auth/me", { token });
}

let bootstrapped = false;

/** Load any persisted token once on the client and hydrate the current user. */
function bootstrap(): void {
  if (bootstrapped) return;
  bootstrapped = true;

  let token: string | null = null;
  try {
    token = window.localStorage.getItem(TOKEN_KEY);
  } catch {
    token = null;
  }
  if (!token) {
    setState({ status: "ready" });
    return;
  }

  setState({ token });
  fetchMe(token)
    .then((user) => setState({ user, status: "ready" }))
    .catch(() => {
      clearToken();
      setState({ token: null, user: null, status: "ready" });
    });
}

function persistToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Ignore storage failures; the in-memory token still works this session.
  }
}

function clearToken(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Ignore.
  }
}

/** Register a new account, store the token, and load the profile. */
export async function register(
  email: string,
  password: string,
  fullName: string | null
): Promise<void> {
  const { access_token } = await request<AuthToken>("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  persistToken(access_token);
  const user = await fetchMe(access_token);
  setState({ token: access_token, user, status: "ready" });
}

/** Log in, store the token, and load the profile. */
export async function login(email: string, password: string): Promise<void> {
  const { access_token } = await request<AuthToken>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  persistToken(access_token);
  const user = await fetchMe(access_token);
  setState({ token: access_token, user, status: "ready" });
}

/** Clear the session. */
export function logout(): void {
  clearToken();
  setState({ token: null, user: null, status: "ready" });
}

export interface UseAuth extends AuthState {
  register: typeof register;
  login: typeof login;
  logout: typeof logout;
}

/** Subscribe to the shared auth state and trigger a one-time bootstrap. */
export function useAuth(): UseAuth {
  const snapshot = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot
  );
  useEffect(() => {
    bootstrap();
  }, []);
  return { ...snapshot, register, login, logout };
}

// --- Authenticated resource helpers -------------------------------------

export function getWatchlist(): Promise<WatchlistItem[]> {
  return request<WatchlistItem[]>("/watchlist");
}

export function addToWatchlist(symbol: string): Promise<WatchlistItem> {
  return request<WatchlistItem>("/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol }),
  });
}

export function removeFromWatchlist(symbol: string): Promise<void> {
  return request<void>(`/watchlist/${encodeURIComponent(symbol)}`, {
    method: "DELETE",
  });
}

export function getPortfolio(): Promise<PortfolioAnalysis> {
  return request<PortfolioAnalysis>("/portfolio");
}

export function upsertPosition(
  symbol: string,
  quantity: number,
  averageCost: number
): Promise<PortfolioAnalysis> {
  return request<PortfolioAnalysis>("/portfolio", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      symbol,
      quantity,
      average_cost: averageCost,
    }),
  });
}

export function removePosition(symbol: string): Promise<PortfolioAnalysis> {
  return request<PortfolioAnalysis>(
    `/portfolio/${encodeURIComponent(symbol)}`,
    { method: "DELETE" }
  );
}

export function getAlertSubscriptions(): Promise<AlertSubscription[]> {
  return request<AlertSubscription[]>("/alerts");
}

export function subscribeToAlerts(symbol: string): Promise<AlertSubscription> {
  return request<AlertSubscription>("/alerts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol }),
  });
}

export function unsubscribeFromAlerts(symbol: string): Promise<void> {
  return request<void>(`/alerts/${encodeURIComponent(symbol)}`, {
    method: "DELETE",
  });
}
