import api from "./axios.js";

/**
 * Get the authenticated user's subscription plan, status, and current usage.
 */
export async function getSubscriptionStatus() {
  const response = await api.get("/billing/subscription/");
  return response.data;
}

/**
 * Create a Stripe Checkout session for upgrading to Pro.
 * @returns {Promise<{url: string}>} The Stripe Checkout URL to redirect to.
 */
export async function createCheckoutSession() {
  const response = await api.post("/billing/create-checkout-session/");
  return response.data;
}

/**
 * Create a Stripe Customer Portal session for managing an existing subscription.
 * @returns {Promise<{url: string}>} The Stripe Customer Portal URL to redirect to.
 */
export async function createPortalSession() {
  const response = await api.post("/billing/create-portal-session/");
  return response.data;
}
