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

/**
 * Fetch the authenticated user's profile data.
 * Used by loginWithToken after OAuth to get user details.
 */
export async function getProfile() {
  const response = await api.get("/user/profile/");
  return response.data;
}

/**
 * Request a password reset email for the given address.
 * Never reveals whether the email exists.
 */
export async function requestPasswordReset(email) {
  const response = await api.post("/auth/password-reset/", { email });
  return response.data;
}

/**
 * Confirm a password reset using the uid/token from the reset link.
 */
export async function confirmPasswordReset(uid, token, new_password) {
  const response = await api.post("/auth/password-reset/confirm/", { uid, token, new_password });
  return response.data;
}

/**
 * Change the current user's password (requires current password for verification).
 * Returns a fresh access token to keep the session alive.
 */
export async function changePassword(current_password, new_password) {
  const response = await api.post("/auth/change-password/", { current_password, new_password });
  return response.data;
}

/**
 * Resend the email verification link.
 * Pass an email to resend without being logged in (e.g. from the login page);
 * omit it to resend for the currently authenticated user (e.g. dashboard banner).
 */
export async function resendVerification(email) {
  const body = email ? { email } : {};
  const response = await api.post("/auth/resend-verification/", body);
  return response.data;
}
