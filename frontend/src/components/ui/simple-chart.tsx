import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface DataPoint {
  label: string;
  value: number;
  color?: string;
}

interface SimpleChartProps {
  data: DataPoint[];
  type?: 'bar' | 'line' | 'pie';
  className?: string;
  animated?: boolean;
}

export const SimpleChart: React.FC<SimpleChartProps> = ({
  data,
  type = 'bar',
  className,
  animated = true
}) => {
  const maxValue = Math.max(...data.map(d => d.value));
  const totalValue = data.reduce((sum, d) => sum + d.value, 0);

  if (type === 'bar') {
    return (
      <div className={cn("w-full h-64 flex items-end space-x-2", className)}>
        {data.map((point, index) => (
          <div key={point.label} className="flex-1 flex flex-col items-center">
            <motion.div
              className={cn(
                "w-full rounded-t",
                point.color || 'bg-blue-500'
              )}
              initial={{ height: 0 }}
              animate={{ height: `${(point.value / maxValue) * 100}%` }}
              transition={animated ? { duration: 0.8, delay: index * 0.1 } : { duration: 0 }}
            />
            <span className="text-xs text-gray-600 mt-2 text-center">
              {point.label}
            </span>
            <span className="text-xs text-gray-500">
              {point.value}
            </span>
          </div>
        ))}
      </div>
    );
  }

  if (type === 'line') {
    const points = data.map((point, index) => ({
      x: (index / (data.length - 1)) * 100,
      y: 100 - (point.value / maxValue) * 100
    }));

    const pathData = points
      .map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`)
      .join(' ');

    return (
      <div className={cn("w-full h-64 relative", className)}>
        <svg className="w-full h-full" viewBox="0 0 100 100" preserveAspectRatio="none">
          <motion.path
            d={pathData}
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-blue-500"
            initial={{ pathLength: 0 }}
            animate={{ pathLength: 1 }}
            transition={animated ? { duration: 1 } : { duration: 0 }}
          />
          {points.map((point, index) => (
            <motion.circle
              key={index}
              cx={point.x}
              cy={point.y}
              r="2"
              fill="currentColor"
              className="text-blue-500"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={animated ? { duration: 0.3, delay: index * 0.1 } : { duration: 0 }}
            />
          ))}
        </svg>
      </div>
    );
  }

  if (type === 'pie') {
    let currentAngle = 0;
    const radius = 40;
    const centerX = 50;
    const centerY = 50;

    return (
      <div className={cn("w-full h-64 flex items-center justify-center", className)}>
        <svg className="w-32 h-32" viewBox="0 0 100 100">
          {data.map((point, index) => {
            const percentage = point.value / totalValue;
            const angle = percentage * 360;
            const startAngle = currentAngle;
            const endAngle = currentAngle + angle;
            
            const x1 = centerX + radius * Math.cos((startAngle - 90) * Math.PI / 180);
            const y1 = centerY + radius * Math.sin((startAngle - 90) * Math.PI / 180);
            const x2 = centerX + radius * Math.cos((endAngle - 90) * Math.PI / 180);
            const y2 = centerY + radius * Math.sin((endAngle - 90) * Math.PI / 180);
            
            const largeArcFlag = angle > 180 ? 1 : 0;
            const pathData = `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
            
            currentAngle += angle;
            
            return (
              <motion.path
                key={point.label}
                d={pathData}
                fill={point.color || `hsl(${index * 60}, 70%, 50%)`}
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={animated ? { duration: 0.5, delay: index * 0.1 } : { duration: 0 }}
              />
            );
          })}
        </svg>
      </div>
    );
  }

  return null;
};



