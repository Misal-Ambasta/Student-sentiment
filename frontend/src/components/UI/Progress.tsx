import React from 'react';
import { cn } from '../../lib/utils';

interface ProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'success' | 'warning' | 'danger';
  showLabel?: boolean;
  label?: string;
}

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ className, value, max = 100, size = 'md', variant = 'default', showLabel = false, label, ...props }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
    
    const baseStyles = 'w-full bg-gray-200 rounded-full overflow-hidden';
    
    const sizes = {
      sm: 'h-2',
      md: 'h-3',
      lg: 'h-4',
    };
    
    const variants = {
      default: 'bg-gradient-to-r from-blue-500 to-blue-600',
      success: 'bg-gradient-to-r from-green-500 to-green-600',
      warning: 'bg-gradient-to-r from-amber-500 to-amber-600',
      danger: 'bg-gradient-to-r from-red-500 to-red-600',
    };

    return (
      <div ref={ref} className={cn('space-y-3', className)} {...props}>
        {(showLabel || label) && (
          <div className="flex justify-between items-center">
            <span className="text-sm font-medium text-gray-700">{label || 'Progress'}</span>
            <span className="text-sm font-semibold text-gray-900">{Math.round(percentage)}%</span>
          </div>
        )}
        <div className={cn(baseStyles, sizes[size])}>
          <div
            className={cn('h-full transition-all duration-500 ease-out rounded-full', variants[variant])}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    );
  }
);

interface CircularProgressProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number;
  max?: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'success' | 'warning' | 'danger';
  showLabel?: boolean;
  label?: string;
}

const CircularProgress = React.forwardRef<HTMLDivElement, CircularProgressProps>(
  ({ className, value, max = 100, size = 'md', variant = 'default', showLabel = false, label, ...props }, ref) => {
    const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
    const circumference = 2 * Math.PI * 45; // radius = 45
    const strokeDashoffset = circumference - (percentage / 100) * circumference;
    
    const sizes = {
      sm: 'w-12 h-12',
      md: 'w-16 h-16',
      lg: 'w-24 h-24',
    };
    
    const variants = {
      default: 'stroke-blue-600',
      success: 'stroke-green-600',
      warning: 'stroke-amber-600',
      danger: 'stroke-red-600',
    };

    return (
      <div ref={ref} className={cn('flex flex-col items-center space-y-3', className)} {...props}>
        <div className={cn('relative', sizes[size])}>
          <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="45"
              stroke="currentColor"
              strokeWidth="6"
              fill="none"
              className="text-gray-200"
            />
            <circle
              cx="50"
              cy="50"
              r="45"
              strokeWidth="6"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className={cn('transition-all duration-700 ease-out', variants[variant])}
            />
          </svg>
          {showLabel && (
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-sm font-semibold text-gray-900">
                {Math.round(percentage)}%
              </span>
            </div>
          )}
        </div>
        {label && (
          <span className="text-sm font-medium text-gray-700">{label}</span>
        )}
      </div>
    );
  }
);

export { Progress, CircularProgress };
export default Progress;