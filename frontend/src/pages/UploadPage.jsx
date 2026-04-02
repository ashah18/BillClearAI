import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadBill } from "../api/bills.js";
import BillUploader from "../components/BillUploader.jsx";
import Navbar from "../components/Navbar.jsx";

/**
 * File upload page. Allows the user to select/drag a bill file,
 * then submits it to the backend for AI parsing and analysis.
 */
export default function UploadPage() {
  const navigate = useNavigate();
  const [selectedFile, setSelectedFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    if (!selectedFile) {
      setError("Please select a file to upload.");
      return;
    }

    setError("");
    setIsLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const bill = await uploadBill(formData);
      navigate(`/bills/${bill.id}`);
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        "Upload failed. Please try again.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Upload a Medical Bill</h1>
            <p className="text-gray-500 text-sm mt-1">
              Upload your bill or EOB and our AI will analyze it for errors and overcharges.
            </p>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-200">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <BillUploader onFileSelect={setSelectedFile} selectedFile={selectedFile} />

            <button
              type="submit"
              disabled={isLoading || !selectedFile}
              className="w-full bg-blue-600 text-white py-3 rounded-xl font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                  </svg>
                  Analyzing your bill...
                </span>
              ) : (
                "Upload and Analyze"
              )}
            </button>
          </form>

          {isLoading && (
            <p className="text-center text-xs text-gray-400 mt-3">
              This may take 30–60 seconds while AI processes your document.
            </p>
          )}
        </div>
      </main>
    </div>
  );
}
