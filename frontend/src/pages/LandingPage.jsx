import { Link } from "react-router-dom";

/**
 * Public marketing landing page shown at the root route (/) for unauthenticated
 * visitors. Logged-in users are redirected to /dashboard by the router.
 */

function FeatureCard({ icon, title, children }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8 text-center">
      <div className="mx-auto w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      <p className="text-sm text-gray-500 mt-2 leading-relaxed">{children}</p>
    </div>
  );
}

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

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white text-gray-900">
      {/* Header */}
      <header className="border-b border-gray-100 sticky top-0 bg-white/90 backdrop-blur z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <span className="text-xl font-bold text-blue-600">BillClear AI</span>
          <div className="flex items-center gap-3 sm:gap-4">
            <Link
              to="/login"
              className="text-sm font-medium text-gray-600 hover:text-blue-600 transition-colors"
            >
              Log In
            </Link>
            <Link
              to="/register"
              className="text-sm font-medium bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Sign Up Free
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center pt-20 pb-16 sm:pt-28 sm:pb-24">
          <span className="inline-block text-xs font-semibold uppercase tracking-wide text-blue-600 bg-blue-50 px-3 py-1 rounded-full mb-6">
            AI-powered medical bill review
          </span>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-gray-900 leading-tight">
            Understand your medical bill.
            <br className="hidden sm:block" />{" "}
            <span className="text-blue-600">Fight back against overcharges.</span>
          </h1>
          <p className="mt-6 text-base sm:text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed">
            Upload any medical bill or EOB and let AI translate the codes, flag errors,
            compare against fair pricing, and draft a dispute letter — in minutes.
          </p>
          <div className="mt-9 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/register"
              className="w-full sm:w-auto bg-blue-600 text-white font-medium px-7 py-3 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Sign Up Free
            </Link>
            <Link
              to="/login"
              className="w-full sm:w-auto border border-gray-300 text-gray-700 font-medium px-7 py-3 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Log In
            </Link>
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="bg-gray-50 border-y border-gray-100 px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto py-16 sm:py-20 text-center">
          <p className="text-4xl sm:text-5xl font-extrabold text-blue-600">80%</p>
          <h2 className="mt-4 text-2xl sm:text-3xl font-bold text-gray-900">
            of medical bills contain errors
          </h2>
          <p className="mt-4 text-base text-gray-500 leading-relaxed">
            Duplicate charges, upcoding, and unbundled services quietly inflate what you owe —
            and most people have no idea what they're actually being billed for. BillClear AI
            reads the fine print so you don't have to.
          </p>
        </div>
      </section>

      {/* Features */}
      <section className="px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto py-16 sm:py-24">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">
              From confusing to clear — in three steps
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <FeatureCard
              title="Understand Your Bill"
              icon={
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              }
            >
              AI translates every billing code (CPT, HCPCS, CDT) into plain English so you know
              exactly what each charge means.
            </FeatureCard>
            <FeatureCard
              title="Find Errors"
              icon={
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              }
            >
              Automatically detects duplicate charges, unbundling, and upcoding, then compares
              prices against regional fair-market rates.
            </FeatureCard>
            <FeatureCard
              title="Fight Back"
              icon={
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              }
            >
              Generate a professional, ready-to-send dispute letter in one click — pre-filled
              with your details and the flagged charges.
            </FeatureCard>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="bg-gray-50 border-y border-gray-100 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto py-16 sm:py-24">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">Simple, honest pricing</h2>
            <p className="mt-3 text-base text-gray-500">
              Start free. Upgrade only when you're ready to dispute.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
            {/* Free */}
            <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-7 flex flex-col">
              <h3 className="text-lg font-semibold text-gray-900">Free</h3>
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
              <Link
                to="/register"
                className="mt-7 w-full text-center border border-gray-300 text-gray-700 font-medium px-5 py-2.5 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Get Started Free
              </Link>
            </div>

            {/* Pro */}
            <div className="bg-white rounded-2xl border-2 border-blue-600 shadow-sm p-7 flex flex-col relative">
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-semibold uppercase tracking-wide text-white bg-blue-600 px-3 py-1 rounded-full">
                Most Popular
              </span>
              <h3 className="text-lg font-semibold text-gray-900">Pro</h3>
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
              <Link
                to="/register"
                className="mt-7 w-full text-center bg-blue-600 text-white font-medium px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Upgrade to Pro
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* AI transparency */}
      <section className="px-4 sm:px-6 lg:px-8">
        <div className="max-w-3xl mx-auto py-16 sm:py-20">
          <div className="bg-white rounded-2xl border border-gray-200 shadow-sm p-6 sm:p-8">
            <div className="flex items-start gap-3">
              <svg className="h-6 w-6 text-blue-600 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h2 className="text-lg font-semibold text-gray-900">How we use AI</h2>
                <p className="mt-2 text-sm text-gray-500 leading-relaxed">
                  BillClear uses Anthropic's Claude AI to analyze your bills. Results are
                  informational only and are <span className="font-medium text-gray-700">not legal,
                  medical, or financial advice</span>. Your documents are processed securely and
                  are <span className="font-medium text-gray-700">never used to train AI models</span>.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto py-10 flex flex-col sm:flex-row items-center justify-between gap-4">
          <span className="text-lg font-bold text-blue-600">BillClear AI</span>
          <p className="text-xs text-gray-400 text-center sm:text-right max-w-md">
            BillClear AI provides informational analysis only and is not a substitute for
            professional legal, medical, or financial advice. © {new Date().getFullYear()} BillClear AI.
          </p>
        </div>
      </footer>
    </div>
  );
}
