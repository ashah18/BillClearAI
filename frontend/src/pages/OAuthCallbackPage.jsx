import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";

/**
 * Landing page after Google OAuth completes.
 *
 * The backend's GoogleJWTView redirects here with ?access_token=XXX after
 * issuing SimpleJWT tokens and setting the refresh cookie. This page:
 *   1. Reads the access token from the URL
 *   2. Clears it from browser history immediately
 *   3. Calls loginWithToken() to store the token and fetch the user profile
 *   4. Navigates to /dashboard
 */
export default function OAuthCallbackPage() {
  const [error, setError] = useState(null);
  const { loginWithToken } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    async function handleCallback() {
      const token = searchParams.get("access_token");
      const oauthError = searchParams.get("error");

      // Remove token from URL immediately — don't leave it in browser history
      window.history.replaceState({}, document.title, "/oauth/callback");

      if (oauthError || !token) {
        setError("Google sign-in failed. Please try again.");
        return;
      }

      try {
        await loginWithToken(token);
        navigate("/dashboard", { replace: true });
      } catch {
        setError("Could not complete sign-in. Please try again.");
      }
    }

    handleCallback();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
        <div className="text-center">
          <p className="text-red-600 text-sm mb-4">{error}</p>
          <a href="/login" className="text-blue-600 hover:underline text-sm font-medium">
            Back to sign in
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <p className="text-gray-400 text-sm">Completing sign-in...</p>
    </div>
  );
}
