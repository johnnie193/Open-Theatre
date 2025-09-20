import React, { useState, useRef, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Copy, Download, Play, Square } from 'lucide-react';
import { cn } from '@/lib/utils';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  className?: string;
  readOnly?: boolean;
  showLineNumbers?: boolean;
  theme?: 'light' | 'dark';
  onRun?: (code: string) => void;
  onSave?: (code: string) => void;
}

export const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language = 'javascript',
  className,
  readOnly = false,
  showLineNumbers = true,
  theme = 'light',
  onRun,
  onSave
}) => {
  const [isFocused, setIsFocused] = useState(false);
  const [cursorPosition, setCursorPosition] = useState({ line: 1, column: 1 });
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  const lines = value.split('\n');
  const lineCount = lines.length;

  useEffect(() => {
    if (textareaRef.current) {
      const textarea = textareaRef.current;
      const textareaRect = textarea.getBoundingClientRect();
      const textareaStyle = getComputedStyle(textarea);
      
      const lineHeight = parseInt(textareaStyle.lineHeight);
      const paddingTop = parseInt(textareaStyle.paddingTop);
      const paddingLeft = parseInt(textareaStyle.paddingLeft);
      
      const scrollTop = textarea.scrollTop;
      const scrollLeft = textarea.scrollLeft;
      
      const textareaValue = textarea.value;
      const textBeforeCursor = textareaValue.substring(0, textarea.selectionStart);
      const linesBeforeCursor = textBeforeCursor.split('\n');
      const currentLine = linesBeforeCursor.length;
      const currentColumn = linesBeforeCursor[linesBeforeCursor.length - 1].length + 1;
      
      setCursorPosition({ line: currentLine, column: currentColumn });
    }
  }, [value]);

  const handleScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const textarea = textareaRef.current;
      if (textarea) {
        const start = textarea.selectionStart;
        const end = textarea.selectionEnd;
        const newValue = value.substring(0, start) + '  ' + value.substring(end);
        onChange(newValue);
        
        setTimeout(() => {
          textarea.selectionStart = textarea.selectionEnd = start + 2;
        }, 0);
      }
    }
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
  };

  const handleDownload = () => {
    const blob = new Blob([value], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `code.${language}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getLanguageColor = (lang: string) => {
    const colors: Record<string, string> = {
      javascript: 'text-yellow-600',
      python: 'text-blue-600',
      java: 'text-red-600',
      cpp: 'text-blue-500',
      c: 'text-blue-400',
      html: 'text-orange-600',
      css: 'text-blue-500',
      json: 'text-green-600',
      yaml: 'text-purple-600',
      markdown: 'text-gray-600'
    };
    return colors[lang] || 'text-gray-600';
  };

  return (
    <div className={cn("relative", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 bg-gray-100 dark:bg-gray-800 rounded-t-lg border-b">
        <div className="flex items-center space-x-2">
          <div className={cn("w-3 h-3 rounded-full", getLanguageColor(language))} />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {language.toUpperCase()}
          </span>
          <span className="text-xs text-gray-500">
            {cursorPosition.line}:{cursorPosition.column}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          {onRun && (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => onRun(value)}
              className="p-2 text-green-600 hover:bg-green-100 rounded-lg transition-colors"
            >
              <Play className="h-4 w-4" />
            </motion.button>
          )}
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleCopy}
            className="p-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <Copy className="h-4 w-4" />
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleDownload}
            className="p-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
          >
            <Download className="h-4 w-4" />
          </motion.button>
        </div>
      </div>

      {/* Editor */}
      <div className="relative flex">
        {/* Line Numbers */}
        {showLineNumbers && (
          <div
            ref={lineNumbersRef}
            className="flex-shrink-0 w-12 bg-gray-50 dark:bg-gray-900 text-right text-sm text-gray-500 dark:text-gray-400 py-3 px-2 border-r border-gray-200 dark:border-gray-700"
            style={{ lineHeight: '1.5rem' }}
          >
            {Array.from({ length: lineCount }, (_, i) => (
              <div key={i + 1} className="h-6 leading-6">
                {i + 1}
              </div>
            ))}
          </div>
        )}

        {/* Text Area */}
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onScroll={handleScroll}
            onKeyDown={handleKeyDown}
            readOnly={readOnly}
            className={cn(
              "w-full h-64 p-3 text-sm font-mono resize-none border-0 outline-none",
              "bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100",
              "placeholder-gray-500 dark:placeholder-gray-400",
              isFocused && "ring-2 ring-blue-500"
            )}
            style={{ lineHeight: '1.5rem' }}
            placeholder={`// 输入你的 ${language} 代码...`}
          />
          
          {/* Cursor */}
          {isFocused && (
            <motion.div
              className="absolute w-0.5 h-6 bg-blue-500 pointer-events-none"
              style={{
                left: `${cursorPosition.column * 8 + 12}px`,
                top: `${(cursorPosition.line - 1) * 24 + 12}px`
              }}
              animate={{ opacity: [1, 0, 1] }}
              transition={{ duration: 1, repeat: Infinity }}
            />
          )}
        </div>
      </div>
    </div>
  );
};



