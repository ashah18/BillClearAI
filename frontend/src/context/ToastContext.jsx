import { createContext, useContext, useState, useCallback } from "react";

export const ToastContext = createContext(null);

const TYPE_STYLES = {
  success: "bg-green-600",
  error: "bg-red-600",
  info: "bg-blue-600",
};

function ToastContainer({ toasts }) {
  if (toasts.length === 0) return null;
  return (
    <div className="fixed top-4 right-4 z-[200] flex flex-col gap-2 pointer-events-none">
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`${TYPE_STYLES[t.type] || TYPE_STYLES.success} text-white text-sm font-medium px-4 py-3 rounded-lg shadow-lg max-w-sm pointer-events-auto`}
        >
          {t.message}
        </div>
      ))}
    </div>
  );
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = "success") => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  return (
    <ToastContext.Provider value={{ addToast }}>
      {children}
      <ToastContainer toasts={toasts} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
