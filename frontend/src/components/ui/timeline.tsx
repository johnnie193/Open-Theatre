import React from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface TimelineItem {
  id: string;
  title: string;
  description?: string;
  timestamp: Date;
  status: 'completed' | 'current' | 'upcoming';
  icon?: React.ReactNode;
}

interface TimelineProps {
  items: TimelineItem[];
  className?: string;
  orientation?: 'vertical' | 'horizontal';
}

export const Timeline: React.FC<TimelineProps> = ({
  items,
  className,
  orientation = 'vertical'
}) => {
  const getStatusColor = (status: TimelineItem['status']) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500 border-green-500';
      case 'current':
        return 'bg-blue-500 border-blue-500';
      case 'upcoming':
        return 'bg-gray-300 border-gray-300';
      default:
        return 'bg-gray-300 border-gray-300';
    }
  };

  const getStatusTextColor = (status: TimelineItem['status']) => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'current':
        return 'text-blue-600';
      case 'upcoming':
        return 'text-gray-500';
      default:
        return 'text-gray-500';
    }
  };

  if (orientation === 'horizontal') {
    return (
      <div className={cn("flex items-center space-x-4", className)}>
        {items.map((item, index) => (
          <div key={item.id} className="flex items-center">
            <div className="flex flex-col items-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className={cn(
                  "w-8 h-8 rounded-full border-2 flex items-center justify-center",
                  getStatusColor(item.status)
                )}
              >
                {item.icon || (
                  <div className="w-2 h-2 bg-white rounded-full" />
                )}
              </motion.div>
              <div className="mt-2 text-center">
                <p className={cn("text-sm font-medium", getStatusTextColor(item.status))}>
                  {item.title}
                </p>
                <p className="text-xs text-gray-500">
                  {item.timestamp.toLocaleDateString()}
                </p>
              </div>
            </div>
            {index < items.length - 1 && (
              <div className="w-8 h-0.5 bg-gray-300 mx-2" />
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className={cn("space-y-4", className)}>
      {items.map((item, index) => (
        <motion.div
          key={item.id}
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.1 }}
          className="flex items-start space-x-4"
        >
          <div className="flex flex-col items-center">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: index * 0.1 + 0.2 }}
              className={cn(
                "w-8 h-8 rounded-full border-2 flex items-center justify-center",
                getStatusColor(item.status)
              )}
            >
              {item.icon || (
                <div className="w-2 h-2 bg-white rounded-full" />
              )}
            </motion.div>
            {index < items.length - 1 && (
              <div className="w-0.5 h-16 bg-gray-300 mt-2" />
            )}
          </div>
          
          <div className="flex-1 pb-8">
            <div className="flex items-center space-x-2">
              <h3 className={cn("text-lg font-medium", getStatusTextColor(item.status))}>
                {item.title}
              </h3>
              <span className="text-sm text-gray-500">
                {item.timestamp.toLocaleDateString()}
              </span>
            </div>
            {item.description && (
              <p className="mt-1 text-sm text-gray-600">
                {item.description}
              </p>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
};



