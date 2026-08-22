import React, {
  createContext,
  useContext,
  useState,
  useCallback,
} from 'react';

const ToastContext = createContext(null);

export function useToast() {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error('useToast must be used inside a ToastProvider');
  }

  return context;
}

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((toast) => {
    const id =
      typeof crypto !== 'undefined' && crypto.randomUUID
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random()}`;

    setToasts((prev) => [
      ...prev,
      {
        id,
        type: 'info',
        message: '',
        ...toast,
      },
    ]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);

    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const success = useCallback(
    (message) => {
      return addToast({
        type: 'success',
        message,
      });
    },
    [addToast]
  );

  const error = useCallback(
    (message) => {
      return addToast({
        type: 'error',
        message,
      });
    },
    [addToast]
  );

  const info = useCallback(
    (message) => {
      return addToast({
        type: 'info',
        message,
      });
    },
    [addToast]
  );

  return (
    <ToastContext.Provider
      value={{
        addToast,
        removeToast,
        success,
        error,
        info,
      }}
    >
      {children}

      <div className="fixed bottom-4 right-4 space-y-2 z-50">
        {toasts.map(({ id, type, message }) => (
          <div
            key={id}
            className={`max-w-xs w-full px-4 py-3 rounded-lg shadow-lg text-white ${
              type === 'success'
                ? 'bg-green-500'
                : type === 'error'
                ? 'bg-red-500'
                : 'bg-blue-500'
            }`}
          >
            {message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
