import React from 'react';
import { 
  X, 
  CheckCircle, 
  AlertCircle, 
  Info, 
  AlertTriangle 
} from 'lucide-react';
import { useAppStore, Notification } from '../../stores/useAppStore';
import { cn, formatRelativeTime } from '../../lib/utils';

const NotificationCenter: React.FC = () => {
  const { notifications, removeNotification } = useAppStore();

  if (notifications.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-4 right-4 z-50 w-80 max-w-sm space-y-2">
      {notifications.map((notification) => (
        <NotificationItem
          key={notification.id}
          notification={notification}
          onDismiss={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  );
};

interface NotificationItemProps {
  notification: Notification;
  onDismiss: () => void;
}

const NotificationItem: React.FC<NotificationItemProps> = ({ 
  notification, 
  onDismiss 
}) => {
  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'info':
      default:
        return <Info className="h-5 w-5 text-blue-500" />;
    }
  };

  const getBorderColor = () => {
    switch (notification.type) {
      case 'success':
        return 'border-l-green-500';
      case 'error':
        return 'border-l-red-500';
      case 'warning':
        return 'border-l-yellow-500';
      case 'info':
      default:
        return 'border-l-blue-500';
    }
  };

  return (
    <div
      className={cn(
        "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg p-4 border-l-4 transition-all duration-300 ease-in-out",
        getBorderColor()
      )}
      role="alert"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0">
          {getIcon()}
        </div>
        
        <div className="ml-3 flex-1">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="text-sm font-medium text-gray-900 dark:text-white">
                {notification.title}
              </h4>
              
              {notification.message && (
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                  {notification.message}
                </p>
              )}
              
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-500">
                {formatRelativeTime(notification.timestamp)}
              </p>
            </div>
            
            <button
              type="button"
              onClick={onDismiss}
              className="ml-4 inline-flex text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
            >
              <span className="sr-only">Dismiss notification</span>
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationCenter;