import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface GlowTextProps {
  children: React.ReactNode;
  className?: string;
  glowColor?: string;
  intensity?: number;
  animate?: boolean;
}

export const GlowText: React.FC<GlowTextProps> = ({
  children,
  className,
  glowColor = '#3B82F6',
  intensity = 0.5,
  animate = true
}) => {
  return (
    <motion.div
      className={cn('relative inline-block', className)}
      animate={animate ? {
        textShadow: [
          `0 0 10px ${glowColor}${Math.floor(intensity * 255).toString(16).padStart(2, '0')}`,
          `0 0 20px ${glowColor}${Math.floor(intensity * 255).toString(16).padStart(2, '0')}`,
          `0 0 10px ${glowColor}${Math.floor(intensity * 255).toString(16).padStart(2, '0')}`
        ]
      } : {}}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }}
    >
      {children}
    </motion.div>
  );
};



