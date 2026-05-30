import { createContext, useContext, useState, useCallback, useEffect, type ReactNode } from 'react';

type ToastType = 'success' | 'error' | 'info';

interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  toast: (type: ToastType, message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

let nextId = 0;

const bgMap: Record<ToastType, string> = {
  success: 'border-accent-green bg-accent-green/10',
  error: 'border-accent-red bg-accent-red/10',
  info: 'border-accent-cyan bg-accent-cyan/10',
};

const iconMap: Record<ToastType, string> = {
  success: 'checkmark',
  error: 'cross',
  info: 'info',
};

function ToastIcon({ type }: { type: ToastType }) {
  if (type === 'success') {
    return (
      <svg className="w-4 h-4 text-accent-green shrink-0" viewBox="0 0 16 16" fill="currentColor">
        <path d="M8 0a8 8 0 110 16A8 8 0 018 0zm3.646 5.146a.5.5 0 00-.708 0L7.5 8.586 5.354 6.44a.5.5 0 10-.708.708l2.5 2.5a.5.5 0 00.708 0l4-4a.5.5 0 000-.708z" />
      </svg>
    );
  }
  if (type === 'error') {
    return (
      <svg className="w-4 h-4 text-accent-red shrink-0" viewBox="0 0 16 16" fill="currentColor">
        <path d="M8 0a8 8 0 110 16A8 8 0 018 0zm3.646 4.646a.5.5 0 00-.708 0L8 7.586l-2.938-2.94a.5.5 0 10-.708.708L7.292 8.29l-2.938 2.938a.5.5 0 00.708.708L8 8.998l2.938 2.938a.5.5 0 00.708-.708L8.708 8.29l2.938-2.938a.5.5 0 000-.708z" />
      </svg>
    );
  }
  return (
    <svg className="w-4 h-4 text-accent-cyan shrink-0" viewBox="0 0 16 16" fill="currentColor">
      <path d="M8 0a8 8 0 110 16A8 8 0 018 0zm0 2a1 1 0 00-1 1v5a1 1 0 002 0V3a1 1 0 00-1-1zm0 8a1 1 0 100 2 1 1 0 000-2z" />
    </svg>
  );
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, message: string) => {
    const id = nextId++;
    setToasts((prev) => [...prev, { id, type, message }]);
  }, []);

  const removeToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast: addToast }}>
      {children}
      <div className="fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDone={removeToast} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

function ToastItem({ toast, onDone }: { toast: Toast; onDone: (id: number) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onDone(toast.id), 3000);
    return () => clearTimeout(timer);
  }, [toast.id, onDone]);

  return (
    <div
      className={`pointer-events-auto flex items-start gap-2.5 px-4 py-3 rounded-lg border ${bgMap[toast.type]}
                  backdrop-blur-md shadow-lg shadow-black/30 min-w-[280px] max-w-[420px]
                  animate-slide-up`}
      role="alert"
    >
      <ToastIcon type={toast.type} />
      <p className="text-sm text-text-primary leading-snug flex-1">{toast.message}</p>
      <button
        onClick={() => onDone(toast.id)}
        className="shrink-0 p-0.5 rounded text-text-muted hover:text-text-primary transition-colors"
        aria-label="Dismiss"
      >
        <svg className="w-3.5 h-3.5" viewBox="0 0 16 16" fill="currentColor">
          <path d="M4.646 4.646a.5.5 0 01.708 0L8 7.293l2.646-2.647a.5.5 0 01.708.708L8.707 8l2.647 2.646a.5.5 0 01-.708.708L8 8.707l-2.646 2.647a.5.5 0 01-.708-.708L7.293 8 4.646 5.354a.5.5 0 010-.708z" />
        </svg>
      </button>
    </div>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return ctx;
}
