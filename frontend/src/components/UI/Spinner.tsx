import React from 'react';
import { cn } from '../../lib/utils';

interface SpinnerProps {
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'default' | 'primary' | 'secondary';
  className?: string;
}

const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  variant = 'default',
  className
}) => {
  const sizes = {
    xs: 'w-3 h-3',
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  };

  const variants = {
    default: 'text-gray-600 dark:text-gray-400',
    primary: 'text-blue-600 dark:text-blue-400',
    secondary: 'text-gray-400 dark:text-gray-600'
  };

  return (
    <svg
      className={cn(
        'animate-spin',
        sizes[size],
        variants[variant],
        className
      )}
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      role="status"
      aria-label="Loading"
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
      />
    </svg>
  );
};

// Loading Overlay Component
interface LoadingOverlayProps {
  isLoading: boolean;
  children: React.ReactNode;
  message?: string;
  spinnerSize?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
}

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({
  isLoading,
  children,
  message = 'Loading...',
  spinnerSize = 'lg',
  className
}) => {
  return (
    <div className={cn('relative', className)}>
      {children}
      {isLoading && (
        <div className="absolute inset-0 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm flex items-center justify-center z-10">
          <div className="flex flex-col items-center space-y-3">
            <Spinner size={spinnerSize} variant="primary" />
            {message && (
              <p className="text-sm text-gray-600 dark:text-gray-400 font-medium">
                {message}
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Dots Spinner Component
interface DotsSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'primary' | 'secondary';
  className?: string;
}

const DotsSpinner: React.FC<DotsSpinnerProps> = ({
  size = 'md',
  variant = 'default',
  className
}) => {
  const sizes = {
    sm: 'w-1 h-1',
    md: 'w-2 h-2',
    lg: 'w-3 h-3'
  };

  const variants = {
    default: 'bg-gray-600 dark:bg-gray-400',
    primary: 'bg-blue-600 dark:bg-blue-400',
    secondary: 'bg-gray-400 dark:bg-gray-600'
  };

  return (
    <div className={cn('flex space-x-1', className)} role="status" aria-label="Loading">
      {[0, 1, 2].map((index) => (
        <div
          key={index}
          className={cn(
            'rounded-full animate-pulse',
            sizes[size],
            variants[variant]
          )}
          style={{
            animationDelay: `${index * 0.2}s`,
            animationDuration: '1s'
          }}
        />
      ))}
    </div>
  );
};

// Pulse Spinner Component
interface PulseSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'primary' | 'secondary';
  className?: string;
}

const PulseSpinner: React.FC<PulseSpinnerProps> = ({
  size = 'md',
  variant = 'default',
  className
}) => {
  const sizes = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16'
  };

  const variants = {
    default: 'bg-gray-600 dark:bg-gray-400',
    primary: 'bg-blue-600 dark:bg-blue-400',
    secondary: 'bg-gray-400 dark:bg-gray-600'
  };

  return (
    <div
      className={cn(
        'rounded-full animate-pulse',
        sizes[size],
        variants[variant],
        className
      )}
      role="status"
      aria-label="Loading"
    />
  );
};

export { Spinner, LoadingOverlay, DotsSpinner, PulseSpinner };
export default Spinner;