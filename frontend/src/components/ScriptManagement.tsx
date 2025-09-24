import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { ScrollArea } from './ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { 
  Settings, 
  Loader2,
  CheckCircle,
  AlertCircle,
  Plus,
  Trash2,
  Users,
  MapPin
} from 'lucide-react';
import { apiService, Script, GameState, Character as ApiCharacter } from '../services/api';

interface ScriptManagementProps {
  script: Script;
  onScriptChange: (script: Script) => void;
  onGameStateChange: (gameState: GameState) => void;
}


interface Character {
  id: string;
  profile: string;
  initialMemory: string;
}

interface Scene {
  id: string;
  name: string;
  info: string; // 场景描述信息
  mode: 'v1' | 'v2' | 'v2_plus' | 'v2_prime' | 'v3';
  characters: Record<string, string>; // character motivations
  chains: string[];
  streams: Record<string, string[]>;
}

export const ScriptManagement: React.FC<ScriptManagementProps> = ({
  script,
  onScriptChange,
  onGameStateChange
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  
  // 脚本基本信息
  const [scriptName, setScriptName] = useState(script.id || '');
  const [playerName, setPlayerName] = useState(script.background?.player || '');
  const [backgroundNarrative, setBackgroundNarrative] = useState(script.background?.narrative || '');
  
  // 角色管理
  const [characters, setCharacters] = useState<Character[]>([]);
  
  // 场景管理
  const [scenes, setScenes] = useState<Scene[]>([]);

  // 初始化数据
  useEffect(() => {
    initializeData();
  }, []);

  const initializeData = () => {
    // 初始化角色数据
    if (script.background?.characters) {
      const chars = Object.entries(script.background.characters).map(([name, profile]) => ({
        id: name,
        profile: profile || '',
        initialMemory: script.background?.context?.[name] || ''
      }));
      setCharacters(chars);
    }

    // 初始化场景数据
    if (script.scenes) {
      const sceneList = Object.entries(script.scenes).map(([key, scene]) => ({
        id: key,
        name: scene.name || '',
        info: scene.info || '',
        mode: (scene.mode as any) || 'v1',
        characters: scene.characters || {},
        chains: scene.chain || [],
        streams: scene.stream || {}
      }));
      setScenes(sceneList);
    }
  };

  // 角色管理函数
  const addCharacter = () => {
    const newCharacter: Character = {
      id: '',
      profile: '',
      initialMemory: ''
    };
    setCharacters([...characters, newCharacter]);
  };

  const removeCharacter = (index: number) => {
    setCharacters(characters.filter((_, i) => i !== index));
  };

  const updateCharacter = (index: number, field: keyof Character, value: string) => {
    const updated = [...characters];
    updated[index] = { ...updated[index], [field]: value };
    setCharacters(updated);
  };

  // 场景管理函数
  const addScene = () => {
    const newScene: Scene = {
      id: `scene${scenes.length + 1}`,
      name: '',
      info: '',
      mode: 'v1',
      characters: {},
      chains: [],
      streams: {}
    };
    setScenes([...scenes, newScene]);
  };

  const removeScene = (index: number) => {
    setScenes(scenes.filter((_, i) => i !== index));
  };

  const updateScene = (index: number, field: keyof Scene, value: any) => {
    const updated = [...scenes];
    updated[index] = { ...updated[index], [field]: value };
    setScenes(updated);
  };

  // 添加场景角色动机
  const addSceneCharacter = (sceneIndex: number) => {
    const scene = scenes[sceneIndex];
    const allCharacterNames = characters.map(c => c.id).filter(name => !!name);
    if (allCharacterNames.length === 0) return;

    // 选择一个尚未加入该场景的角色，避免覆盖
    const existingNames = new Set(Object.keys(scene.characters || {}));
    const candidate = allCharacterNames.find(name => !existingNames.has(name));
    if (!candidate) return; // 所有可选角色都已添加时不再新增

    const updated = [...scenes];
    updated[sceneIndex] = {
      ...scene,
      characters: { ...(scene.characters || {}), [candidate]: '' }
    };
    setScenes(updated);
  };

  const removeSceneCharacter = (sceneIndex: number, characterName: string) => {
    const updated = [...scenes];
    const newCharacters = { ...updated[sceneIndex].characters };
    delete newCharacters[characterName];
    updated[sceneIndex] = {
      ...updated[sceneIndex],
      characters: newCharacters
    };
    setScenes(updated);
  };

  const updateSceneCharacter = (sceneIndex: number, characterName: string, motivation: string) => {
    const updated = [...scenes];
    updated[sceneIndex] = {
      ...updated[sceneIndex],
      characters: { ...updated[sceneIndex].characters, [characterName]: motivation }
    };
    setScenes(updated);
  };

  // 添加剧情链
  const addChain = (sceneIndex: number) => {
    const updated = [...scenes];
    updated[sceneIndex] = {
      ...updated[sceneIndex],
      chains: [...updated[sceneIndex].chains, '']
    };
    setScenes(updated);
  };

  const removeChain = (sceneIndex: number, chainIndex: number) => {
    const updated = [...scenes];
    updated[sceneIndex] = {
      ...updated[sceneIndex],
      chains: updated[sceneIndex].chains.filter((_, i) => i !== chainIndex)
    };
    setScenes(updated);
  };

  const updateChain = (sceneIndex: number, chainIndex: number, value: string) => {
    const updated = [...scenes];
    updated[sceneIndex] = {
      ...updated[sceneIndex],
      chains: updated[sceneIndex].chains.map((chain, i) => i === chainIndex ? value : chain)
    };
    setScenes(updated);
  };

  // 保存配置
  const handleSaveConfig = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      const scriptData = {
        id: scriptName,
        background_narrative: backgroundNarrative,
        player_name: playerName,
        characters: characters.map(char => ({
          id: char.id,
          profile: char.profile,
          initial_memory: char.initialMemory
        })),
        scenes: scenes.reduce((acc, scene, index) => {
          acc[`scene${index + 1}`] = {
            sceneName: scene.name,
            info: scene.info, // 使用info字段存储场景信息
            chains: scene.chains,
            streams: scene.streams,
            characters: scene.characters,
            mode: scene.mode
          };
          return acc;
        }, {} as Record<string, any>),
        storageMode: true
      };

      const response = await apiService.saveConfig(scriptData);
      if (response.success && response.data) {
        setMessage({ type: 'success', text: '脚本配置保存成功！' });
        // 更新父组件的脚本数据
        const updatedScript = {
          ...script,
          id: scriptName,
          background: {
            ...script.background,
            narrative: backgroundNarrative,
            player: playerName,
            characters: characters.reduce((acc, char) => {
              if (char.id) acc[char.id] = char.profile;
              return acc;
            }, {} as Record<string, string>),
            context: characters.reduce((acc, char) => {
              if (char.id) acc[char.id] = char.initialMemory;
              return acc;
            }, {} as Record<string, string>)
          },
          scenes: scenes.reduce((acc, scene, index) => {
            acc[`scene${index + 1}`] = {
              name: scene.name,
              info: scene.info,
              chain: scene.chains,
              streams: scene.streams,
              characters: scene.characters,
              mode: scene.mode
            };
            return acc;
          }, {} as Record<string, any>)
        };
        onScriptChange(updatedScript);
        
        // 更新gameState以刷新主页面
        const updatedGameState: GameState = {
          id: scriptName,
          scene_cnt: 1, // 设置为1，因为场景从scene1开始
          nc: [],
          characters: characters.reduce((acc, char) => {
            if (char.id) {
              acc[char.id] = {
                id: char.id,
                name: char.id,
                profile: char.profile,
                memory: char.initialMemory ? [char.initialMemory] : []
              };
            }
            return acc;
          }, {} as Record<string, ApiCharacter>),
          scenes: scenes.reduce((acc, scene, index) => {
            acc[`scene${index + 1}`] = {
              id: `scene${index + 1}`,
              name: scene.name,
              info: scene.info,
              mode: scene.mode,
              characters: scene.characters,
              chain: scene.chains,
              stream: scene.streams
            };
            return acc;
          }, {} as Record<string, any>),
          script: updatedScript
        };
        onGameStateChange(updatedGameState);
      } else {
        setMessage({ type: 'error', text: response.error || '保存失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '保存失败，请重试' });
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="space-y-6">
      {/* 消息提示 */}
      {message && (
        <Card className={`${message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              {message.type === 'success' ? (
                <CheckCircle className="w-5 h-5 text-green-600" />
              ) : (
                <AlertCircle className="w-5 h-5 text-red-600" />
              )}
              <span className={message.type === 'success' ? 'text-green-800' : 'text-red-800'}>
                {message.text}
              </span>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="space-y-6">

        {/* 脚本配置 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                脚本配置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">脚本名称</label>
                  <Input
                    value={scriptName || ''}
                    onChange={(e) => setScriptName(e.target.value)}
                    placeholder="请输入脚本名称..."
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">玩家名称</label>
                  <Input
                    value={playerName || ''}
                    onChange={(e) => setPlayerName(e.target.value)}
                    placeholder="请输入玩家名称..."
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">背景叙述</label>
                <Textarea
                  value={backgroundNarrative}
                  onChange={(e) => setBackgroundNarrative(e.target.value)}
                  placeholder="请输入背景叙述..."
                  rows={4}
                />
              </div>
            </CardContent>
          </Card>

          {/* 角色管理 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  角色管理
                </div>
                <Button onClick={addCharacter} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  添加角色
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground mb-3">
                小提示：请在此处添加本剧本的所有角色，并确保包含玩家名称。
              </p>
              <ScrollArea className="h-64">
                <div className="space-y-4">
                  {characters.map((character, index) => (
                    <div key={index} className="p-4 border rounded-lg space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">角色 {index + 1}</h4>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeCharacter(index)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-sm font-medium mb-1 block">角色名称</label>
                          <Input
                            value={character.id || ''}
                            onChange={(e) => updateCharacter(index, 'id', e.target.value)}
                            placeholder="角色名称"
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium mb-1 block">角色档案</label>
                          <Input
                            value={character.profile || ''}
                            onChange={(e) => updateCharacter(index, 'profile', e.target.value)}
                            placeholder="角色档案"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-1 block">初始记忆</label>
                        <Textarea
                          value={character.initialMemory}
                          onChange={(e) => updateCharacter(index, 'initialMemory', e.target.value)}
                          placeholder="角色的初始记忆..."
                          rows={2}
                        />
                      </div>
                    </div>
                  ))}
                  {characters.length === 0 && (
                    <div className="text-center text-muted-foreground py-8">
                      <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>暂无角色，点击"添加角色"开始创建</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* 场景管理 */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MapPin className="w-5 h-5" />
                  场景管理
                </div>
                <Button onClick={addScene} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  添加场景
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-4">
                  {scenes.map((scene, sceneIndex) => (
                    <div key={sceneIndex} className="p-4 border rounded-lg space-y-4">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">场景 {sceneIndex + 1}</h4>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => removeScene(sceneIndex)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-sm font-medium mb-1 block">场景名称</label>
                          <Input
                            value={scene.name || ''}
                            onChange={(e) => updateScene(sceneIndex, 'name', e.target.value)}
                            placeholder="场景名称"
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium mb-1 block">架构模式</label>
                          <Select
                            value={scene.mode}
                            onValueChange={(value: any) => updateScene(sceneIndex, 'mode', value)}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="v1">v1 - One-for-All</SelectItem>
                              <SelectItem value="v2">v2 - Director-Actor(single action)</SelectItem>
                              <SelectItem value="v2_plus">v2_plus - Director-Actor(multiple actions)</SelectItem>
                              <SelectItem value="v2_prime">v2_prime - Director-Global-Actor</SelectItem>
                              <SelectItem value="v3">v3 - Hybrid Architecture</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>

                      <div>
                        <label className="text-sm font-medium mb-1 block">场景信息</label>
                        <Textarea
                          value={scene.info}
                          onChange={(e) => updateScene(sceneIndex, 'info', e.target.value)}
                          placeholder="场景背景信息..."
                          rows={3}
                        />
                      </div>

                      {/* 角色动机 */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium">角色动机</label>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => addSceneCharacter(sceneIndex)}
                          >
                            <Plus className="w-4 h-4 mr-1" />
                            添加角色
                          </Button>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2">
                          小提示：请为该场景补充所有需要的角色（含玩家），并在需要时为他们填写角色动机。
                        </p>
                        <div className="space-y-2">
                          {Object.entries(scene.characters).map(([charName, motivation]) => (
                            <div key={charName} className="flex items-center gap-2">
                              <Select
                                value={charName}
                                onValueChange={(value) => {
                                  const newCharacters = { ...scene.characters };
                                  delete newCharacters[charName];
                                  newCharacters[value] = motivation;
                                  updateScene(sceneIndex, 'characters', newCharacters);
                                }}
                              >
                                <SelectTrigger className="w-32">
                                  <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                  {characters.map(char => (
                                    <SelectItem key={char.id} value={char.id}>
                                      {char.id}
                                    </SelectItem>
                                  ))}
                                </SelectContent>
                              </Select>
                              <Input
                                value={motivation || ''}
                                onChange={(e) => updateSceneCharacter(sceneIndex, charName, e.target.value)}
                                placeholder="角色动机..."
                                className="flex-1"
                              />
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => removeSceneCharacter(sceneIndex, charName)}
                                className="text-red-600"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* 剧情链 */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium">剧情链</label>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => addChain(sceneIndex)}
                          >
                            <Plus className="w-4 h-4 mr-1" />
                            添加剧情
                          </Button>
                        </div>
                        <div className="space-y-2">
                          {scene.chains.map((chain, chainIndex) => (
                            <div key={chainIndex} className="flex items-center gap-2">
                              <Input
                                value={chain || ''}
                                onChange={(e) => updateChain(sceneIndex, chainIndex, e.target.value)}
                                placeholder="剧情链内容..."
                                className="flex-1"
                              />
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => removeChain(sceneIndex, chainIndex)}
                                className="text-red-600"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                  {scenes.length === 0 && (
                    <div className="text-center text-muted-foreground py-8">
                      <MapPin className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>暂无场景，点击"添加场景"开始创建</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button 
              onClick={handleSaveConfig} 
              disabled={isLoading} 
              size="lg"
              className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700"
            >
              {isLoading ? (
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              ) : (
                <Settings className="w-5 h-5 mr-2" />
              )}
              保存设置
            </Button>
          </div>
      </div>
    </div>
  );
};