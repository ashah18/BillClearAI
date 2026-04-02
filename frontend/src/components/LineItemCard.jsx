import RiskBadge from "./RiskBadge.jsx";
import { formatCurrency } from "../utils/formatters.js";

/**
 * Displays a single medical bill line item card with code, description,
 * charged amount, risk level, and any error type detected.
 */
export default function LineItemCard({ item }) {
  const { cpt_code, hcpcs_code, description_plain, description_raw, charged_amount, risk_level, error_type } = item;

  const code = cpt_code || hcpcs_code || null;
  const description = description_plain || description_raw || "No description available";

  const errorLabels = {
    duplicate: "Possible Duplicate Charge",
    unbundled: "Possible Unbundling",
    upcoded: "Possible Upcoding",
    balance_billing: "Possible Balance Billing",
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {code && (
            <span className="inline-block bg-gray-100 text-gray-700 text-xs font-mono px-2 py-0.5 rounded mb-1">
              {code}
            </span>
          )}
          <p className="text-sm text-gray-900 font-medium leading-snug">{description}</p>
          {error_type && errorLabels[error_type] && (
            <p className="mt-1 text-xs text-red-600 font-medium">{errorLabels[error_type]}</p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="text-base font-semibold text-gray-900">
            {formatCurrency(charged_amount)}
          </span>
          <RiskBadge risk_level={risk_level} />
        </div>
      </div>
    </div>
  );
}
