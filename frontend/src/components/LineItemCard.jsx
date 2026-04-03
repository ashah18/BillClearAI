import { useState } from "react";
import RiskBadge from "./RiskBadge.jsx";
import { formatCurrency } from "../utils/formatters.js";

const ERROR_LABELS = {
  duplicate: "Possible Duplicate Charge",
  unbundled: "Possible Unbundling",
  upcoded: "Possible Upcoding",
  balance_billing: "Possible Balance Billing",
};

/**
 * Displays a single medical bill line item card. Clicking expands it to show
 * full detail: billing code, raw vs plain-English descriptions side by side,
 * charged vs regional average, and a contextual explanation of any flag.
 *
 * When selectable=true, a checkbox appears and onToggle is called on click.
 */
export default function LineItemCard({ item, selectable = false, selected = false, onToggle }) {
  const [expanded, setExpanded] = useState(false);

  const {
    cpt_code,
    hcpcs_code,
    icd10_codes,
    description_plain,
    description_raw,
    quantity,
    charged_amount,
    allowed_amount,
    regional_average,
    risk_level,
    error_type,
    flag_explanation,
  } = item;

  const code = cpt_code || hcpcs_code || null;

  return (
    <div
      className={`bg-white border rounded-lg shadow-sm transition-shadow ${
        selected
          ? "border-blue-400 ring-2 ring-blue-100"
          : expanded
          ? "border-blue-200 shadow-md"
          : "border-gray-200 hover:shadow-md"
      }`}
    >
      {/* Collapsed row — always visible */}
      <div className="p-4 flex items-start gap-3">
        {/* Checkbox for dispute selection mode */}
        {selectable && (
          <button
            type="button"
            onClick={() => onToggle?.(item.id)}
            className="mt-0.5 shrink-0 focus:outline-none"
            aria-label={selected ? "Deselect charge" : "Select charge"}
          >
            <div className={`h-5 w-5 rounded border-2 flex items-center justify-center transition-colors ${
              selected ? "bg-blue-600 border-blue-600" : "border-gray-300 bg-white"
            }`}>
              {selected && (
                <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
          </button>
        )}
        <button
          type="button"
          onClick={() => setExpanded((prev) => !prev)}
          className="flex-1 min-w-0 text-left flex items-start justify-between gap-4"
        >
        <div className="flex-1 min-w-0">
          {code && (
            <span className="inline-block bg-gray-100 text-gray-700 text-xs font-mono px-2 py-0.5 rounded mb-1">
              {code}
            </span>
          )}
          <p className="text-sm text-gray-900 font-medium leading-snug">
            {description_plain || description_raw || "No description available"}
          </p>
          {error_type && ERROR_LABELS[error_type] && (
            <p className="mt-1 text-xs text-red-600 font-medium">{ERROR_LABELS[error_type]}</p>
          )}
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <span className="text-base font-semibold text-gray-900">
            {formatCurrency(charged_amount)}
          </span>
          <RiskBadge risk_level={risk_level} />
        </div>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className={`h-4 w-4 text-gray-400 shrink-0 mt-1 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
        </button>
      </div>

      {/* Expanded detail panel */}
      {expanded && (
        <div className="border-t border-gray-100 px-4 pb-5 pt-4 space-y-4">

          {/* Billing codes */}
          <div className="flex flex-wrap gap-2 text-xs">
            {cpt_code && (
              <span className="bg-blue-50 text-blue-700 font-mono px-2 py-0.5 rounded">
                CPT: {cpt_code}
              </span>
            )}
            {hcpcs_code && (
              <span className="bg-purple-50 text-purple-700 font-mono px-2 py-0.5 rounded">
                HCPCS: {hcpcs_code}
              </span>
            )}
            {icd10_codes?.length > 0 && icd10_codes.map((code) => (
              <span key={code} className="bg-gray-100 text-gray-600 font-mono px-2 py-0.5 rounded">
                ICD-10: {code}
              </span>
            ))}
            {quantity > 1 && (
              <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                Qty: {quantity}
              </span>
            )}
          </div>

          {/* Description comparison */}
          {(description_raw || description_plain) && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                  On your bill
                </p>
                <p className="text-sm text-gray-700">
                  {description_raw || "—"}
                </p>
              </div>
              <div className="bg-blue-50 rounded-lg p-3">
                <p className="text-xs font-semibold text-blue-500 uppercase tracking-wide mb-1">
                  What it means
                </p>
                <p className="text-sm text-blue-900">
                  {description_plain || "—"}
                </p>
              </div>
            </div>
          )}

          {/* Amounts comparison */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="text-center bg-gray-50 rounded-lg p-3">
              <p className="text-base font-bold text-gray-900">{formatCurrency(charged_amount)}</p>
              <p className="text-xs text-gray-500 mt-0.5">Charged</p>
            </div>
            {allowed_amount != null && (
              <div className="text-center bg-gray-50 rounded-lg p-3">
                <p className="text-base font-bold text-gray-900">{formatCurrency(allowed_amount)}</p>
                <p className="text-xs text-gray-500 mt-0.5">Allowed</p>
              </div>
            )}
            {regional_average != null && (
              <div className="text-center bg-green-50 rounded-lg p-3">
                <p className="text-base font-bold text-green-700">{formatCurrency(regional_average)}</p>
                <p className="text-xs text-green-600 mt-0.5">Regional Avg</p>
              </div>
            )}
            {regional_average != null && (
              <div className="text-center bg-gray-50 rounded-lg p-3">
                <p className={`text-base font-bold ${parseFloat(charged_amount) > parseFloat(regional_average) ? "text-red-600" : "text-green-600"}`}>
                  {parseFloat(charged_amount) > parseFloat(regional_average)
                    ? `+${formatCurrency(parseFloat(charged_amount) - parseFloat(regional_average))}`
                    : `-${formatCurrency(parseFloat(regional_average) - parseFloat(charged_amount))}`}
                </p>
                <p className="text-xs text-gray-500 mt-0.5">vs. Regional</p>
              </div>
            )}
          </div>

          {/* Flag explanation */}
          {flag_explanation && (
            <div className={`rounded-lg p-3 text-sm ${risk_level === "red" ? "bg-red-50 text-red-800 border border-red-100" : "bg-yellow-50 text-yellow-800 border border-yellow-100"}`}>
              <p className="font-semibold text-xs uppercase tracking-wide mb-1 opacity-70">
                Why this was flagged
              </p>
              <p>{flag_explanation}</p>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
