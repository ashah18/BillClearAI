import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";

/**
 * Top navigation bar with logo, nav links, and logout button.
 * On mobile, nav links collapse into a hamburger menu.
 */
export default function Navbar() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-blue-600">BillClear AI</span>
          </Link>

          {/* Desktop nav links — hidden on mobile */}
          {isAuthenticated && (
            <div className="hidden sm:flex items-center gap-6">
              <Link to="/dashboard" className="text-sm text-gray-600 hover:text-blue-600 font-medium transition-colors">
                Dashboard
              </Link>
              <Link to="/upload" className="text-sm text-gray-600 hover:text-blue-600 font-medium transition-colors">
                Upload Bill
              </Link>
              <Link to="/profile" className="text-sm text-gray-600 hover:text-blue-600 font-medium transition-colors">
                Profile
              </Link>
              <button
                onClick={handleLogout}
                className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 transition-colors font-medium"
              >
                Logout
              </button>
            </div>
          )}

          {/* Unauthenticated links — always visible */}
          {!isAuthenticated && (
            <div className="flex items-center gap-4">
              <Link to="/login" className="text-sm text-gray-600 hover:text-blue-600 font-medium">
                Login
              </Link>
              <Link to="/register" className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 transition-colors font-medium">
                Sign Up
              </Link>
            </div>
          )}

          {/* Hamburger button — mobile only, authenticated only */}
          {isAuthenticated && (
            <button
              onClick={() => setMenuOpen((o) => !o)}
              className="sm:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors"
              aria-label={menuOpen ? "Close menu" : "Open menu"}
            >
              {menuOpen ? (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Mobile dropdown menu */}
      {menuOpen && isAuthenticated && (
        <div className="sm:hidden border-t border-gray-100 bg-white px-4 py-3 space-y-1">
          <Link
            to="/dashboard"
            onClick={() => setMenuOpen(false)}
            className="block px-3 py-2.5 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Dashboard
          </Link>
          <Link
            to="/upload"
            onClick={() => setMenuOpen(false)}
            className="block px-3 py-2.5 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Upload Bill
          </Link>
          <Link
            to="/profile"
            onClick={() => setMenuOpen(false)}
            className="block px-3 py-2.5 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Profile
          </Link>
          <button
            onClick={() => { handleLogout(); setMenuOpen(false); }}
            className="w-full text-left px-3 py-2.5 text-sm font-medium text-red-600 rounded-lg hover:bg-red-50 transition-colors"
          >
            Logout
          </button>
        </div>
      )}
    </nav>
  );
}
