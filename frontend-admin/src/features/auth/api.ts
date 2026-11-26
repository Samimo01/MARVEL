import { apiRequest } from "@/app/api-client";
import type { UserSession } from "@/app/auth/session-context";
import type { AuthResponse, LoginPayload } from "@/features/auth/types";

export function login(payload: LoginPayload) {
  return apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    body: {
      email: payload.email.trim().toLowerCase(),
      password: payload.password,
      remember_me: payload.rememberMe,
    },
  });
}

export function getCurrentSession(signal?: AbortSignal) {
  return apiRequest<UserSession>("/users/me", { signal });
}

export function logout() {
  return apiRequest<{ message: string }>("/auth/logout", { method: "POST" });
}
