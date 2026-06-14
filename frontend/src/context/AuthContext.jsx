import React, { createContext, useReducer, useEffect } from "react";
import { login as apiLogin, logout as apiLogout, register as apiRegister, refreshToken, getProfile } from "../api/auth.js";
import { setAccessToken } from "../api/axios.js";

export const AuthContext = createContext(null);

const initialState = {
  user: null,
  isAuthenticated: false,
  isLoading: true, // true while checking existing session on mount
};

function authReducer(state, action) {
  switch (action.type) {
    case "LOGIN":
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        isLoading: false,
      };
    case "LOGOUT":
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        isLoading: false,
      };
    case "SET_USER":
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        isLoading: false,
      };
    case "SET_LOADING":
      return {
        ...state,
        isLoading: action.payload,
      };
    default:
      return state;
  }
}

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Listen for session-expiry events dispatched by the axios interceptor when
  // both the access token and refresh token are expired/invalid.
  useEffect(() => {
    function handleSessionExpired() {
      setAccessToken(null);
      dispatch({ type: "LOGOUT" });
    }
    window.addEventListener("auth:session-expired", handleSessionExpired);
    return () => window.removeEventListener("auth:session-expired", handleSessionExpired);
  }, []);

  // On mount, attempt to restore session via refresh token cookie before
  // rendering any protected routes (see isLoading gate in App.jsx).
  useEffect(() => {
    async function restoreSession() {
      try {
        const data = await refreshToken();
        setAccessToken(data.access);
        const userData = await getProfile();
        dispatch({ type: "SET_USER", payload: { user: userData } });
      } catch {
        // No valid session — treat as logged out
        setAccessToken(null);
        dispatch({ type: "SET_LOADING", payload: false });
      }
    }
    restoreSession();
  }, []);

  async function login(email, password) {
    const data = await apiLogin(email, password);
    setAccessToken(data.access);
    dispatch({ type: "LOGIN", payload: { user: data.user } });
    return data;
  }

  async function logout() {
    try {
      await apiLogout();
    } catch {
      // Ignore errors — clear local state regardless
    }
    setAccessToken(null);
    dispatch({ type: "LOGOUT" });
  }

  async function register(email, password, password2) {
    const data = await apiRegister(email, password, password2);
    return data;
  }

  async function loginWithToken(token) {
    setAccessToken(token);
    try {
      const userData = await getProfile();
      dispatch({ type: "LOGIN", payload: { user: userData } });
    } catch {
      setAccessToken(null);
      throw new Error("OAuth login failed — could not fetch profile.");
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        isLoading: state.isLoading,
        login,
        logout,
        register,
        loginWithToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
