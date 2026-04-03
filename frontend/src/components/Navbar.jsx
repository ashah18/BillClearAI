import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";

/**
 * Top navigation bar with logo, nav links, and logout button.
 */
export default function Navbar() {
  const { isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();

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

          {/* Nav links */}
          {isAuthenticated && (
            <div className="flex items-center gap-6">
              <Link
                to="/dashboard"
                className="text-sm text-gray-600 hover:text-blue-600 font-medium transition-colors"
              >
                Dashboard
              </Link>
              <Link
                to="/upload"
                className="text-sm text-gray-600 hover:text-blue-600 font-medium transition-colors"
              >
                Upload Bill
              </Link>
              <Link
                to="/profile"
                className="text-sm text-gray-600 hover:text-blue-600 font-medium transition-colors"
              >
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

          {/* Unauthenticated links */}
          {!isAuthenticated && (
            <div className="flex items-center gap-4">
              <Link
                to="/login"
                className="text-sm text-gray-600 hover:text-blue-600 font-medium"
              >
                Login
              </Link>
              <Link
                to="/register"
                className="text-sm bg-blue-600 text-white px-3 py-1.5 rounded-md hover:bg-blue-700 transition-colors font-medium"
              >
                Sign Up
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
}
