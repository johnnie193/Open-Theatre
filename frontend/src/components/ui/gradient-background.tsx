import React from 'react';
import { cn } from '../../lib/utils';

interface GradientBackgroundProps {
  className?: string;
  variant?: 'default' | 'drama' | 'mystery' | 'romance';
}

export const GradientBackground: React.FC<GradientBackgroundProps> = ({
  className,
  variant = 'default'
}) => {
  const gradients = {
    default: 'from-blue-50 via-indigo-50 to-purple-50',
    drama: 'from-red-50 via-orange-50 to-yellow-50',
    mystery: 'from-gray-50 via-slate-50 to-zinc-50',
    romance: 'from-pink-50 via-rose-50 to-red-50'
  };

  return (
    <div className={cn(
      "absolute inset-0 bg-gradient-to-br -z-10",
      gradients[variant],
      className
    )}>
      {/* <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%239C92AC%22%20fill-opacity%3D%220.1%22%3E%3Ccircle%20cx%3D%2230%22%20cy%3D%2230%22%20r%3D%222%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-20" /> */}
    </div>
  );
};


