import { useState, useEffect, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { getBills, getUserSavings, deleteBill } from "../api/bills.js";
import Navbar from "../components/Navbar.jsx";
import { formatCurrency, formatDate } from "../utils/formatters.js";

const STATUS_STYLES = {
  new: "bg-blue-100 text-blue-700",
  reviewed: "bg-purple-100 text-purple-700",
  disputed: "bg-yellow-100 text-yellow-700",
  resolved: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-600",
};

export default function DashboardPage() {
  const navigate = useNavigate();

  const [bills, setBills] = useState([]);
  const [confirmedSavings, setConfirmedSavings] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  // Multi-select state
  const [selectMode, setSelectMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [isDeleting, setIsDeleting] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  // Stats and savings derived from local bills state — update instantly on delete
  const stats = useMemo(() => ({
    total_bills: bills.length,
    disputed_bills: bills.filter((b) => b.status === "disputed").length,
    resolved_bills: bills.filter((b) => b.status === "resolved").length,
    total_potential_savings: bills.reduce((sum, b) => sum + (b.potential_savings || 0), 0),
  }), [bills]);

  useEffect(() => {
    async function load() {
      try {
        const [billsData, savingsData] = await Promise.all([getBills(), getUserSavings()]);
        setBills(billsData);
        setConfirmedSavings(savingsData.confirmed_savings ?? 0);
      } catch {
        setError("Failed to load your bills. Please refresh the page.");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  function exitSelectMode() {
    setSelectMode(false);
    setSelectedIds(new Set());
  }

  function toggleSelect(billId) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.has(billId) ? next.delete(billId) : next.add(billId);
      return next;
    });
  }

  function toggleSelectAll() {
    if (selectedIds.size === bills.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(bills.map((b) => b.id)));
    }
  }

  async function handleDeleteSelected() {
    if (selectedIds.size === 0) return;
    if (!window.confirm(`Delete ${selectedIds.size} bill${selectedIds.size !== 1 ? "s" : ""}? This cannot be undone.`)) return;
    setIsDeleting(true);
    setError("");
    try {
      await Promise.all([...selectedIds].map((id) => deleteBill(id)));
      setBills((prev) => prev.filter((b) => !selectedIds.has(b.id)));
      exitSelectMode();
    } catch {
      setError("Failed to delete some bills. Please try again.");
    } finally {
      setIsDeleting(false);
    }
  }

  async function handleDeleteSingle(e, billId) {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm("Delete this bill? This cannot be undone.")) return;
    setDeletingId(billId);
    setError("");
    try {
      await deleteBill(billId);
      setBills((prev) => prev.filter((b) => b.id !== billId));
    } catch {
      setError("Failed to delete bill. Please try again.");
    } finally {
      setDeletingId(null);
    }
  }

  function handleRowClick(e, bill) {
    if (selectMode) {
      toggleSelect(bill.id);
    } else {
      navigate(`/bills/${bill.id}`);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Your Bills</h1>
          <div className="flex items-center gap-3">
            {bills.length > 0 && (
              <button
                onClick={selectMode ? exitSelectMode : () => setSelectMode(true)}
                className="text-sm text-gray-600 border border-gray-300 px-3 py-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {selectMode ? "Cancel" : "Select"}
              </button>
            )}
            <Link
              to="/upload"
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Upload New Bill
            </Link>
          </div>
        </div>

        {/* Stats — derived from local state, update instantly */}
        {!isLoading && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            {[
              { label: "Total Bills", value: stats.total_bills },
              { label: "Disputed", value: stats.disputed_bills },
              { label: "Resolved", value: stats.resolved_bills },
            ].map(({ label, value }) => (
              <div key={label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                <p className="text-2xl font-bold text-gray-900">{value}</p>
                <p className="text-xs text-gray-500 mt-1">{label}</p>
              </div>
            ))}
            {/* Potential Savings card */}
            <div className="bg-green-50 rounded-xl border border-green-200 p-4 text-center">
              <p className="text-lg font-bold text-green-700 leading-tight">
                Up to {formatCurrency(stats.total_potential_savings)}
              </p>
              <p className="text-xs text-green-600 mt-1">Total Potential Savings Across All Bills</p>
              {confirmedSavings > 0 && (
                <p className="text-xs text-green-500 mt-1.5">
                  {formatCurrency(confirmedSavings)} confirmed
                </p>
              )}
            </div>
          </div>
        )}

        {isLoading && (
          <div className="text-center py-16 text-gray-400">Loading your bills...</div>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm border border-red-200 mb-4">
            {error}
          </div>
        )}

        {!isLoading && bills.length === 0 && !error && (
          <div className="text-center py-16">
            <p className="text-gray-500 text-sm">No bills uploaded yet.</p>
            <Link to="/upload" className="text-blue-600 text-sm hover:underline mt-2 inline-block">
              Upload your first bill
            </Link>
          </div>
        )}

        {/* Select-all row */}
        {selectMode && bills.length > 0 && (
          <div className="flex items-center gap-3 mb-2 px-1">
            <button
              onClick={toggleSelectAll}
              className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
            >
              <div className={`h-4 w-4 rounded border-2 flex items-center justify-center transition-colors ${
                selectedIds.size === bills.length
                  ? "bg-blue-600 border-blue-600"
                  : selectedIds.size > 0
                  ? "bg-blue-200 border-blue-400"
                  : "border-gray-300 bg-white"
              }`}>
                {selectedIds.size > 0 && (
                  <svg className="h-2.5 w-2.5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>
              {selectedIds.size === bills.length ? "Deselect all" : "Select all"}
            </button>
            {selectedIds.size > 0 && (
              <span className="text-sm text-gray-400">
                {selectedIds.size} of {bills.length} selected
              </span>
            )}
          </div>
        )}

        <div className="space-y-3">
          {bills.map((bill) => {
            const isSelected = selectedIds.has(bill.id);
            return (
              <div
                key={bill.id}
                onClick={(e) => handleRowClick(e, bill)}
                className={`bg-white border rounded-xl p-5 transition-all cursor-pointer ${
                  selectMode
                    ? isSelected
                      ? "border-blue-400 ring-2 ring-blue-100 shadow-sm"
                      : "border-gray-200 hover:border-gray-300"
                    : "border-gray-200 hover:shadow-md"
                }`}
              >
                <div className="flex items-center gap-3">
                  {/* Checkbox (select mode only) */}
                  {selectMode && (
                    <div className={`shrink-0 h-5 w-5 rounded border-2 flex items-center justify-center transition-colors ${
                      isSelected ? "bg-blue-600 border-blue-600" : "border-gray-300 bg-white"
                    }`}>
                      {isSelected && (
                        <svg className="h-3 w-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                    </div>
                  )}

                  {/* Bill info */}
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 truncate">
                      {bill.provider_name || "Unknown Provider"}
                    </p>
                    <p className="text-sm text-gray-500 mt-0.5">
                      Date of service: {formatDate(bill.date_of_service)}
                    </p>
                    {bill.potential_savings > 0 && (
                      <p className="text-xs text-green-600 font-medium mt-1">
                        Up to {formatCurrency(bill.potential_savings)} in potential savings
                      </p>
                    )}
                    {bill.confirmed_savings > 0 && (
                      <p className="text-xs text-green-500 font-medium mt-0.5">
                        {formatCurrency(bill.confirmed_savings)} confirmed
                      </p>
                    )}
                  </div>

                  {/* Right side */}
                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-900">
                        {bill.total_charged != null
                          ? formatCurrency(bill.total_charged)
                          : formatCurrency(
                              (bill.line_items || []).reduce((sum, i) => {
                                const amt = parseFloat(i.charged_amount || 0);
                                return sum + (amt > 0 ? amt : 0);
                              }, 0)
                            )}
                      </p>
                      <p className="text-xs text-gray-400">Total Charged</p>
                    </div>
                    <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_STYLES[bill.status] || "bg-gray-100 text-gray-600"}`}>
                      {bill.status}
                    </span>
                    {/* Single-delete (hidden in select mode) */}
                    {!selectMode && (
                      <button
                        onClick={(e) => handleDeleteSingle(e, bill.id)}
                        disabled={deletingId === bill.id}
                        className="text-gray-400 hover:text-red-500 transition-colors disabled:opacity-50 p-1"
                        title="Delete bill"
                      >
                        {deletingId === bill.id ? (
                          <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                          </svg>
                        ) : (
                          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </main>

      {/* Sticky delete bar (select mode) */}
      {selectMode && (
        <div className="fixed bottom-0 inset-x-0 bg-white border-t border-gray-200 shadow-lg z-50">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
            <p className="text-sm text-gray-700">
              <span className="font-semibold">{selectedIds.size}</span> bill{selectedIds.size !== 1 ? "s" : ""} selected
            </p>
            <div className="flex gap-3">
              <button
                onClick={exitSelectMode}
                className="text-sm text-gray-600 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteSelected}
                disabled={isDeleting || selectedIds.size === 0}
                className="text-sm bg-red-600 text-white px-5 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors font-medium"
              >
                {isDeleting ? "Deleting..." : `Delete ${selectedIds.size > 0 ? selectedIds.size : ""} bill${selectedIds.size !== 1 ? "s" : ""}`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
