import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import api from "../api/axios.js";
import { resendVerification } from "../api/auth.js";
import { useAuth } from "../hooks/useAuth.js";

export default function VerifyEmailPage() {
  const { token } = useParams();
  const { isAuthenticated } = useAuth();

  const [status, setStatus] = useState("loading"); // "loading" | "success" | "error"
  const [resendSent, setResendSent] = useState(false);
  const [isResending, setIsResending] = useState(false);

  useEffect(() => {
    async function verify() {
      try {
        await api.get(`/auth/verify-email/${token}/`);
        setStatus("success");
      } catch {
        setStatus("error");
      }
    }
    verify();
  }, [token]);

  async function handleResend() {
    setIsResending(true);
    try {
      await resendVerification();
      setResendSent(true);
    } catch {
      // silently fail — user sees the button again
    } finally {
      setIsResending(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center">
        <h1 className="text-2xl font-bold text-blue-600 mb-6">BillClear AI</h1>

        {status === "loading" && (
          <p className="text-gray-500 text-sm">Verifying your email address...</p>
        )}

        {status === "success" && (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-4 rounded-lg text-sm">
              Your email address has been verified. You can now use all features of BillClear AI.
            </div>
            <Link
              to="/dashboard"
              className="inline-block bg-blue-600 text-white px-5 py-2.5 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Go to dashboard
            </Link>
          </div>
        )}

        {status === "error" && (
          <div className="space-y-4">
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-4 rounded-lg text-sm">
              This verification link is invalid or has expired.
            </div>
            {isAuthenticated ? (
              resendSent ? (
                <p className="text-sm text-green-600 font-medium">A new verification email has been sent.</p>
              ) : (
                <button
                  onClick={handleResend}
                  disabled={isResending}
                  className="text-sm text-blue-600 hover:underline disabled:opacity-50"
                >
                  {isResending ? "Sending..." : "Resend verification email"}
                </button>
              )
            ) : (
              <p className="text-sm text-gray-500">
                <Link to="/login" className="text-blue-600 hover:underline font-medium">
                  Sign in
                </Link>{" "}
                to request a new verification link.
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
