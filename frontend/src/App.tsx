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

// Import components
import { ScriptManagement } from './components/ScriptManagement';
import { PromptManagement } from './components/PromptManagement';
import { LoadScript, LoadScriptRef } from './components/LoadScript';
import { InfoPanels } from './components/InfoPanels';
import { GameInterface } from './components/GameInterface';
import { ModelConfig } from './components/ModelConfig';

// Import API service
import { apiService, GameState, Script } from './services/api';

// Type definitions
interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
  duration?: number;
}

export default function App() {
  // State management
  const [gameState, setGameState] = useState<GameState | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [activeTab, setActiveTab] = useState('current');
  
  // LoadScript component ref
  const loadScriptRef = useRef<LoadScriptRef>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);


  // Initialize game
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
        // Don't set gameState, keep it null to show welcome screen
      }
    } catch (error) {
      console.error('Failed to initialize game:', error);
      // Don't set gameState, keep it null to show welcome screen
    }
  };


  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  // Event handlers
  const handleGameStateChange = (newGameState: GameState) => {
    console.log('App: Updating gameState', {
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


  // Start creating new script
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
          player: 'Player',
          narrative: '',
          characters: {}
        },
        scenes: {}
      }
    };
    setGameState(newGameState);
    setSettingsOpen(true);
    setMessage({ type: 'success', text: 'Started creating new script' });
  };

  // Load example script
  const handleLoadExampleScript = async () => {
    try {
      const response = await apiService.loadScript('load-script-hp');
      if (response.success && response.data) {
        setGameState(response.data);
        setMessage({ type: 'success', text: 'Example script loaded successfully' });
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to load example script' });
      }
    } catch (error) {
      console.error('Failed to load example script:', error);
      setMessage({ type: 'error', text: 'Failed to load example script' });
    }
  };

  // Import script file
  const handleImportScript = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.yaml,.yml';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        try {
          await file.text();
          // Here you can add YAML file parsing logic
          setMessage({ type: 'info', text: 'Script file import feature under development...' });
        } catch (error) {
          setMessage({ type: 'error', text: 'File read failed' });
        }
      }
    };
    input.click();
  };

  // Auto-hide messages
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => {
        setMessage(null);
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  // If no game state loaded or incomplete, show welcome screen
  if (!gameState || !gameState.id || !gameState.script) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50 dark:from-slate-900 dark:to-slate-800">
        <ParticlesBackground />
        <GradientBackground />
        
        {/* Notification container */}
        <NotificationContainer 
          notifications={notifications}
          onClose={removeNotification}
        />

        {/* Message notifications */}
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

        {/* Welcome screen */}
        <div className="min-h-screen flex flex-col">
          {/* Header */}
          <div className="w-full p-6">
            <div className="flex items-center justify-between max-w-7xl mx-auto">
              <div className="flex items-center gap-4">
                <GlowText className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-cyan-600 to-slate-600 bg-clip-text text-transparent">
                  Open Theatre
                </GlowText>
                <Badge className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-0 px-3 py-1">
                  Welcome
                </Badge>
              </div>
              <div className="flex items-center gap-2">
                <ThemeToggle />
              </div>
            </div>
          </div>

          {/* Main content - Welcome screen */}
          <div className="flex-1 flex items-center justify-center px-6 py-12">
            <div className="w-full max-w-4xl mx-auto">
              {/* Main content card */}
              <div className="bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-12 text-center">
                {/* Icon and title */}
                <div className="mb-12">
                  <div className="w-32 h-32 mx-auto mb-8 bg-gradient-to-br from-blue-400 via-cyan-400 to-slate-400 rounded-full flex items-center justify-center shadow-2xl">
                    <span className="text-6xl">🎭</span>
                  </div>
                  <h1 className="text-5xl font-bold mb-6 bg-gradient-to-r from-blue-600 via-cyan-600 to-slate-600 bg-clip-text text-transparent">
                    Welcome to Open Theatre
                  </h1>
                  <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
                    Create your interactive drama, experience AI-driven role-playing
                  </p>
                </div>

                {/* Action buttons */}
                <div className="space-y-6 mb-12">
                  <Button 
                    size="lg" 
                    className="w-full max-w-md mx-auto h-16 text-lg font-semibold bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 shadow-xl hover:shadow-2xl transition-all duration-300"
                    onClick={handleCreateNewScript}
                  >
                    <Settings className="w-6 h-6 mr-3" />
                    Start Creating Script
                  </Button>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl mx-auto">
                    <Button 
                      variant="outline" 
                      size="lg" 
                      className="h-14 text-base font-medium border-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 transition-all duration-300"
                      onClick={handleLoadExampleScript}
                    >
                      <FileText className="w-5 h-5 mr-2" />
                      Load Example Script
                    </Button>
                    <Button 
                      variant="outline" 
                      size="lg" 
                      className="h-14 text-base font-medium border-2 border-cyan-200 hover:border-cyan-400 hover:bg-cyan-50 dark:hover:bg-cyan-900/20 transition-all duration-300"
                      onClick={handleImportScript}
                    >
                      <Upload className="w-5 h-5 mr-2" />
                      Import Script File
                    </Button>
                  </div>
                </div>

                {/* Quick start guide */}
                <div className="bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20 rounded-2xl p-8 border border-blue-100 dark:border-blue-800/30">
                  <h3 className="text-2xl font-bold mb-6 text-slate-800 dark:text-slate-200">Quick Start</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="text-center">
                      <div className="w-12 h-12 mx-auto mb-3 bg-blue-100 dark:bg-blue-900/30 rounded-full flex items-center justify-center">
                        <span className="text-2xl">📝</span>
                      </div>
                      <p className="text-slate-700 dark:text-slate-300 font-medium">
                        Click "Start Creating Script" to set basic info and characters
                      </p>
                    </div>
                    <div className="text-center">
                      <div className="w-12 h-12 mx-auto mb-3 bg-cyan-100 dark:bg-cyan-900/30 rounded-full flex items-center justify-center">
                        <span className="text-2xl">⚡</span>
                      </div>
                      <p className="text-slate-700 dark:text-slate-300 font-medium">
                        Select or load example script for quick experience
                      </p>
                    </div>
                    <div className="text-center">
                      <div className="w-12 h-12 mx-auto mb-3 bg-slate-100 dark:bg-slate-900/30 rounded-full flex items-center justify-center">
                        <span className="text-2xl">📁</span>
                      </div>
                      <p className="text-slate-700 dark:text-slate-300 font-medium">
                        Import existing script files to continue editing
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>


        {/* Magic effects */}
        <MagicEffects isActive={false} />
      </div>
    );
  }

  // Main game interface - based on original layout
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <ParticlesBackground />
      <GradientBackground />
      
      {/* Notification container */}
      <NotificationContainer 
        notifications={notifications}
        onClose={removeNotification}
      />

      {/* Main container */}
      <div className="min-h-screen flex flex-col">
        {/* Header - Script name */}
        <div className="w-full p-6 bg-white/80 dark:bg-gray-900/80 backdrop-blur-xl border-b border-white/20">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <GlowText className="text-4xl font-bold bg-gradient-to-r from-blue-600 via-cyan-600 to-slate-600 bg-clip-text text-transparent">
                  Open Theatre
                </GlowText>
                <Badge className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-0 px-3 py-1">
                  {gameState?.id || 'Untitled Script'}
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
                  Settings
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* Main content area - centered layout */}
        <div className="flex-1 flex justify-center p-6">
          <div className="w-full max-w-7xl flex gap-6">
            {/* Left chat area */}
            <div className="flex-1 min-w-0 max-w-3xl">
              <GameInterface
                gameState={gameState}
                onGameStateChange={handleGameStateChange}
              />
            </div>

            {/* Right info panel */}
            <div className="w-[500px] flex-shrink-0">
              <InfoPanels
                gameState={gameState}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Settings panel */}
      {settingsOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          {/* Close button in top-right corner for easy access */}
          <button
            onClick={() => setSettingsOpen(false)}
            aria-label="Close settings"
            className="absolute top-4 right-4 p-3 rounded-full bg-white/80 hover:bg-white shadow-lg border border-white/60 backdrop-blur-sm transition-colors dark:bg-gray-800/80 dark:hover:bg-gray-800"
          >
            <X className="w-5 h-5" />
          </button>
          <Card className="w-full max-w-6xl max-h-[90vh] overflow-hidden">
            <CardContent className="p-0">
              <div className="flex h-[80vh]">
                {/* Left navigation */}
                <div className="w-64 border-r bg-muted/50 p-4">
                  <Tabs value={activeTab} onValueChange={setActiveTab} orientation="vertical" className="w-full">
                    <TabsList className="grid w-full grid-cols-1 h-auto">
                      <TabsTrigger value="current" className="justify-start">Current Script</TabsTrigger>
                      <TabsTrigger value="prompts" className="justify-start">Prompt Settings</TabsTrigger>
                      <TabsTrigger value="load" className="justify-start">Load Script</TabsTrigger>
                      <TabsTrigger value="model" className="justify-start">Model Config</TabsTrigger>
                    </TabsList>
                  </Tabs>
                </div>

                {/* Right content */}
                <div className="flex-1 p-6 overflow-auto">
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold">Settings</h2>
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
                      <LoadScript 
                        ref={loadScriptRef} 
                        onGameStateChange={handleGameStateChange} 
                        onNewScript={handleCreateNewScript}
                      />
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

      {/* Magic effects */}
      <MagicEffects isActive={false} />
    </div>
  );
}