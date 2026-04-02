import api from "./axios.js";

/**
 * Authenticate a user and return JWT access token + user data.
 */
export async function login(email, password) {
  const response = await api.post("/auth/login/", { email, password });
  return response.data;
}

/**
 * Register a new user account.
 */
export async function register(email, password, password2) {
  const response = await api.post("/auth/register/", { email, password, password2 });
  return response.data;
}

/**
 * Logout — invalidates the refresh token cookie server-side.
 */
export async function logout() {
  const response = await api.post("/auth/logout/");
  return response.data;
}

/**
 * Attempt to exchange the refresh token cookie for a new access token.
 * Used on app mount to restore an existing session.
 */
export async function refreshToken() {
  const response = await api.post("/auth/refresh/");
  return response.data;
}
