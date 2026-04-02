import { useState, useEffect, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  getBillDetail,
  getChatHistory,
  sendChatMessage,
  createDispute,
  analyzeBill,
} from "../api/bills.js";
import Navbar from "../components/Navbar.jsx";
import LineItemCard from "../components/LineItemCard.jsx";
import { formatCurrency, formatDate } from "../utils/formatters.js";

/**
 * Bill detail page showing provider info, line items with risk levels,
 * and a chat interface for asking questions about the bill.
 */
export default function BillDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [bill, setBill] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isDisputing, setIsDisputing] = useState(false);
  const [error, setError] = useState("");
  const [pageLoading, setPageLoading] = useState(true);

  const chatBottomRef = useRef(null);

  useEffect(() => {
    async function load() {
      try {
        const [billData, historyData] = await Promise.all([
          getBillDetail(id),
          getChatHistory(id),
        ]);
        setBill(billData);
        setChatMessages(historyData);
      } catch {
        setError("Failed to load bill details.");
      } finally {
        setPageLoading(false);
      }
    }
    load();
  }, [id]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  async function handleSendMessage(e) {
    e.preventDefault();
    const message = chatInput.trim();
    if (!message) return;

    // Optimistically show the user message
    setChatMessages((prev) => [
      ...prev,
      { id: Date.now(), role: "user", content: message, created_at: new Date().toISOString() },
    ]);
    setChatInput("");
    setIsChatLoading(true);

    try {
      const assistantMsg = await sendChatMessage(id, message);
      setChatMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setChatMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          role: "assistant",
          content: "Sorry, I couldn't process your message. Please try again.",
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsChatLoading(false);
    }
  }

  async function handleReanalyze() {
    setIsAnalyzing(true);
    try {
      const updated = await analyzeBill(id);
      setBill(updated);
    } catch {
      setError("Re-analysis failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  async function handleDispute() {
    setIsDisputing(true);
    try {
      const dispute = await createDispute(id);
      navigate(`/bills/${id}?dispute=${dispute.id}`);
      setError("");
      alert(`Dispute letter created successfully! Dispute ID: ${dispute.id}`);
    } catch {
      setError("Failed to generate dispute letter. Please try again.");
    } finally {
      setIsDisputing(false);
    }
  }

  if (pageLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="text-center py-24 text-gray-400">Loading bill...</div>
      </div>
    );
  }

  if (error && !bill) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-2xl mx-auto px-4 py-12">
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg border border-red-200 text-sm">
            {error}
          </div>
        </div>
      </div>
    );
  }

  const redItems = bill?.line_items?.filter((i) => i.risk_level === "red") || [];
  const hasIssues = redItems.length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {error && (
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg border border-red-200 text-sm">
            {error}
          </div>
        )}

        {/* Bill summary */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                {bill.provider_name || "Unknown Provider"}
              </h1>
              <p className="text-sm text-gray-500 mt-0.5">
                {bill.facility_type} &bull; Date of service: {formatDate(bill.date_of_service)}
              </p>
            </div>
            <span className="capitalize text-xs font-medium bg-purple-100 text-purple-700 px-2.5 py-1 rounded-full">
              {bill.status}
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4 mt-6">
            {[
              { label: "Total Charged", value: formatCurrency(bill.total_charged) },
              { label: "Total Allowed", value: formatCurrency(bill.total_allowed) },
              { label: "Your Responsibility", value: formatCurrency(bill.patient_responsibility) },
            ].map(({ label, value }) => (
              <div key={label} className="text-center">
                <p className="text-lg font-bold text-gray-900">{value}</p>
                <p className="text-xs text-gray-500">{label}</p>
              </div>
            ))}
          </div>

          <div className="flex gap-3 mt-6">
            <button
              onClick={handleReanalyze}
              disabled={isAnalyzing}
              className="text-sm text-gray-600 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              {isAnalyzing ? "Re-analyzing..." : "Re-analyze"}
            </button>
            {hasIssues && (
              <button
                onClick={handleDispute}
                disabled={isDisputing}
                className="text-sm bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {isDisputing ? "Generating..." : `Dispute ${redItems.length} Issue${redItems.length !== 1 ? "s" : ""}`}
              </button>
            )}
          </div>
        </div>

        {/* Line items */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">
            Line Items ({bill.line_items?.length || 0})
          </h2>
          {bill.line_items?.length > 0 ? (
            <div className="space-y-3">
              {bill.line_items.map((item) => (
                <LineItemCard key={item.id} item={item} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No line items extracted yet.</p>
          )}
        </div>

        {/* Chat interface */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Ask about this bill</h2>
            <p className="text-sm text-gray-500">Get plain-English explanations from AI</p>
          </div>

          {/* Messages */}
          <div className="px-6 py-4 space-y-4 max-h-80 overflow-y-auto">
            {chatMessages.length === 0 && (
              <p className="text-sm text-gray-400 text-center py-6">
                Ask a question about any charge on this bill.
              </p>
            )}
            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-sm px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-blue-600 text-white rounded-br-sm"
                      : "bg-gray-100 text-gray-800 rounded-bl-sm"
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isChatLoading && (
              <div className="flex justify-start">
                <div className="bg-gray-100 text-gray-500 px-4 py-2.5 rounded-2xl rounded-bl-sm text-sm">
                  Thinking...
                </div>
              </div>
            )}
            <div ref={chatBottomRef} />
          </div>

          {/* Input */}
          <form
            onSubmit={handleSendMessage}
            className="px-4 py-4 border-t border-gray-100 flex gap-3"
          >
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              disabled={isChatLoading}
              placeholder="E.g. What is CPT code 99213?"
              className="flex-1 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={isChatLoading || !chatInput.trim()}
              className="bg-blue-600 text-white px-5 py-2.5 rounded-xl text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              Send
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
