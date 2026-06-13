import { useState } from "react";

/**
 * First-time AI disclosure consent modal shown before a user can upload a bill.
 */
export default function AIDisclosureModal({ onAcknowledge }) {
  const [dontShowAgain, setDontShowAgain] = useState(false);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-3">Before you upload</h2>
        <p className="text-sm text-gray-600 mb-6">
          Your bill will be analyzed by AI. BillClear uses Anthropic&apos;s Claude to read and
          interpret your medical documents. Results are estimates to help you understand your
          bill and are not legal, medical, or financial advice. Your documents are processed
          securely and are never used to train AI models.
        </p>
        <label className="flex items-center gap-2 mb-6 text-sm text-gray-700 cursor-pointer">
          <input
            type="checkbox"
            checked={dontShowAgain}
            onChange={(e) => setDontShowAgain(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          Don&apos;t show this again
        </label>
        <button
          type="button"
          onClick={() => onAcknowledge(dontShowAgain)}
          className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 transition-colors"
        >
          I Understand
        </button>
      </div>
    </div>
  );
}
