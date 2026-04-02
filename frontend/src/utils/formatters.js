/**
 * Format a number as US currency string (e.g. "$1,234.56").
 * @param {number|string|null} amount
 * @returns {string}
 */
export function formatCurrency(amount) {
  if (amount === null || amount === undefined) return "N/A";
  const num = typeof amount === "string" ? parseFloat(amount) : amount;
  if (isNaN(num)) return "N/A";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
  }).format(num);
}

/**
 * Format an ISO date string into a human-readable date (e.g. "Jan 15, 2025").
 * @param {string|null} dateStr
 * @returns {string}
 */
export function formatDate(dateStr) {
  if (!dateStr) return "N/A";
  try {
    const date = new Date(dateStr + "T00:00:00"); // Avoid timezone shift
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateStr;
  }
}
