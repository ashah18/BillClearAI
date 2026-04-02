import React, { createContext, useReducer, useEffect } from "react";
import { login as apiLogin, logout as apiLogout, register as apiRegister, refreshToken } from "../api/auth.js";
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

  // On mount, attempt to restore session via refresh token cookie
  useEffect(() => {
    async function restoreSession() {
      try {
        const data = await refreshToken();
        setAccessToken(data.access);
        // Fetch user profile if returned, or set minimal user object
        dispatch({ type: "SET_USER", payload: { user: data.user || { email: "" } } });
      } catch {
        // No valid session — clear loading state
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

  return (
    <AuthContext.Provider
      value={{
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        isLoading: state.isLoading,
        login,
        logout,
        register,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
