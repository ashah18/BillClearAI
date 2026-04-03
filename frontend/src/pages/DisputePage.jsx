import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { saveAs } from "file-saver";
import api from "../api/axios.js";
import { getDispute } from "../api/bills.js";
import Navbar from "../components/Navbar.jsx";
import RiskBadge from "../components/RiskBadge.jsx";
import { formatCurrency, formatDate } from "../utils/formatters.js";

const STATUS_STYLES = {
  draft: "bg-gray-100 text-gray-600",
  sent: "bg-blue-100 text-blue-700",
  acknowledged: "bg-purple-100 text-purple-700",
  resolved: "bg-green-100 text-green-700",
  denied: "bg-red-100 text-red-700",
};

/**
 * Dispute detail page showing the AI-generated dispute letter with
 * options to copy the plain-text preview or download the formatted .docx.
 */
export default function DisputePage() {
  const { id, disputeId } = useParams();

  const [dispute, setDispute] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const data = await getDispute(id, disputeId);
        setDispute(data);
      } catch {
        setError("Failed to load dispute.");
      } finally {
        setIsLoading(false);
      }
    }
    load();
  }, [id, disputeId]);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(dispute.letter_content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // clipboard not available
    }
  }

  async function handleDownload() {
    setIsDownloading(true);
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
      setIsDownloading(false);
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="text-center py-24 text-gray-400">Loading dispute...</div>
      </div>
    );
  }

  if (error || !dispute) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <div className="max-w-2xl mx-auto px-4 py-12">
          <div className="bg-red-50 text-red-700 px-4 py-3 rounded-lg border border-red-200 text-sm">
            {error || "Dispute not found."}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Back link */}
        <Link
          to={`/bills/${id}`}
          className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          Back to bill
        </Link>

        {/* Header */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-bold text-gray-900">Dispute #{dispute.id}</h1>
              <p className="text-sm text-gray-500 mt-0.5">Created {formatDate(dispute.created_at)}</p>
            </div>
            <span className={`capitalize text-xs font-medium px-2.5 py-1 rounded-full ${STATUS_STYLES[dispute.status] || "bg-gray-100 text-gray-600"}`}>
              {dispute.status}
            </span>
          </div>
        </div>

        {/* Disputed charges */}
        <div>
          <h2 className="text-base font-semibold text-gray-900 mb-3">
            Disputed Charges ({dispute.line_items.length})
          </h2>
          <div className="space-y-2">
            {dispute.line_items.map((item) => {
              const code = item.cpt_code || item.hcpcs_code;
              return (
                <div
                  key={item.id}
                  className="bg-white border border-gray-200 rounded-xl px-4 py-3 flex items-center justify-between gap-4"
                >
                  <div className="flex-1 min-w-0">
                    {code && (
                      <span className="inline-block bg-gray-100 text-gray-700 text-xs font-mono px-2 py-0.5 rounded mb-1">
                        {code}
                      </span>
                    )}
                    <p className="text-sm text-gray-900 font-medium leading-snug">
                      {item.description_plain || item.description_raw || "No description"}
                    </p>
                    {item.error_type && (
                      <p className="text-xs text-red-600 mt-0.5 font-medium capitalize">
                        {item.error_type.replace(/_/g, " ")}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-sm font-semibold text-gray-900">
                      {formatCurrency(item.charged_amount)}
                    </span>
                    <RiskBadge risk_level={item.risk_level} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Dispute letter */}
        <div className="rounded-2xl border border-gray-200 shadow-sm overflow-hidden bg-gray-100">
          {/* Toolbar */}
          <div className="px-6 py-4 bg-white border-b border-gray-200 flex items-center justify-between gap-3 flex-wrap">
            <div>
              <h2 className="text-base font-semibold text-gray-900">Dispute Letter</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                Fill in{" "}
                <span className="font-mono bg-yellow-100 text-yellow-800 px-1 rounded">
                  [BRACKETED]
                </span>{" "}
                fields before sending · Download for full formatting
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleCopy}
                className="flex items-center gap-1.5 text-sm text-gray-600 border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {copied ? (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                    Copied
                  </>
                ) : (
                  <>
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                    Copy text
                  </>
                )}
              </button>
              <button
                onClick={handleDownload}
                disabled={isDownloading || !dispute.letter_pdf}
                className="flex items-center gap-1.5 text-sm bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                {isDownloading ? "Preparing…" : "Download .docx"}
              </button>
            </div>
          </div>

          {/* Letter paper — plain text preview */}
          <div className="p-6 sm:p-10">
            <div
              className="bg-white mx-auto shadow-md"
              style={{
                maxWidth: "680px",
                padding: "72px 80px",
                fontFamily: "'Georgia', 'Times New Roman', serif",
                fontSize: "14px",
                lineHeight: "1.7",
                color: "#1a1a1a",
                minHeight: "900px",
              }}
            >
              {dispute.letter_content ? (
                <pre
                  style={{
                    fontFamily: "inherit",
                    fontSize: "inherit",
                    lineHeight: "inherit",
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    margin: 0,
                  }}
                >
                  {dispute.letter_content}
                </pre>
              ) : (
                <p style={{ color: "#9ca3af" }}>Letter content is not available.</p>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
