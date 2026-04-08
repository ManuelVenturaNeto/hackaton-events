import React from 'react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface BadgeProps extends React.ComponentProps<'div'> {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info' | 'outline';
  children?: React.ReactNode;
  className?: string;
}

export function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  const variants = {
    default: 'bg-gray-100 text-gray-800 border-transparent',
    success: 'bg-green-100 text-green-800 border-transparent',
    warning: 'bg-yellow-100 text-yellow-800 border-transparent',
    danger: 'bg-red-100 text-red-800 border-transparent',
    info: 'bg-blue-100 text-blue-800 border-transparent',
    outline: 'text-gray-800 border-gray-300'
  };

  return (
    <div
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
