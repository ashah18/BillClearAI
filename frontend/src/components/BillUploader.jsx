import { useState, useRef } from "react";

const ACCEPTED_TYPES = ["application/pdf", "image/jpeg", "image/jpg", "image/png"];
const ACCEPTED_EXTENSIONS = [".pdf", ".jpg", ".jpeg", ".png"];

/**
 * Drag-and-drop file upload area with file type validation.
 * Calls onFileSelect(file) when a valid file is chosen.
 */
export default function BillUploader({ onFileSelect, selectedFile }) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  function validateFile(file) {
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError("Please upload a PDF or image file (JPG, PNG).");
      return false;
    }
    if (file.size > 20 * 1024 * 1024) {
      setError("File must be smaller than 20 MB.");
      return false;
    }
    setError("");
    return true;
  }

  function handleFile(file) {
    if (validateFile(file)) {
      onFileSelect(file);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function handleDragOver(e) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave() {
    setIsDragging(false);
  }

  function handleInputChange(e) {
    const file = e.target.files[0];
    if (file) handleFile(file);
  }

  return (
    <div className="w-full">
      <div
        onClick={() => inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`relative border-2 border-dashed rounded-xl p-8 sm:p-10 text-center cursor-pointer transition-colors
          ${isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50"}`}
      >
        {/* capture="environment" opens the rear camera on mobile; ignored on desktop */}
        <input
          ref={inputRef}
          type="file"
          accept="image/*,.pdf"
          capture="environment"
          onChange={handleInputChange}
          className="hidden"
        />

        {selectedFile ? (
          <div>
            <p className="text-green-600 font-semibold text-sm">{selectedFile.name}</p>
            <p className="text-gray-400 text-xs mt-1">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB — Tap to change
            </p>
          </div>
        ) : (
          <div>
            <div className="mx-auto w-12 h-12 mb-3 text-gray-400">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
              </svg>
            </div>
            {/* Mobile: camera-first prompt */}
            <p className="sm:hidden text-sm font-medium text-gray-700">
              Tap to take a photo of your bill
            </p>
            {/* Desktop: drag-and-drop prompt */}
            <p className="hidden sm:block text-sm font-medium text-gray-700">
              Drag and drop your bill here, or <span className="text-blue-600">browse</span>
            </p>
            <p className="text-xs text-gray-400 mt-1">Supports PDF, JPG, PNG — up to 20 MB</p>
          </div>
        )}
      </div>

      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  );
}
