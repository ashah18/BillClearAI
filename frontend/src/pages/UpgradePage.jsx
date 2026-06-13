import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { useToast } from "../context/ToastContext.jsx";
import { createCheckoutSession, getSubscriptionStatus } from "../api/billing.js";

/**
 * Public upgrade / pricing page at /upgrade.
 *
 * Accessible whether the visitor is logged in or not. For a logged-in user we
 * show which account the upgrade applies to and, on click, create a Stripe
 * Checkout session and redirect to it.
 */

function CheckItem({ children, included = true }) {
  return (
    <li className="flex items-start gap-2.5 text-sm">
      {included ? (
        <svg className="h-5 w-5 text-green-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="h-5 w-5 text-gray-300 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      )}
      <span className={included ? "text-gray-700" : "text-gray-400"}>{children}</span>
    </li>
  );
}

export default function UpgradePage() {
  const { isAuthenticated, user } = useAuth();
  const { addToast } = useToast();
  const [searchParams, setSearchParams] = useSearchParams();
  const [subscription, setSubscription] = useState(null);
  const [upgrading, setUpgrading] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) return;

    getSubscriptionStatus()
      .then(setSubscription)
      .catch(() => {
        // Subscription status is non-critical for this page; ignore failures.
      });
  }, [isAuthenticated]);

  useEffect(() => {
    const checkout = searchParams.get("checkout");
    if (!checkout) return;

    if (checkout === "success") {
      addToast("Welcome to Pro! Your subscription is now active.", "success");
    } else if (checkout === "canceled") {
      addToast("Checkout canceled — you're still on the Free plan.", "info");
    }

    setSearchParams({}, { replace: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams]);

  async function handleUpgrade() {
    setUpgrading(true);
    try {
      const { url } = await createCheckoutSession();
      window.location.href = url;
    } catch (err) {
      addToast(err.response?.data?.detail || "Could not start checkout. Please try again.", "error");
      setUpgrading(false);
    }
  }

  const isPro = Boolean(subscription?.is_pro);

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
        <div className="text-center max-w-2xl mx-auto mb-10 sm:mb-12">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900">Upgrade to Pro</h1>
          <p className="mt-3 text-base text-gray-500">
            Unlock unlimited bill analyses and the dispute letters that get your money back.
          </p>
          {isAuthenticated && user?.email && (
            <p className="mt-4 inline-block text-sm text-gray-600 bg-white border border-gray-200 rounded-full px-4 py-1.5">
              Upgrading account: <span className="font-medium text-gray-900">{user.email}</span>
            </p>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
          {/* Free */}
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-7 flex flex-col">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Free</h3>
              {isAuthenticated && !isPro && (
                <span className="text-xs font-semibold text-gray-500 bg-gray-100 px-2.5 py-1 rounded-full">
                  Current plan
                </span>
              )}
            </div>
            <div className="mt-3 flex items-baseline gap-1">
              <span className="text-4xl font-extrabold text-gray-900">$0</span>
              <span className="text-sm text-gray-500">/month</span>
            </div>
            <p className="mt-2 text-sm text-gray-500">Everything you need to spot overcharges.</p>
            <ul className="mt-6 space-y-3 flex-1">
              <CheckItem>3 bill analyses per month</CheckItem>
              <CheckItem>AI plain-English translations</CheckItem>
              <CheckItem>Error &amp; overcharge detection</CheckItem>
              <CheckItem>Fair-price comparison</CheckItem>
              <CheckItem included={false}>Dispute letter generation</CheckItem>
            </ul>
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="mt-7 w-full text-center border border-gray-300 text-gray-700 font-medium px-5 py-2.5 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Back to Dashboard
              </Link>
            ) : (
              <Link
                to="/register"
                className="mt-7 w-full text-center border border-gray-300 text-gray-700 font-medium px-5 py-2.5 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Get Started Free
              </Link>
            )}
          </div>

          {/* Pro */}
          <div className="bg-white rounded-2xl border-2 border-blue-600 shadow-sm p-7 flex flex-col relative">
            <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-semibold uppercase tracking-wide text-white bg-blue-600 px-3 py-1 rounded-full">
              Most Popular
            </span>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Pro</h3>
              {isPro && (
                <span className="text-xs font-semibold text-blue-700 bg-blue-100 px-2.5 py-1 rounded-full">
                  Current plan
                </span>
              )}
            </div>
            <div className="mt-3 flex items-baseline gap-1">
              <span className="text-4xl font-extrabold text-gray-900">$9.99</span>
              <span className="text-sm text-gray-500">/month</span>
            </div>
            <p className="mt-2 text-sm text-gray-500">Unlock the full power to fight back.</p>
            <ul className="mt-6 space-y-3 flex-1">
              <CheckItem>Unlimited bill analyses</CheckItem>
              <CheckItem>Unlimited AI chat about your bills</CheckItem>
              <CheckItem>Dispute letter generation &amp; downloads</CheckItem>
              <CheckItem>Full dispute tracking</CheckItem>
            </ul>
            {isPro ? (
              <Link
                to="/profile"
                className="mt-7 w-full text-center bg-blue-600 text-white font-medium px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Manage in Profile
              </Link>
            ) : isAuthenticated ? (
              <button
                onClick={handleUpgrade}
                disabled={upgrading}
                className="mt-7 w-full text-center bg-blue-600 text-white font-medium px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {upgrading ? "Redirecting…" : "Upgrade to Pro"}
              </button>
            ) : (
              <Link
                to="/register"
                className="mt-7 w-full text-center bg-blue-600 text-white font-medium px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Sign Up to Upgrade
              </Link>
            )}
          </div>
        </div>

        <p className="text-center text-xs text-gray-400 mt-8">
          Cancel anytime. Secure payments processed by Stripe.
        </p>
      </main>
    </div>
  );
}
