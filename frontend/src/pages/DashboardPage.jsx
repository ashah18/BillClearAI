import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { getBills, getUserSavings } from "../api/bills.js";
import Navbar from "../components/Navbar.jsx";
import { formatCurrency, formatDate } from "../utils/formatters.js";

const STATUS_STYLES = {
  new: "bg-blue-100 text-blue-700",
  reviewed: "bg-purple-100 text-purple-700",
  disputed: "bg-yellow-100 text-yellow-700",
  resolved: "bg-green-100 text-green-700",
};

/**
 * Dashboard page showing all of the user's bills and aggregate savings stats.
 */
export default function DashboardPage() {
  const [bills, setBills] = useState([]);
  const [savings, setSavings] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const [billsData, savingsData] = await Promise.all([getBills(), getUserSavings()]);
        setBills(billsData);
        setSavings(savingsData);
      } catch {
        setError("Failed to load your bills. Please refresh the page.");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Your Bills</h1>
          <Link
            to="/upload"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
          >
            Upload New Bill
          </Link>
        </div>

        {/* Savings summary */}
        {savings && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            {[
              { label: "Total Bills", value: savings.total_bills },
              { label: "Disputed", value: savings.disputed_bills },
              { label: "Resolved", value: savings.resolved_bills },
              { label: "Total Savings", value: formatCurrency(savings.total_savings) },
            ].map(({ label, value }) => (
              <div key={label} className="bg-white rounded-xl border border-gray-200 p-4 text-center">
                <p className="text-2xl font-bold text-gray-900">{value}</p>
                <p className="text-xs text-gray-500 mt-1">{label}</p>
              </div>
            ))}
          </div>
        )}

        {/* Bills list */}
        {isLoading && (
          <div className="text-center py-16 text-gray-400">Loading your bills...</div>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm border border-red-200">
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

        <div className="space-y-3">
          {bills.map((bill) => (
            <Link
              key={bill.id}
              to={`/bills/${bill.id}`}
              className="block bg-white border border-gray-200 rounded-xl p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold text-gray-900">
                    {bill.provider_name || "Unknown Provider"}
                  </p>
                  <p className="text-sm text-gray-500 mt-0.5">
                    Date of service: {formatDate(bill.date_of_service)}
                  </p>
                </div>
                <div className="flex items-center gap-4">
                  <span className="text-lg font-bold text-gray-900">
                    {formatCurrency(bill.total_charged)}
                  </span>
                  <span
                    className={`px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${STATUS_STYLES[bill.status] || "bg-gray-100 text-gray-600"}`}
                  >
                    {bill.status}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  );
}
