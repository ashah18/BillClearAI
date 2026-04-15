import api from "./axios.js";

/**
 * Upload a new medical bill file for AI parsing and analysis.
 * @param {FormData} formData - Must contain a "file" field.
 */
export async function uploadBill(formData) {
  const response = await api.post("/bills/upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

/**
 * Get all bills for the authenticated user.
 */
export async function getBills() {
  const response = await api.get("/bills/");
  return response.data;
}

/**
 * Get full detail for a single bill including line items.
 * @param {number} id - Bill ID.
 */
export async function getBillDetail(id) {
  const response = await api.get(`/bills/${id}/`);
  return response.data;
}

/**
 * Re-run AI analysis on an existing bill.
 * @param {number} id - Bill ID.
 */
export async function analyzeBill(id) {
  const response = await api.post(`/bills/${id}/analyze/`);
  return response.data;
}

/**
 * Generate a dispute letter for flagged line items on a bill.
 * @param {number} id - Bill ID.
 * @param {number[]} [lineItemIds] - Optional specific line item IDs to dispute.
 */
export async function createDispute(id, lineItemIds = []) {
  const response = await api.post(`/bills/${id}/dispute/`, {
    line_item_ids: lineItemIds,
  });
  return response.data;
}

/**
 * Get all disputes for a bill.
 * @param {number} id - Bill ID.
 */
export async function getBillDisputes(id) {
  const response = await api.get(`/bills/${id}/disputes/`);
  return response.data;
}

/**
 * Get a specific dispute for a bill.
 * @param {number} id - Bill ID.
 * @param {number} disputeId - Dispute ID.
 */
export async function getDispute(id, disputeId) {
  const response = await api.get(`/bills/${id}/dispute/${disputeId}/`);
  return response.data;
}

/**
 * Update dispute status and/or savings_amount.
 * @param {number} billId - Bill ID.
 * @param {number} disputeId - Dispute ID.
 * @param {{ status?: string, savings_amount?: string }} data
 */
export async function updateDispute(billId, disputeId, data) {
  const response = await api.patch(`/bills/${billId}/dispute/${disputeId}/`, data);
  return response.data;
}

/**
 * Send a chat message about a specific bill.
 * @param {number} id - Bill ID.
 * @param {string} message - User's message text.
 */
export async function sendChatMessage(id, message) {
  const response = await api.post(`/bills/${id}/chat/`, { message });
  return response.data;
}

/**
 * Get the full chat history for a bill.
 * @param {number} id - Bill ID.
 */
export async function getChatHistory(id) {
  const response = await api.get(`/bills/${id}/chat/`);
  return response.data;
}

/**
 * Delete a bill by ID.
 * @param {number} id - Bill ID.
 */
export async function deleteBill(id) {
  await api.delete(`/bills/${id}/`);
}

/**
 * Get aggregate savings data for the authenticated user's dashboard.
 */
export async function getUserSavings() {
  const response = await api.get("/user/savings/");
  return response.data;
}
