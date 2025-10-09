import React, { useState, useEffect, useRef } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { 
  Send, 
  SkipForward, 
  SkipBack, 
  RotateCcw, 
  Download,
  MessageSquare,
  Loader2,
  AlertCircle,
  CheckCircle
} from 'lucide-react';
import { apiService, GameState, Message, InteractionRequest } from '../services/api';
import { AnimatedMessage } from './ui/animated-message';
import { Avatar, AvatarImage, AvatarFallback } from './ui/avatar';
import { MagicEffects } from './ui/magic-effects';

interface GameInterfaceProps {
  gameState: GameState | null;
  onGameStateChange: (gameState: GameState) => void;
}

export const GameInterface: React.FC<GameInterfaceProps> = ({
  gameState,
  onGameStateChange
}) => {
  const [messageInput, setMessageInput] = useState('');
  const [actionType, setActionType] = useState('-speak');
  const [targetCharacter, setTargetCharacter] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showMagicEffects, setShowMagicEffects] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [availableCharacters, setAvailableCharacters] = useState<string[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  // If gameState is null, show loading state
  if (!gameState) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading game state...</p>
        </div>
      </div>
    );
  }

  // Load available character list
  useEffect(() => {
    loadAvailableCharacters();
  }, []);

  // Reload character list when gameState changes
  useEffect(() => {
    if (gameState) {
      loadAvailableCharacters();
    }
  }, [gameState]);

  // Clear conversation history when script ID changes
  useEffect(() => {
    if (gameState?.script?.id) {
      setMessages([]);
    }
  }, [gameState?.script?.id]);

  // Scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadAvailableCharacters = async () => {
    try {
      console.log('Loading available characters...');
      const response = await apiService.getCharacters();
      console.log('Characters API response:', response);
      if (response.success && response.data) {
        // Filter out null, undefined and empty strings
        const validCharacters = (response.data.characters || [])
          .filter(char => char && char !== 'null' && char.trim() !== '');
        console.log('Filtered character list:', validCharacters);
        setAvailableCharacters(validCharacters);
      } else {
        console.log('Characters API call failed:', response.error);
        setAvailableCharacters([]);
      }
    } catch (error) {
      console.error('Failed to load characters:', error);
      setAvailableCharacters([]);
    }
  };

  // Send message
  const handleSendMessage = async () => {
    if (!messageInput.trim() && actionType === '-speak') return;

    setIsLoading(true);
    setShowMagicEffects(true);
    setMessage(null);

    try {
      const request: InteractionRequest = {
        type: actionType,
        message: messageInput.trim(),
        object: targetCharacter || undefined
      };

      const response = await apiService.calculateInteraction(request);
      
      if (response.success && response.data) {
        // Handle error cases
        if (response.data.error) {
          setMessage({ type: 'error', text: response.data.error });
          return;
        }

        // Add player message (based on original code logic)
        if (response.data.input && (response.data.input as any).x === '-speak') {
          let playerContent = '';
          if (Array.isArray((response.data.input as any).bid) && (response.data.input as any).bid.length > 0) {
            playerContent = '@ ' + (response.data.input as any).bid.join(', ') + '  ';
          }
          playerContent += (response.data.input as any).content;

          const playerMessage: Message = {
            id: Date.now().toString(),
            character: gameState?.script?.background?.player || 'Player',
            content: playerContent,
            timestamp: new Date(),
            type: 'speak',
            bid: (response.data.input as any).bid
          };
          setMessages(prev => [...prev, playerMessage]);
        }

        // Add character reply (based on original code logic)
        if (response.data.action && Array.isArray(response.data.action)) {
          const characterMessages: Message[] = response.data.action
            .filter((action: any) => action.x === '-speak')
            .map((action: any) => {
              let characterContent = '';
              if (Array.isArray(action.bid) && action.bid.length > 0) {
                characterContent = '@ ' + action.bid.join(', ') + '  ';
              } else if (typeof action.bid === 'string') {
                characterContent = '@ ' + action.bid + '  ';
              }
              characterContent += action.content;

              return {
                id: Date.now().toString() + Math.random(),
                character: action.aid,
                content: characterContent,
                timestamp: new Date(),
                type: 'speak',
                bid: action.bid
              };
            });
          setMessages(prev => [...prev, ...characterMessages]);
        }

        // 更新游戏状态
        if (response.data.done && response.data.state) {
          onGameStateChange(response.data.state);
          // Reload character list
          loadAvailableCharacters();
        }

        setMessageInput('');
        setTargetCharacter('');
        setMessage({ type: 'success', text: 'Message sent successfully' });
      } else {
        setMessage({ type: 'error', text: response.error || 'Send failed' });
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      setMessage({ type: 'error', text: 'Failed to send message' });
    } finally {
      setIsLoading(false);
      setTimeout(() => setShowMagicEffects(false), 2000);
    }
  };

  // Next scene
  const handleNextScene = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      console.log('Switching to next scene, current scene_cnt:', gameState?.scene_cnt);
      const response = await apiService.calculateInteraction({ interact: 'next' });
      console.log('Next scene API response:', response);
      if (response.success && response.data) {
        // Check API response structure, may return gameState directly instead of wrapped in state
        const gameStateData = response.data.state || response.data;
        console.log('Updated gameState, new scene_cnt:', (gameStateData as any).scene_cnt);
        onGameStateChange(gameStateData as GameState);
        // Reload available character list
        loadAvailableCharacters();
        setMessage({ type: 'success', text: 'Switched to next scene' });
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to switch scene' });
      }
    } catch (error) {
      console.error('Failed to switch scene:', error);
      setMessage({ type: 'error', text: 'Failed to switch scene' });
    } finally {
      setIsLoading(false);
    }
  };

  // Previous scene
  const handleBackScene = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      const response = await apiService.calculateInteraction({ interact: 'back' });
      if (response.success && response.data) {
        // Check API response structure, may return gameState directly instead of wrapped in state
        const gameStateData = response.data.state || response.data;
        console.log('Updated gameState, new scene_cnt:', (gameStateData as any).scene_cnt);
        onGameStateChange(gameStateData as GameState);
        // Reload available character list
        loadAvailableCharacters();
        setMessage({ type: 'success', text: 'Switched to previous scene' });
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to switch scene' });
      }
    } catch (error) {
      console.error('Failed to switch scene:', error);
      setMessage({ type: 'error', text: 'Failed to switch scene' });
    } finally {
      setIsLoading(false);
    }
  };

  // Withdraw message
  const handleWithdraw = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      const response = await apiService.calculateInteraction({ interact: 'withdraw' });
      if (response.success && response.data) {
        // Delete last few messages
        if (response.data && response.data.cnt) {
          setMessages(prev => prev.slice(0, -response.data!.cnt!));
        }
        // Reload available character list (equivalent to original code's updateInfoPanelBySubmit)
        loadAvailableCharacters();
        setMessage({ type: 'success', text: 'Message withdrawn' });
      } else {
        setMessage({ type: 'error', text: response.error || 'Withdraw failed' });
      }
    } catch (error) {
      console.error('Failed to withdraw message:', error);
      setMessage({ type: 'error', text: 'Failed to withdraw message' });
    } finally {
      setIsLoading(false);
    }
  };

  // Export records
  const handleExportRecords = async () => {
    try {
      const blob = await apiService.exportRecords();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `records_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      setMessage({ type: 'success', text: 'Records exported successfully' });
    } catch (error) {
      console.error('Failed to export records:', error);
      setMessage({ type: 'error', text: 'Failed to export records' });
    }
  };

  // Handle keyboard events
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Ensure scene_cnt is at least 1, as scenes start from scene1
  const effectiveSceneCnt = Math.max(gameState?.scene_cnt || 0, 1);
  const currentScene = gameState?.scenes?.[`scene${effectiveSceneCnt}`];
  const playerName = gameState?.script?.background?.player || 'Player';
  
  // Build scene title based on original code logic
  const sceneTitle = currentScene?.name 
    ? `Scene ${effectiveSceneCnt}  ${currentScene.name}`
    : `Scene ${effectiveSceneCnt}`;
  
  // Debug info
  console.log('GameInterface Debug:', {
    gameState,
    scene_cnt: gameState?.scene_cnt,
    effectiveSceneCnt,
    scenes: gameState?.scenes,
    currentScene,
    currentSceneMode: currentScene?.mode,
    sceneKey: `scene${effectiveSceneCnt}`,
    sceneTitle
  });

  return (
    <div className="h-[calc(100vh-200px)] flex flex-col space-y-4">
      {/* Scene info */}
      <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
              {sceneTitle}
            </h2>
            <p className="text-slate-600 dark:text-slate-300 mt-1 text-sm">
              {currentScene?.info ? currentScene.info.replace(/\\n/g, '<br>') : 'No scene information'}
            </p>
          </div>
          <Badge className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-0 px-3 py-1">
            {currentScene?.mode || 'v1'}
          </Badge>
        </div>
      </div>

      {/* Chat area - fixed height */}
      <div className="flex-1 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 overflow-hidden min-h-0">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-bold flex items-center gap-2 text-slate-800 dark:text-slate-200">
            <MessageSquare className="w-4 h-4" />
            Conversation History
          </h3>
        </div>
        <div className="h-[calc(100%-60px)] p-4">
          <ScrollArea className="h-full">
            <div className="space-y-3">
              {messages.map((msg) => (
                <AnimatedMessage
                  key={msg.id}
                  id={msg.id}
                  character={msg.character}
                  content={msg.content}
                  timestamp={msg.timestamp}
                  type={msg.type}
                  avatar={`/assets/${msg.character}.jpg`}
                />
              ))}
              {isLoading && (
                <div className="flex items-center justify-center py-6">
                  <div className="flex items-center gap-3">
                    <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                    <span className="text-slate-600 dark:text-slate-300">AI is thinking...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* Input area - fixed at bottom */}
      <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 p-4">
        <div className="space-y-4">
          {/* Action type and target selection */}
          <div className="flex items-center gap-3">
            <Select value={actionType} onValueChange={setActionType}>
              <SelectTrigger className="w-28 border-2 border-blue-200 hover:border-blue-400">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="-stay">-stay</SelectItem>
                <SelectItem value="-speak">-speak</SelectItem>
              </SelectContent>
            </Select>

            {actionType === '-speak' && (
              <Select value={targetCharacter || 'none'} onValueChange={(value) => setTargetCharacter(value === 'none' ? '' : value)}>
                <SelectTrigger className="w-40 border-2 border-cyan-200 hover:border-cyan-400">
                  <SelectValue placeholder="Select target character" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No target</SelectItem>
                  {availableCharacters?.map((char) => (
                    <SelectItem key={char} value={char}>
                      {char}
                    </SelectItem>
                  )) || []}
                </SelectContent>
              </Select>
            )}
            {/* Debug info */}
            {actionType === '-speak' && (
              <div className="text-xs text-gray-500">
                Characters: {availableCharacters?.length || 0}
              </div>
            )}
          </div>

          {/* Message input */}
          <div className="flex items-center gap-3">
            {/* Player avatar */}
            <Avatar>
              <AvatarImage src={`/assets/${playerName}.jpg`} alt={playerName} />
              <AvatarFallback>{playerName?.slice(0, 1) || 'P'}</AvatarFallback>
            </Avatar>
            <Input
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Enter your message..."
              className="flex-1 h-10 text-sm border-2 border-gray-200 hover:border-blue-300 focus:border-blue-500 transition-colors"
              disabled={isLoading}
            />
            <Button 
              onClick={handleSendMessage} 
              disabled={isLoading || (!messageInput.trim() && actionType === '-speak')}
              size="sm"
              className="h-10 px-4 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-lg hover:shadow-xl transition-all duration-300"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>

          {/* Status message */}
          {message && (
            <div className={`flex items-center gap-2 text-sm p-3 rounded-lg ${
              message.type === 'success' 
                ? 'bg-green-50 text-green-700 border border-green-200' 
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}>
              {message.type === 'success' ? (
                <CheckCircle className="w-4 h-4" />
              ) : (
                <AlertCircle className="w-4 h-4" />
              )}
              {message.text}
            </div>
          )}

          {/* Control buttons */}
          <div className="flex items-center gap-2 flex-wrap">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleNextScene}
              disabled={isLoading}
              className="h-8 px-3 text-xs border-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
            >
              <SkipForward className="w-3 h-3 mr-1" />
              Next Scene
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleBackScene}
              disabled={isLoading}
              className="h-8 px-3 text-xs border-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
            >
              <SkipBack className="w-3 h-3 mr-1" />
              Previous Scene
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleWithdraw}
              disabled={isLoading}
              className="h-8 px-3 text-xs border-2 border-orange-200 hover:border-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20"
            >
              <RotateCcw className="w-3 h-3 mr-1" />
              Withdraw
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleExportRecords}
              className="h-8 px-3 text-xs border-2 border-green-200 hover:border-green-400 hover:bg-green-50 dark:hover:bg-green-900/20"
            >
              <Download className="w-3 h-3 mr-1" />
              Export
            </Button>
          </div>
        </div>
      </div>

      {/* Magic effects */}
      {showMagicEffects && <MagicEffects isActive={true} />}
    </div>
  );
};