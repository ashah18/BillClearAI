import api from "./axios.js";

/**
 * Get the authenticated user's full profile.
 */
export async function getProfile() {
  const response = await api.get("/user/profile/");
  return response.data;
}

/**
 * Update the authenticated user's profile fields.
 * @param {object} data - Partial profile fields to update.
 */
export async function updateProfile(data) {
  const response = await api.put("/user/profile/", data);
  return response.data;
}
