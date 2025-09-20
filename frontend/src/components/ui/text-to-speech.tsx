import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Volume2, VolumeX, Play, Pause } from 'lucide-react';
import { cn } from '@/lib/utils';

interface TextToSpeechProps {
  text: string;
  className?: string;
  autoPlay?: boolean;
  rate?: number;
  pitch?: number;
  volume?: number;
}

export const TextToSpeech: React.FC<TextToSpeechProps> = ({
  text,
  className,
  autoPlay = false,
  rate = 1,
  pitch = 1,
  volume = 1
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [utterance, setUtterance] = useState<SpeechSynthesisUtterance | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      setIsSupported(true);
    }
  }, []);

  useEffect(() => {
    if (isSupported && text) {
      const newUtterance = new SpeechSynthesisUtterance(text);
      newUtterance.rate = rate;
      newUtterance.pitch = pitch;
      newUtterance.volume = volume;
      newUtterance.lang = 'zh-CN';

      newUtterance.onstart = () => setIsPlaying(true);
      newUtterance.onend = () => setIsPlaying(false);
      newUtterance.onerror = () => setIsPlaying(false);

      setUtterance(newUtterance);

      if (autoPlay) {
        speechSynthesis.speak(newUtterance);
      }
    }
  }, [text, isSupported, rate, pitch, volume, autoPlay]);

  const play = () => {
    if (utterance && !isPlaying) {
      speechSynthesis.speak(utterance);
    }
  };

  const pause = () => {
    if (isPlaying) {
      speechSynthesis.pause();
    }
  };

  const stop = () => {
    speechSynthesis.cancel();
    setIsPlaying(false);
  };

  if (!isSupported) {
    return null;
  }

  return (
    <div className={cn("flex items-center space-x-2", className)}>
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={isPlaying ? pause : play}
        className={cn(
          "p-2 rounded-full transition-colors duration-200",
          isPlaying 
            ? "bg-green-500 text-white" 
            : "bg-blue-500 text-white hover:bg-blue-600"
        )}
      >
        {isPlaying ? (
          <Pause className="h-4 w-4" />
        ) : (
          <Play className="h-4 w-4" />
        )}
      </motion.button>

      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={stop}
        className="p-2 rounded-full bg-gray-500 text-white hover:bg-gray-600 transition-colors duration-200"
      >
        <VolumeX className="h-4 w-4" />
      </motion.button>

      {isPlaying && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.8 }}
          className="flex items-center space-x-1 text-sm text-gray-600"
        >
          <div className="flex space-x-1">
            <div className="w-1 h-4 bg-green-500 rounded-full animate-pulse" />
            <div className="w-1 h-4 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.1s' }} />
            <div className="w-1 h-4 bg-green-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
          </div>
          <span>正在播放...</span>
        </motion.div>
      )}
    </div>
  );
};



