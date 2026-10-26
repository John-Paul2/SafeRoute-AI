/**
 * SafeRoute AI — Toast Notification System
 * Course Outcome Mapping:
 * - System feedback & telemetry alerts
 */

import React, { useEffect } from 'react';
import { AlertCircle, CheckCircle, Info, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  );
};

const ToastItem: React.FC<{ toast: ToastMessage; onDismiss: (id: string) => void }> = ({
  toast,
  onDismiss,
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss(toast.id);
    }, 4000);
    return () => clearTimeout(timer);
  }, [toast.id, onDismiss]);

  const getIcon = () => {
    switch (toast.type) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-hot shrink-0" />;
      case 'success':
        return <CheckCircle className="w-4 h-4 text-brand shrink-0" />;
      case 'info':
      default:
        return <Info className="w-4 h-4 text-cold shrink-0" />;
    }
  };

  const getBorderColor = () => {
    switch (toast.type) {
      case 'error':
        return 'border-hot/30 bg-[#fff5f6]';
      case 'success':
        return 'border-brand/30 bg-[#f2fcf4]';
      case 'info':
      default:
        return 'border-hairline bg-surface';
    }
  };

  return (
    <div
      className={`pointer-events-auto rounded-md border p-3 shadow-md flex items-start gap-2.5 text-xs text-ink font-sans transition-all animate-slideIn ${getBorderColor()}`}
    >
      {getIcon()}
      <div className="flex-1 text-[12px] font-medium leading-snug">
        {toast.message}
      </div>
      <button
        onClick={() => onDismiss(toast.id)}
        className="text-body hover:text-ink transition-colors p-0.5 rounded-sm"
      >
        <X className="w-3.5 h-3.5" />
      </button>
    </div>
  );
};
