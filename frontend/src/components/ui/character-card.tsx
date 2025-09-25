import React from 'react';
import { motion } from 'framer-motion';
import { Avatar, AvatarFallback, AvatarImage } from './avatar';
import { Badge } from './badge';
import { cn } from '@/lib/utils';

interface CharacterCardProps {
  character: {
    id: string;
    name: string;
    avatar: string;
    profile: string;
    selected?: boolean;
  };
  onClick?: () => void;
  className?: string;
}

export const CharacterCard: React.FC<CharacterCardProps> = ({
  character,
  onClick,
  className
}) => {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        "flex items-center space-x-3 p-3 rounded-lg cursor-pointer transition-all duration-200",
        character.selected 
          ? 'bg-blue-50 border border-blue-200 shadow-md' 
          : 'hover:bg-gray-50 hover:shadow-sm',
        className
      )}
    >
      <div className="relative">
        <Avatar className="h-12 w-12">
          <AvatarImage src={character.avatar} alt={character.name} />
          <AvatarFallback>{character.name.charAt(0)}</AvatarFallback>
        </Avatar>
        {character.selected && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className="absolute -top-1 -right-1 w-4 h-4 bg-blue-500 rounded-full flex items-center justify-center"
          >
            <div className="w-2 h-2 bg-white rounded-full" />
          </motion.div>
        )}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2 mb-1">
          <p className="font-medium text-sm truncate">{character.name}</p>
          {character.selected && (
            <Badge variant="secondary" className="text-xs">
              已选择
            </Badge>
          )}
        </div>
        <p className="text-xs text-gray-500 line-clamp-2">
          {character.profile}
        </p>
      </div>
    </motion.div>
  );
};



