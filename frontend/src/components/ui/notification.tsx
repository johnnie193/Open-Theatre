import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import { cn } from '../../lib/utils';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

interface NotificationProps {
  id: string;
  type: NotificationType;
  title: string;
  message?: string;
  duration?: number;
  onClose: (id: string) => void;
  className?: string;
}

export const Notification: React.FC<NotificationProps> = ({
  id,
  type,
  title,
  message,
  duration = 5000,
  onClose,
  className
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(() => onClose(id), 300);
      }, duration);

      return () => clearTimeout(timer);
    }
  }, [duration, id, onClose]);

  const handleClose = () => {
    setIsVisible(false);
    setTimeout(() => onClose(id), 300);
  };

  const icons = {
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertTriangle,
    info: Info
  };

  const colors = {
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    info: 'bg-blue-50 border-blue-200 text-blue-800'
  };

  const iconColors = {
    success: 'text-green-500',
    error: 'text-red-500',
    warning: 'text-yellow-500',
    info: 'text-blue-500'
  };

  const Icon = icons[type];

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -50, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -50, scale: 0.95 }}
          transition={{ duration: 0.3, ease: "easeOut" }}
          className={cn(
            "relative max-w-sm w-full bg-white rounded-lg shadow-lg border p-4",
            colors[type],
            className
          )}
        >
          <div className="flex items-start">
            <Icon className={cn("h-5 w-5 mt-0.5 mr-3 flex-shrink-0", iconColors[type])} />
            <div className="flex-1">
              <h4 className="text-sm font-medium">{title}</h4>
              {message && (
                <p className="mt-1 text-sm opacity-90">{message}</p>
              )}
            </div>
            <button
              onClick={handleClose}
              className="ml-2 flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

interface NotificationContainerProps {
  notifications: Array<{
    id: string;
    type: NotificationType;
    title: string;
    message?: string;
    duration?: number;
  }>;
  onClose: (id: string) => void;
  className?: string;
}

export const NotificationContainer: React.FC<NotificationContainerProps> = ({
  notifications,
  onClose,
  className
}) => {
  return (
    <div className={cn("fixed top-4 right-4 z-50 space-y-2", className)}>
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          {...notification}
          onClose={onClose}
        />
      ))}
    </div>
  );
};
