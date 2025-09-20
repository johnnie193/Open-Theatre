import { useState, useEffect, useRef } from 'react';
import { Card, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { ParticlesBackground } from './components/ui/particles-background';
import { GradientBackground } from './components/ui/gradient-background';
import { GlowText } from './components/ui/glow-text';
import { ThemeToggle } from './components/ui/theme-toggle';
import { NotificationContainer } from './components/ui/notification';
import { MagicEffects } from './components/ui/magic-effects';
import { 
  Settings, 
  FileText, 
  X,
  Upload
} from 'lucide-react';

// 导入组件
import { ScriptManagement } from './components/ScriptManagement';
import { PromptManagement } from './components/PromptManagement';
import { LoadScript, LoadScriptRef } from './components/LoadScript';
import { InfoPanels } from './components/InfoPanels';
import { GameInterface } from './components/GameInterface';
import { ModelConfig } from './components/ModelConfig';

// 导入API服务
import { apiService, GameState, Script } from './services/api';

// 类型定义
interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export default function App() {
  // 状态管理
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [activeTab, setActiveTab] = useState('current');
  
  // LoadScript组件的ref
  const loadScriptRef = useRef<LoadScriptRef>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);


  // 初始化游戏
  useEffect(() => {
    initializeGame();
  }, []);

  const initializeGame = async () => {
    try {
      const response = await apiService.initGame();
      console.log('API Response:', response);
        if (response.success && response.data && response.data.id && response.data.script) {
          console.log('Setting game state with complete data:', response.data);
          setGameState(response.data);
        } else {
        console.log('API call failed or incomplete data, showing welcome screen:', response);
        // 不设置gameState，让它保持null以显示欢迎界面
      }
    } catch (error) {
      console.error('Failed to initialize game:', error);
      // 不设置gameState，让它保持null以显示欢迎界面
    }
  };


  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  // 事件处理
  const handleGameStateChange = (newGameState: GameState) => {
    console.log('App: 更新gameState', {
      oldSceneCnt: gameState?.scene_cnt,
      newSceneCnt: newGameState.scene_cnt,
      newGameState
    });
    setGameState(newGameState);
  };


  const handleScriptChange = (script: Partial<Script>) => {
    if (gameState) {
      setGameState({ ...gameState, script: { ...gameState.script, ...script } });
    }
  };


  // 开始创建新剧本
  const handleCreateNewScript = () => {
    const newGameState: GameState = {
      id: 'new-script',
      scene_cnt: 1,
      nc: [],
      characters: {},
      scenes: {},
      script: {
        id: 'new-script',
        background: {
          player: '玩家',
          narrative: '',
          characters: {}
        },
        scenes: {}
      }
    };
    setGameState(newGameState);
    setSettingsOpen(true);
    setMessage({ type: 'success', text: '开始创建新剧本' });
  };

  // 加载示例剧本
  const handleLoadExampleScript = async () => {
    try {
      const response = await apiService.loadScript('load-script-hp');
      if (response.success && response.data) {
        setGameState(response.data);
        setMessage({ type: 'success', text: '示例剧本加载成功' });
      } else {
        setMessage({ type: 'error', text: response.error || '加载示例剧本失败' });
      }
    } catch (error) {
      console.error('加载示例剧本失败:', error);
      setMessage({ type: 'error', text: '加载示例剧本失败' });
    }
  };

  // 导入剧本文件
  const handleImportScript = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.yaml,.yml';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        try {
          await file.text();
          // 这里可以添加解析YAML文件的逻辑
          setMessage({ type: 'info', text: '剧本文件导入功能开发中...' });
        } catch (error) {
          setMessage({ type: 'error', text: '文件读取失败' });
        }
      }
    };
    input.click();
  };

  // 自动隐藏消息
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage(null);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  // 如果没有加载游戏状态或者游戏状态不完整，显示欢迎界面
  if (!gameState || !gameState.id || !gameState.script) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 dark:from-slate-900 dark:to-slate-800">
        <ParticlesBackground />
        <GradientBackground />
        
        {/* 通知容器 */}
        <NotificationContainer 
          notifications={notifications}
          onClose={removeNotification}
        />

        {/* 消息提示 */}
        {message && (
          <div className="fixed top-4 right-4 z-50">
            <div className={`px-4 py-2 rounded-lg shadow-lg ${
              message.type === 'success' ? 'bg-green-500 text-white' :
              message.type === 'error' ? 'bg-red-500 text-white' :
              'bg-blue-500 text-white'
            }`}>
              {message.text}
            </div>
          </div>
        )}

        {/* 欢迎界面 */}
        <div className="min-h-screen flex flex-col">
          {/* 头部 */}
          <div className="w-full p-6">
            <div className="flex items-center justify-between max-w-7xl mx-auto">
              <div className="flex items-center gap-4">
                <GlowText className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-cyan-600 to-slate-600 bg-clip-text text-transparent">
                  Open Theatre
                </GlowText>
                <Badge className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-0 px-3 py-1">
                  欢迎使用
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <ThemeToggle />
              </div>
            </div>
          </div>

          {/* 主内容 - 欢迎界面 */}
          <div className="flex-1 flex items-center justify-center px-6 py-12">
            <div className="w-full max-w-4xl mx-auto">
              {/* 主要内容卡片 */}
              <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-12 text-center">
                {/* 图标和标题 */}
                <div className="mb-12">
                  <div className="w-32 h-32 mx-auto mb-8 bg-gradient-to-br from-blue-400 via-cyan-400 to-slate-400 rounded-full flex items-center justify-center shadow-2xl">
                    <span className="text-6xl">🎭</span>
                  </div>
                  <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-blue-600 via-cyan-600 to-slate-600 bg-clip-text text-transparent">
                    欢迎来到 Open Theatre
                  </h1>
                  <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
                    创建您的互动戏剧，体验AI驱动的角色扮演
                  </p>
                </div>

                {/* 操作按钮 */}
                <div className="space-y-6 mb-12">
                  <Button 
                    size="lg" 
                    className="w-full max-w-md mx-auto h-16 text-lg font-semibold bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-xl hover:shadow-2xl transition-all duration-300"
                    onClick={handleCreateNewScript}
                  >
                    <Settings className="w-6 h-6 mr-3" />
                    开始创建剧本
                  </Button>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                    <Button 
                      variant="outline" 
                      size="lg" 
                      className="h-14 text-base font-medium border-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all duration-300"
                      onClick={handleLoadExampleScript}
                    >
                      <FileText className="w-5 h-5 mr-2" />
                      加载示例剧本
                    </Button>
                    <Button 
                      variant="outline" 
                      size="lg" 
                      className="h-14 text-base font-medium border-2 border-cyan-200 hover:border-cyan-400 hover:bg-cyan-50 dark:hover:bg-cyan-900/20 transition-all duration-300"
                      onClick={handleImportScript}
                    >
                      <Upload className="w-5 h-5 mr-2" />
                      导入剧本文件
                    </Button>
                  </div>
                </div>

                {/* 快速开始指南 */}
                <div className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-2xl p-8 border border-blue-100 dark:border-blue-800/30">
                  <h3 className="text-2xl font-bold mb-6 text-slate-800 dark:text-slate-200">快速开始</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="w-12 h-12 mx-auto mb-3 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                        <span className="text-2xl">📝</span>
                      </div>
                      <p className="text-slate-700 dark:text-slate-300 font-medium">
                        点击"开始创建剧本"设置基本信息和角色
                      </p>
                    </div>
                    <div className="text-center">
                      <div className="w-12 h-12 mx-auto mb-3 bg-cyan-100 dark:bg-cyan-900/30 rounded-full flex items-center justify-center">
                        <span className="text-2xl">⚡</span>
                      </div>
                      <p className="text-slate-700 dark:text-slate-300 font-medium">
                        选择或加载示例剧本快速体验
                      </p>
                    </div>
                    <div className="text-center">
                      <div className="w-12 h-12 mx-auto mb-3 bg-slate-100 dark:bg-slate-900/30 rounded-full flex items-center justify-center">
                        <span className="text-2xl">📁</span>
                      </div>
                      <p className="text-slate-700 dark:text-slate-300 font-medium">
                        导入现有的剧本文件继续编辑
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>


        {/* 魔法效果 */}
        <MagicEffects isActive={false} />
      </div>
    );
  }

  // 游戏主界面 - 参考原版布局
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <ParticlesBackground />
      <GradientBackground />
      
      {/* 通知容器 */}
      <NotificationContainer 
        notifications={notifications}
        onClose={removeNotification}
      />

      {/* 主容器 */}
      <div className="min-h-screen flex flex-col">
        {/* 头部 - 脚本名称 */}
        <div className="w-full p-6 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-white/20">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <GlowText className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-cyan-600 to-slate-600 bg-clip-text text-transparent">
                  Open Theatre
                </GlowText>
                <Badge className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-0 px-3 py-1">
                  {gameState?.id || '未命名剧本'}
                </Badge>
              </div>
              <div className="flex items-center gap-3">
                <ThemeToggle />
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSettingsOpen(!settingsOpen)}
                  className="border-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20"
                >
                  <Settings className="w-4 h-4 mr-2" />
                  设置
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* 主内容区域 - 居中布局 */}
        <div className="flex-1 flex justify-center p-6">
          <div className="w-full max-w-7xl flex gap-6">
            {/* 左侧聊天区域 */}
            <div className="flex-1 min-w-0 max-w-3xl">
              <GameInterface
                gameState={gameState}
                onGameStateChange={handleGameStateChange}
              />
            </div>

            {/* 右侧信息面板 */}
            <div className="w-[500px] flex-shrink-0">
              <InfoPanels
                gameState={gameState}
              />
            </div>
          </div>
        </div>
      </div>

      {/* 设置面板 */}
      {settingsOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <Card className="w-full max-w-6xl max-h-[90vh] overflow-hidden">
            <CardContent className="p-0">
              <div className="flex h-[80vh]">
                {/* 左侧导航 */}
                <div className="w-64 border-r bg-muted/50 p-4">
                  <Tabs value={activeTab} onValueChange={setActiveTab} orientation="vertical" className="w-full">
                    <TabsList className="grid w-full grid-cols-1 h-auto">
                      <TabsTrigger value="current" className="justify-start">当前脚本</TabsTrigger>
                      <TabsTrigger value="prompts" className="justify-start">提示词设置</TabsTrigger>
                      <TabsTrigger value="load" className="justify-start">读取脚本</TabsTrigger>
                      <TabsTrigger value="model" className="justify-start">模型配置</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>

                {/* 右侧内容 */}
                <div className="flex-1 p-6 overflow-auto">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold">设置</h2>
                    <Button variant="ghost" size="sm" onClick={() => setSettingsOpen(false)}>
                      <X className="w-4 h-4" />
                    </Button>
                  </div>

                  <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsContent value="current">
                      <ScriptManagement
                        script={gameState?.script || { 
                          id: '', 
                          background: { 
                            narrative: '', 
                            player: '', 
                            characters: {} 
                          }, 
                          scenes: {} 
                        }}
                        onScriptChange={handleScriptChange}
                        onGameStateChange={handleGameStateChange}
                      />
                    </TabsContent>
                    <TabsContent value="prompts">
                      <PromptManagement />
                    </TabsContent>
                    <TabsContent value="load">
                      <LoadScript ref={loadScriptRef} onGameStateChange={handleGameStateChange} />
                    </TabsContent>
                    <TabsContent value="model">
                      <ModelConfig />
                    </TabsContent>
                  </Tabs>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 魔法效果 */}
      <MagicEffects isActive={false} />
    </div>
  );
}