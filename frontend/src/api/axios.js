import axios from "axios";

// In-memory access token storage (never persisted to localStorage)
let accessToken = null;

export function setAccessToken(token) {
  accessToken = token;
}

export function getAccessToken() {
  return accessToken;
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api",
  withCredentials: true, // Send httpOnly cookies (refresh token)
});

// Attach access token to every request
api.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// On 401, attempt a token refresh then retry the original request
let isRefreshing = false;
let failedQueue = [];

function processQueue(error, token = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Avoid infinite loop on refresh endpoint itself
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      !originalRequest.url.includes("/auth/refresh/")
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const response = await api.post("/auth/refresh/");
        const newToken = response.data.access;
        setAccessToken(newToken);
        processQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        setAccessToken(null);
        // Signal the app that the session has fully expired so it can redirect to login
        window.dispatchEvent(new CustomEvent("auth:session-expired"));
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    // Handle rate limiting — show a toast notification via custom event
    if (error.response?.status === 429) {
      const message =
        error.response?.data?.detail || "Too many requests. Please try again later.";
      window.dispatchEvent(new CustomEvent("rate-limit", { detail: { message } }));
    }

    return Promise.reject(error);
  }
);

export default api;
