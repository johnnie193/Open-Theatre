import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface AnimatedButtonProps {
  children: React.ReactNode;
  onClick?: () => void;
  className?: string;
  variant?: 'default' | 'primary' | 'secondary' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
}

export const AnimatedButton: React.FC<AnimatedButtonProps> = ({
  children,
  onClick,
  className,
  variant = 'default',
  size = 'md',
  disabled = false
}) => {
  const variants = {
    default: 'bg-gray-100 hover:bg-gray-200 text-gray-900',
    primary: 'bg-blue-500 hover:bg-blue-600 text-white',
    secondary: 'bg-purple-500 hover:bg-purple-600 text-white',
    ghost: 'bg-transparent hover:bg-gray-100 text-gray-700'
  };

  const sizes = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      whileFocus={{ scale: 1.02 }}
      className={cn(
        'relative overflow-hidden rounded-lg font-medium transition-colors duration-200',
        'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className
      )}
    >
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
        initial={{ x: '-100%' }}
        whileHover={{ x: '100%' }}
        transition={{ duration: 0.6, ease: 'easeInOut' }}
      />
      <span className="relative z-10">{children}</span>
    </motion.button>
  );
};



