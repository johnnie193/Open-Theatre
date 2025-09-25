import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Avatar, AvatarFallback, AvatarImage } from './avatar';
import { TypingText } from './typing-text';
import { cn } from '../../lib/utils';

interface AnimatedMessageProps {
  id: string;
  character: string;
  content: string;
  avatar?: string;
  timestamp: Date;
  type: 'speak' | 'stay';
  className?: string;
}

export const AnimatedMessage: React.FC<AnimatedMessageProps> = ({
  id,
  character,
  content,
  avatar,
  timestamp,
  type,
  className
}) => {
  const [isTyping, setIsTyping] = useState(true);
  const [showContent, setShowContent] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsTyping(false);
      setShowContent(true);
    }, 1000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.3 }}
      className={cn("flex space-x-3", className)}
    >
      <Avatar className="h-8 w-8">
        <AvatarImage src={avatar} alt={character} />
        <AvatarFallback>{character.charAt(0)}</AvatarFallback>
      </Avatar>
      
      <div className="flex-1">
        <div className="flex items-center space-x-2 mb-1">
          <span className="font-medium text-sm">{character}</span>
          <span className="text-xs text-gray-500">
            {timestamp.toLocaleTimeString()}
          </span>
        </div>
        
        <div className="message-bubble">
          <AnimatePresence mode="wait">
            {isTyping ? (
              <motion.div
                key="typing"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="flex items-center space-x-1"
              >
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="content"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <TypingText 
                  text={content} 
                  speed={30}
                  onComplete={() => setShowContent(true)}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
};
