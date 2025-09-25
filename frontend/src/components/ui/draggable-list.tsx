import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GripVertical } from 'lucide-react';
import { cn } from '../../lib/utils';

interface DraggableItem {
  id: string;
  content: React.ReactNode;
}

interface DraggableListProps {
  items: DraggableItem[];
  onReorder: (items: DraggableItem[]) => void;
  className?: string;
  itemClassName?: string;
}

export const DraggableList: React.FC<DraggableListProps> = ({
  items,
  onReorder,
  className,
  itemClassName
}) => {
  const [draggedItem, setDraggedItem] = useState<string | null>(null);
  const [dragOverItem, setDragOverItem] = useState<string | null>(null);

  const handleDragStart = (e: React.DragEvent, itemId: string) => {
    setDraggedItem(itemId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, itemId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverItem(itemId);
  };

  const handleDragLeave = () => {
    setDragOverItem(null);
  };

  const handleDrop = (e: React.DragEvent, targetItemId: string) => {
    e.preventDefault();
    
    if (!draggedItem || draggedItem === targetItemId) {
      setDraggedItem(null);
      setDragOverItem(null);
      return;
    }

    const draggedIndex = items.findIndex(item => item.id === draggedItem);
    const targetIndex = items.findIndex(item => item.id === targetItemId);
    
    if (draggedIndex === -1 || targetIndex === -1) return;

    const newItems = [...items];
    const [draggedItemData] = newItems.splice(draggedIndex, 1);
    newItems.splice(targetIndex, 0, draggedItemData);
    
    onReorder(newItems);
    setDraggedItem(null);
    setDragOverItem(null);
  };

  return (
    <div className={cn("space-y-2", className)}>
      <AnimatePresence>
        {items.map((item) => (
          <motion.div
            key={item.id}
            layout
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            draggable
            onDragStart={(e) => handleDragStart(e as unknown as React.DragEvent, item.id)}
            onDragOver={(e) => handleDragOver(e as unknown as React.DragEvent, item.id)}
            onDragLeave={handleDragLeave}
            onDrop={(e) => handleDrop(e as unknown as React.DragEvent, item.id)}
            className={cn(
              "flex items-center space-x-3 p-3 bg-white rounded-lg border shadow-sm",
              "hover:shadow-md transition-shadow duration-200",
              "cursor-move select-none",
              draggedItem === item.id && "opacity-50",
              dragOverItem === item.id && "border-blue-500 bg-blue-50",
              itemClassName
            )}
          >
            <GripVertical className="h-4 w-4 text-gray-400" />
            <div className="flex-1">{item.content}</div>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};


