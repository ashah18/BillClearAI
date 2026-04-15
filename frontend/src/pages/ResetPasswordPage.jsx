import { useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { confirmPasswordReset } from "../api/auth.js";

export default function ResetPasswordPage() {
  const { uid, token } = useParams();
  const navigate = useNavigate();

  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (password !== password2) {
      setError("Passwords do not match.");
      return;
    }

    setIsLoading(true);
    try {
      await confirmPasswordReset(uid, token, password);
      navigate("/login", {
        state: { message: "Password reset successfully. You can now sign in with your new password." },
      });
    } catch (err) {
      const msg =
        err.response?.data?.detail ||
        "This link is invalid or has expired. Please request a new reset link.";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-blue-600">BillClear AI</h1>
          <p className="text-gray-500 text-sm mt-1">Set a new password</p>
        </div>

        {error && (
          <div className="mb-4 bg-red-50 text-red-700 text-sm px-4 py-3 rounded-lg border border-red-200">
            {error}
            {error.includes("invalid or has expired") && (
              <span>
                {" "}
                <Link to="/forgot-password" className="underline font-medium">
                  Request a new link
                </Link>
              </span>
            )}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="password">
              New password
            </label>
            <input
              id="password"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="At least 8 characters"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1" htmlFor="password2">
              Confirm new password
            </label>
            <input
              id="password2"
              type="password"
              required
              value={password2}
              onChange={(e) => setPassword2(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Repeat your new password"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? "Saving..." : "Set new password"}
          </button>
        </form>
      </div>
    </div>
  );
}
