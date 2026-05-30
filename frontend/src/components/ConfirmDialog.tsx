import { useEffect, useRef } from 'react';

interface ConfirmDialogProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
  destructive?: boolean;
}

export default function ConfirmDialog({
  open,
  title,
  message,
  confirmLabel = 'Confirm',
  cancelLabel = 'Cancel',
  onConfirm,
  onCancel,
  destructive = true,
}: ConfirmDialogProps) {
  const confirmRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (open) {
      const handler = (e: KeyboardEvent) => {
        if (e.key === 'Escape') onCancel();
      };
      document.addEventListener('keydown', handler);
      // Focus the confirm button when opened
      setTimeout(() => confirmRef.current?.focus(), 50);
      return () => document.removeEventListener('keydown', handler);
    }
  }, [open, onCancel]);

  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[9998] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onCancel}
        aria-hidden="true"
      />

      {/* Dialog */}
      <div
        className="relative bg-surface-100 border border-border rounded-xl shadow-2xl shadow-black/40
                   w-full max-w-md mx-4 p-6 animate-fade-in"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-title"
        aria-describedby="confirm-message"
      >
        <h2
          id="confirm-title"
          className="text-base font-semibold text-text-primary mb-2"
        >
          {title}
        </h2>
        <p
          id="confirm-message"
          className="text-sm text-text-secondary leading-relaxed mb-6"
        >
          {message}
        </p>
        <div className="flex items-center justify-end gap-3">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-sm font-medium text-text-secondary
                       bg-surface-200 border border-border hover:border-border-light
                       hover:text-text-primary transition-colors"
          >
            {cancelLabel}
          </button>
          <button
            ref={confirmRef}
            onClick={onConfirm}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors
              ${
                destructive
                  ? 'bg-accent-red/10 text-accent-red border border-accent-red/20 hover:bg-accent-red/20'
                  : 'bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 hover:bg-accent-cyan/20'
              }`}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
