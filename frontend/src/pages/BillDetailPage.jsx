import { useState, useEffect, useRef, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { saveAs } from "file-saver";
import api from "../api/axios.js";
import {
  getBillDetail,
  getBillDisputes,
  getChatHistory,
  sendChatMessage,
  createDispute,
  updateDispute,
  analyzeBill,
  deleteBill,
} from "../api/bills.js";
import Navbar from "../components/Navbar.jsx";
import LineItemCard from "../components/LineItemCard.jsx";
import { formatCurrency, formatDate } from "../utils/formatters.js";

const DISPUTE_STATUS_STYLES = {
  draft: "bg-gray-100 text-gray-600",
  sent: "bg-blue-100 text-blue-700",
  acknowledged: "bg-purple-100 text-purple-700",
  resolved: "bg-green-100 text-green-700",
  denied: "bg-red-100 text-red-700",
};

/**
 * Bill detail page showing provider info, line items with risk levels,
 * and a chat interface for asking questions about the bill.
 */
export default function BillDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [bill, setBill] = useState(null);
  const [disputes, setDisputes] = useState([]);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isReuploading, setIsReuploading] = useState(false);
  const [isDisputing, setIsDisputing] = useState(false);
  const [error, setError] = useState("");
  const [pageLoading, setPageLoading] = useState(true);

  // Dispute selection mode
  const [disputeMode, setDisputeMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [downloadingDisputeId, setDownloadingDisputeId] = useState(null);
  const [updatingDisputeId, setUpdatingDisputeId] = useState(null);
  const [resolvingDisputeId, setResolvingDisputeId] = useState(null);
  const [savingsInput, setSavingsInput] = useState("");

  const chatBottomRef = useRef(null);

  // IDs of every line item that appears in at least one dispute (any status)
  const disputedItemIds = useMemo(() => {
    const ids = new Set();
    disputes.forEach((d) => (d.line_items || []).forEach((li) => ids.add(li.id)));
    return ids;
  }, [disputes]);

  useEffect(() => {
    async function load() {
      try {
        const [billData, historyData, disputesData] = await Promise.all([
          getBillDetail(id),
          getChatHistory(id),
          getBillDisputes(id),
        ]);
        setBill(billData);
        setChatMessages(historyData);
        setDisputes(disputesData);
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

  function enterDisputeMode() {
    // Pre-select all red items
    const redIds = new Set(
      (bill?.line_items || []).filter((i) => i.risk_level === "red").map((i) => i.id)
    );
    setSelectedIds(redIds);
    setDisputeMode(true);
  }

  function toggleItemSelection(itemId) {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(itemId)) next.delete(itemId);
      else next.add(itemId);
      return next;
    });
  }

  async function handleSubmitDispute() {
    if (selectedIds.size === 0) return;
    setIsDisputing(true);
    try {
      const dispute = await createDispute(id, [...selectedIds]);
      setDisputes((prev) => [dispute, ...prev]);
      setDisputeMode(false);
      setSelectedIds(new Set());
      navigate(`/bills/${id}/disputes/${dispute.id}`);
    } catch {
      setError("Failed to generate dispute letter. Please try again.");
    } finally {
      setIsDisputing(false);
    }
  }

  async function handleDownloadDispute(disputeId) {
    setDownloadingDisputeId(disputeId);
    try {
      const response = await api.get(
        `/bills/${id}/dispute/${disputeId}/download/`,
        { responseType: "blob" }
      );
      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      });
      saveAs(blob, `dispute-letter-${disputeId}.docx`);
    } catch {
      // download failed silently
    } finally {
      setDownloadingDisputeId(null);
    }
  }

  async function handleUpdateDispute(disputeId, payload) {
    setUpdatingDisputeId(disputeId);
    try {
      const updated = await updateDispute(id, disputeId, payload);
      setDisputes((prev) => prev.map((d) => (d.id === disputeId ? updated : d)));
    } catch {
      setError("Failed to update dispute. Please try again.");
    } finally {
      setUpdatingDisputeId(null);
    }
  }

  async function handleResolveDispute(disputeId) {
    const payload = { status: "resolved" };
    if (savingsInput.trim() !== "") {
      payload.savings_amount = savingsInput.trim();
    }
    await handleUpdateDispute(disputeId, payload);
    setResolvingDisputeId(null);
    setSavingsInput("");
  }

  async function handleSendMessage(e) {
    e.preventDefault();
    const message = chatInput.trim();
    if (!message) return;

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

  async function handleReupload() {
    setIsReuploading(true);
    try {
      await deleteBill(id);
      navigate("/upload");
    } catch {
      setError("Failed to delete bill. Please try again.");
      setIsReuploading(false);
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

  const flaggedItems = (bill?.line_items || []).filter(
    (i) => i.risk_level === "red" || i.risk_level === "yellow"
  );
  const hasIssues = flaggedItems.length > 0;

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 pb-28 sm:pb-8 space-y-8">
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

          {(() => {
            // Negative line items (credits, payments) are shown as line items
            // but excluded from fallback totals — only count positive charges.
            const lineItemTotal = (bill.line_items || []).reduce((sum, i) => {
              const amt = parseFloat(i.charged_amount || 0);
              return sum + (amt > 0 ? amt : 0);
            }, 0);
            const totalCharged = bill.total_charged ?? lineItemTotal;
            const totalResponsibility = bill.patient_responsibility ?? lineItemTotal;
            const hasAllowed = bill.total_allowed != null;

            const stats = [
              { label: "Total Charged", value: formatCurrency(totalCharged) },
              ...(hasAllowed ? [{ label: "Total Allowed", value: formatCurrency(bill.total_allowed) }] : []),
              { label: "Your Responsibility", value: formatCurrency(totalResponsibility) },
            ];

            return (
              <div className={`grid gap-4 mt-6 ${stats.length === 3 ? "grid-cols-3" : "grid-cols-2"}`}>
                {stats.map(({ label, value }) => (
                  <div key={label} className="text-center">
                    <p className="text-lg font-bold text-gray-900">{value}</p>
                    <p className="text-xs text-gray-500">{label}</p>
                  </div>
                ))}
              </div>
            );
          })()}

          {/* Potential savings banner */}
          {(() => {
            const confirmedSavings = disputes.reduce((sum, d) => {
              if (d.status === "resolved" && d.savings_amount != null) {
                return sum + parseFloat(d.savings_amount);
              }
              return sum;
            }, 0);
            const hasPotential = bill.potential_savings > 0 && bill.status !== "failed";
            const hasConfirmed = confirmedSavings > 0;
            if (!hasPotential && !hasConfirmed) return null;
            return (
              <div className="mt-4 bg-green-50 border border-green-200 rounded-xl px-4 py-3 text-center">
                {hasPotential && (
                  <>
                    <p className="text-sm font-semibold text-green-700">
                      Up to {formatCurrency(bill.potential_savings)} in potential savings identified
                    </p>
                    <p className="text-xs text-green-600 mt-0.5">
                      Based on pricing data and billing error analysis — dispute flagged charges to recover this amount
                    </p>
                  </>
                )}
                {hasConfirmed && (
                  <p className={`text-sm font-semibold text-green-700 ${hasPotential ? "mt-2 pt-2 border-t border-green-200" : ""}`}>
                    {formatCurrency(confirmedSavings)} confirmed savings recovered
                  </p>
                )}
              </div>
            );
          })()}

          {/* Failed parse — hard error */}
          {bill.status === "failed" && (
            <div className="mt-5 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
              <p className="text-sm font-semibold text-red-700 mb-0.5">Trouble reading this bill</p>
              <p className="text-sm text-red-600">
                {bill.error_message ||
                  "We had trouble reading this bill. This could be because the image is blurry, at an angle, or doesn't contain itemized charges. Try uploading a clearer photo or a PDF version of your itemized bill."}
              </p>
            </div>
          )}
          {/* Soft parse warning (payment reminder, low confidence) */}
          {bill.status !== "failed" && bill.parse_status === "warning" && (
            <div className="mt-5 bg-yellow-50 border border-yellow-200 rounded-xl px-4 py-3">
              <p className="text-sm font-semibold text-yellow-800 mb-0.5">Heads up</p>
              <p className="text-sm text-yellow-700">{bill.parse_message}</p>
            </div>
          )}

          <div className="flex gap-3 mt-6">
            <button
              onClick={handleReanalyze}
              disabled={isAnalyzing || disputeMode}
              className="text-sm text-gray-600 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              {isAnalyzing ? "Re-analyzing..." : "Re-analyze"}
            </button>
            <button
              onClick={handleReupload}
              disabled={isReuploading || disputeMode}
              className="text-sm text-gray-600 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              {isReuploading ? "Deleting..." : "Re-upload"}
            </button>
            {hasIssues && !disputeMode && (
              <button
                onClick={enterDisputeMode}
                className="text-sm bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
              >
                Dispute Charges
              </button>
            )}
          </div>
        </div>

        {/* Existing disputes */}
        {disputes.length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-900 mb-3">Disputes</h2>
            <div className="space-y-2">
              {disputes.map((d) => (
                <div
                  key={d.id}
                  className="bg-white border border-gray-200 rounded-xl px-5 py-3.5 hover:shadow-sm transition-shadow"
                >
                  <div className="flex items-center justify-between">
                    <Link to={`/bills/${id}/disputes/${d.id}`} className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900">
                        Dispute #{d.id} &mdash; {d.line_items.length} charge{d.line_items.length !== 1 ? "s" : ""}
                      </p>
                      <p className="text-xs text-gray-400 mt-0.5">
                        {formatDate(d.created_at)}
                        {d.status === "resolved" && d.savings_amount != null && (
                          <span className="ml-2 text-green-600 font-medium">
                            {formatCurrency(d.savings_amount)} confirmed
                          </span>
                        )}
                      </p>
                    </Link>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className={`capitalize text-xs font-medium px-2.5 py-1 rounded-full ${DISPUTE_STATUS_STYLES[d.status] || "bg-gray-100 text-gray-600"}`}>
                        {d.status}
                      </span>
                      <button
                        onClick={() => handleDownloadDispute(d.id)}
                        disabled={downloadingDisputeId === d.id || !d.letter_pdf}
                        className="flex items-center gap-1 text-xs text-blue-600 border border-blue-200 px-2.5 py-1.5 rounded-lg hover:bg-blue-50 disabled:opacity-50 transition-colors"
                      >
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        {downloadingDisputeId === d.id ? "Preparing…" : "Download"}
                      </button>
                      {/* Status action buttons */}
                      {d.status === "draft" && d.letter_pdf && (
                        <button
                          onClick={() => handleUpdateDispute(d.id, { status: "sent" })}
                          disabled={updatingDisputeId === d.id}
                          className="text-xs text-gray-700 border border-gray-300 px-2.5 py-1.5 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
                        >
                          {updatingDisputeId === d.id ? "Saving…" : "Mark as Sent"}
                        </button>
                      )}
                      {d.status === "sent" && (
                        <>
                          <button
                            onClick={() => { setResolvingDisputeId(d.id); setSavingsInput(""); }}
                            disabled={updatingDisputeId === d.id}
                            className="text-xs text-green-700 border border-green-300 px-2.5 py-1.5 rounded-lg hover:bg-green-50 disabled:opacity-50 transition-colors"
                          >
                            Mark as Resolved
                          </button>
                          <button
                            onClick={() => handleUpdateDispute(d.id, { status: "denied" })}
                            disabled={updatingDisputeId === d.id}
                            className="text-xs text-red-600 border border-red-200 px-2.5 py-1.5 rounded-lg hover:bg-red-50 disabled:opacity-50 transition-colors"
                          >
                            {updatingDisputeId === d.id ? "Saving…" : "Mark as Denied"}
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Inline resolve form */}
                  {resolvingDisputeId === d.id && (
                    <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-3">
                      <label className="text-xs text-gray-600 shrink-0">
                        Amount credited back (optional):
                      </label>
                      <div className="relative">
                        <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-xs">$</span>
                        <input
                          type="number"
                          min="0"
                          step="0.01"
                          value={savingsInput}
                          onChange={(e) => setSavingsInput(e.target.value)}
                          placeholder="0.00"
                          className="pl-5 pr-3 py-1.5 border border-gray-300 rounded-lg text-xs w-28 focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        />
                      </div>
                      <button
                        onClick={() => handleResolveDispute(d.id)}
                        disabled={updatingDisputeId === d.id}
                        className="text-xs bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                      >
                        {updatingDisputeId === d.id ? "Saving…" : "Confirm"}
                      </button>
                      <button
                        onClick={() => { setResolvingDisputeId(null); setSavingsInput(""); }}
                        className="text-xs text-gray-500 hover:text-gray-700"
                      >
                        Cancel
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Line items */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              Line Items ({bill.line_items?.length || 0})
            </h2>
            {disputeMode && (
              <p className="text-sm text-gray-500">
                Select the charges you want to dispute
              </p>
            )}
          </div>

          {bill.line_items?.length > 0 ? (
            <div className="space-y-3">
              {bill.line_items.map((item) => {
                const isSelectable = disputeMode && (item.risk_level === "red" || item.risk_level === "yellow");
                return (
                  <LineItemCard
                    key={item.id}
                    item={item}
                    selectable={isSelectable}
                    selected={selectedIds.has(item.id)}
                    onToggle={toggleItemSelection}
                    disputed={disputedItemIds.has(item.id)}
                  />
                );
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-500">No line items extracted yet.</p>
          )}
        </div>

        {/* Chat interface */}
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm">
          <div className="px-6 py-4 border-b border-gray-100">
            <h2 className="text-lg font-semibold text-gray-900">Ask about this bill</h2>
            <p className="text-sm text-gray-500">Get plain-English explanations from AI</p>
          </div>

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
                  {msg.role === "assistant" ? (
                    <ReactMarkdown
                      components={{
                        p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                        strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                        ul: ({ children }) => <ul className="list-disc list-inside mt-1 space-y-0.5">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal list-inside mt-1 space-y-0.5">{children}</ol>,
                        li: ({ children }) => <li>{children}</li>,
                        h1: ({ children }) => <p className="font-bold text-base mb-1">{children}</p>,
                        h2: ({ children }) => <p className="font-bold mb-1">{children}</p>,
                        h3: ({ children }) => <p className="font-semibold mb-0.5">{children}</p>,
                      }}
                    >
                      {msg.content}
                    </ReactMarkdown>
                  ) : (
                    msg.content
                  )}
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

          <form
            onSubmit={handleSendMessage}
            className="px-4 py-3 border-t border-gray-200 flex gap-3 bg-white fixed bottom-0 left-0 right-0 z-20 sm:static sm:z-auto sm:py-4 sm:border-gray-100"
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

      {/* Dispute selection action bar */}
      {disputeMode && (
        <div className="fixed bottom-0 inset-x-0 bg-white border-t border-gray-200 shadow-lg z-50">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between gap-4">
            <p className="text-sm text-gray-700">
              <span className="font-semibold">{selectedIds.size}</span> charge{selectedIds.size !== 1 ? "s" : ""} selected
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => { setDisputeMode(false); setSelectedIds(new Set()); }}
                className="text-sm text-gray-600 border border-gray-300 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleSubmitDispute}
                disabled={isDisputing || selectedIds.size === 0}
                className="text-sm bg-red-600 text-white px-5 py-2 rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors font-medium"
              >
                {isDisputing ? "Generating letter..." : `Generate Dispute Letter`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
