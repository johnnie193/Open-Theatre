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

  // 如果gameState为null，显示加载状态
  if (!gameState) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">正在加载游戏状态...</p>
        </div>
      </div>
    );
  }

  // 加载可用角色列表
  useEffect(() => {
    loadAvailableCharacters();
  }, []);

  // 当gameState变化时重新加载角色列表
  useEffect(() => {
    if (gameState) {
      loadAvailableCharacters();
    }
  }, [gameState]);

  // 滚动到底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadAvailableCharacters = async () => {
    try {
      console.log('加载可用角色列表...');
      const response = await apiService.getCharacters();
      console.log('角色列表API响应:', response);
      if (response.success && response.data) {
        // 过滤掉null、undefined和空字符串
        const validCharacters = (response.data.characters || [])
          .filter(char => char && char !== 'null' && char.trim() !== '');
        console.log('过滤后的角色列表:', validCharacters);
        setAvailableCharacters(validCharacters);
      } else {
        console.log('角色列表API调用失败:', response.error);
        setAvailableCharacters([]);
      }
    } catch (error) {
      console.error('Failed to load characters:', error);
      setAvailableCharacters([]);
    }
  };

  // 发送消息
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
        // 处理错误情况
        if (response.data.error) {
          setMessage({ type: 'error', text: response.data.error });
          return;
        }

        // 添加玩家消息（根据原始代码逻辑）
        if (response.data.input && (response.data.input as any).x === '-speak') {
          let playerContent = '';
          if (Array.isArray((response.data.input as any).bid) && (response.data.input as any).bid.length > 0) {
            playerContent = '@ ' + (response.data.input as any).bid.join(', ') + '  ';
          }
          playerContent += (response.data.input as any).content;

          const playerMessage: Message = {
            id: Date.now().toString(),
            character: gameState?.script?.background?.player || '玩家',
            content: playerContent,
            timestamp: new Date(),
            type: 'speak',
            bid: (response.data.input as any).bid
          };
          setMessages(prev => [...prev, playerMessage]);
        }

        // 添加角色回复（根据原始代码逻辑）
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
          // 重新加载角色列表
          loadAvailableCharacters();
        }

        setMessageInput('');
        setTargetCharacter('');
        setMessage({ type: 'success', text: '消息发送成功' });
      } else {
        setMessage({ type: 'error', text: response.error || '发送失败' });
      }
    } catch (error) {
      console.error('发送消息失败:', error);
      setMessage({ type: 'error', text: '发送消息失败' });
    } finally {
      setIsLoading(false);
      setTimeout(() => setShowMagicEffects(false), 2000);
    }
  };

  // 下一场景
  const handleNextScene = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      console.log('切换到下一场景，当前scene_cnt:', gameState?.scene_cnt);
      const response = await apiService.calculateInteraction({ interact: 'next' });
      console.log('下一场景API响应:', response);
      if (response.success && response.data) {
        // 检查API响应结构，可能直接返回gameState而不是包装在state中
        const gameStateData = response.data.state || response.data;
        console.log('更新gameState，新scene_cnt:', (gameStateData as any).scene_cnt);
        onGameStateChange(gameStateData as GameState);
        // 重新加载可用角色列表
        loadAvailableCharacters();
        setMessage({ type: 'success', text: '已切换到下一场景' });
      } else {
        setMessage({ type: 'error', text: response.error || '切换场景失败' });
      }
    } catch (error) {
      console.error('切换场景失败:', error);
      setMessage({ type: 'error', text: '切换场景失败' });
    } finally {
      setIsLoading(false);
    }
  };

  // 上一场景
  const handleBackScene = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      const response = await apiService.calculateInteraction({ interact: 'back' });
      if (response.success && response.data) {
        // 检查API响应结构，可能直接返回gameState而不是包装在state中
        const gameStateData = response.data.state || response.data;
        console.log('更新gameState，新scene_cnt:', (gameStateData as any).scene_cnt);
        onGameStateChange(gameStateData as GameState);
        // 重新加载可用角色列表
        loadAvailableCharacters();
        setMessage({ type: 'success', text: '已切换到上一场景' });
      } else {
        setMessage({ type: 'error', text: response.error || '切换场景失败' });
      }
    } catch (error) {
      console.error('切换场景失败:', error);
      setMessage({ type: 'error', text: '切换场景失败' });
    } finally {
      setIsLoading(false);
    }
  };

  // 撤回消息
  const handleWithdraw = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      const response = await apiService.calculateInteraction({ interact: 'withdraw' });
      if (response.success && response.data) {
        // 删除最后几条消息
        if (response.data && response.data.cnt) {
          setMessages(prev => prev.slice(0, -response.data!.cnt!));
        }
        // 重新加载可用角色列表（相当于原始代码的updateInfoPanelBySubmit）
        loadAvailableCharacters();
        setMessage({ type: 'success', text: '消息已撤回' });
      } else {
        setMessage({ type: 'error', text: response.error || '撤回失败' });
      }
    } catch (error) {
      console.error('撤回消息失败:', error);
      setMessage({ type: 'error', text: '撤回消息失败' });
    } finally {
      setIsLoading(false);
    }
  };

  // 导出记录
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
      setMessage({ type: 'success', text: '记录导出成功' });
    } catch (error) {
      console.error('导出记录失败:', error);
      setMessage({ type: 'error', text: '导出记录失败' });
    }
  };

  // 处理键盘事件
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // 确保scene_cnt至少为1，因为场景从scene1开始
  const effectiveSceneCnt = Math.max(gameState?.scene_cnt || 0, 1);
  const currentScene = gameState?.scenes?.[`scene${effectiveSceneCnt}`];
  
  // 根据原始代码逻辑构建场景标题
  const sceneTitle = currentScene?.name 
    ? `场景 ${effectiveSceneCnt}  ${currentScene.name}`
    : `场景 ${effectiveSceneCnt}`;
  
  // 调试信息
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
      {/* 场景信息 */}
      <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 p-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
              {sceneTitle}
            </h2>
            <p className="text-slate-600 dark:text-slate-300 mt-1 text-sm">
              {currentScene?.info ? currentScene.info.replace(/\\n/g, '<br>') : '暂无场景信息'}
            </p>
          </div>
          <Badge className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-0 px-3 py-1">
            {currentScene?.mode || 'v1'}
          </Badge>
        </div>
      </div>

      {/* 聊天区域 - 固定高度 */}
      <div className="flex-1 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 overflow-hidden min-h-0">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-bold flex items-center gap-2 text-slate-800 dark:text-slate-200">
            <MessageSquare className="w-4 h-4" />
            对话记录
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
                    <span className="text-slate-600 dark:text-slate-300">AI正在思考...</span>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* 输入区域 - 固定在底部 */}
      <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-2xl shadow-xl border border-white/20 p-4">
        <div className="space-y-4">
          {/* 操作类型和目标选择 */}
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
                  <SelectValue placeholder="选择目标角色" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">无目标</SelectItem>
                  {availableCharacters?.map((char) => (
                    <SelectItem key={char} value={char}>
                      {char}
                    </SelectItem>
                  )) || []}
                </SelectContent>
              </Select>
            )}
            {/* 调试信息 */}
            {actionType === '-speak' && (
              <div className="text-xs text-gray-500">
                角色数: {availableCharacters?.length || 0}
              </div>
            )}
          </div>

          {/* 消息输入 */}
          <div className="flex items-center gap-3">
            <Input
              value={messageInput}
              onChange={(e) => setMessageInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入你的消息..."
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

          {/* 状态消息 */}
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

          {/* 控制按钮 */}
          <div className="flex items-center gap-2 flex-wrap">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleNextScene}
              disabled={isLoading}
              className="h-8 px-3 text-xs border-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
            >
              <SkipForward className="w-3 h-3 mr-1" />
              下一场景
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleBackScene}
              disabled={isLoading}
              className="h-8 px-3 text-xs border-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
            >
              <SkipBack className="w-3 h-3 mr-1" />
              上一场景
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleWithdraw}
              disabled={isLoading}
              className="h-8 px-3 text-xs border-2 border-orange-200 hover:border-orange-400 hover:bg-orange-50 dark:hover:bg-orange-900/20"
            >
              <RotateCcw className="w-3 h-3 mr-1" />
              撤回
            </Button>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={handleExportRecords}
              className="h-8 px-3 text-xs border-2 border-green-200 hover:border-green-400 hover:bg-green-50 dark:hover:bg-green-900/20"
            >
              <Download className="w-3 h-3 mr-1" />
              导出
            </Button>
          </div>
        </div>
      </div>

      {/* 魔法效果 */}
      {showMagicEffects && <MagicEffects isActive={true} />}
    </div>
  );
};