import React from 'react';
import { cn } from '../../lib/utils';

interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'secondary';
  size?: 'sm' | 'md' | 'lg';
  outline?: boolean;
  dot?: boolean;
}

const Badge = React.forwardRef<HTMLDivElement, BadgeProps>(
  ({ className, variant = 'default', size = 'md', outline = false, dot = false, children, ...props }, ref) => {
    const baseStyles = 'inline-flex items-center rounded-full font-medium transition-all duration-200';
    
    const variants = {
      default: outline 
        ? 'border border-gray-300 text-gray-700 bg-white hover:bg-gray-50' 
        : 'bg-gray-100 text-gray-800 hover:bg-gray-200',
      success: outline 
        ? 'border border-green-300 text-green-700 bg-white hover:bg-green-50' 
        : 'bg-green-100 text-green-800 hover:bg-green-200',
      warning: outline 
        ? 'border border-amber-300 text-amber-700 bg-white hover:bg-amber-50' 
        : 'bg-amber-100 text-amber-800 hover:bg-amber-200',
      danger: outline 
        ? 'border border-red-300 text-red-700 bg-white hover:bg-red-50' 
        : 'bg-red-100 text-red-800 hover:bg-red-200',
      info: outline 
        ? 'border border-blue-300 text-blue-700 bg-white hover:bg-blue-50' 
        : 'bg-blue-100 text-blue-800 hover:bg-blue-200',
      secondary: outline 
        ? 'border border-purple-300 text-purple-700 bg-white hover:bg-purple-50' 
        : 'bg-purple-100 text-purple-800 hover:bg-purple-200',
    };
    
    const sizes = {
      sm: 'px-2 py-1 text-xs',
      md: 'px-3 py-1 text-sm',
      lg: 'px-4 py-1.5 text-base',
    };

    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      >
        {dot && (
          <span className="mr-2 h-2 w-2 rounded-full bg-current animate-pulse" />
        )}
        {children}
      </div>
    );
  }
);

// Status Badge Component with predefined statuses
interface StatusBadgeProps extends Omit<BadgeProps, 'variant'> {
  status: 'online' | 'offline' | 'pending' | 'processing' | 'completed' | 'failed' | 'idle';
}

const StatusBadge: React.FC<StatusBadgeProps> = ({ status, ...props }) => {
  const statusConfig = {
    online: { variant: 'success' as const, label: 'Online' },
    offline: { variant: 'secondary' as const, label: 'Offline' },
    pending: { variant: 'warning' as const, label: 'Pending' },
    processing: { variant: 'info' as const, label: 'Processing' },
    completed: { variant: 'success' as const, label: 'Completed' },
    failed: { variant: 'danger' as const, label: 'Failed' },
    idle: { variant: 'secondary' as const, label: 'Idle' }
  };

  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} dot {...props}>
      {config.label}
    </Badge>
  );
};

// Count Badge Component for notifications
interface CountBadgeProps extends Omit<BadgeProps, 'children'> {
  count: number;
  max?: number;
  showZero?: boolean;
}

const CountBadge: React.FC<CountBadgeProps> = ({ 
  count, 
  max = 99, 
  showZero = false, 
  ...props 
}) => {
  if (count === 0 && !showZero) {
    return null;
  }

  const displayCount = count > max ? `${max}+` : count.toString();

  return (
    <Badge size="sm" {...props}>
      {displayCount}
    </Badge>
  );
};

export { Badge, StatusBadge, CountBadge };
export default Badge;