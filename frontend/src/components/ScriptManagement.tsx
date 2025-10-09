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
  info: string; // Scene description info
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
  
  // Script basic info
  const [scriptName, setScriptName] = useState(script.id || '');
  const [playerName, setPlayerName] = useState(script.background?.player || '');
  const [backgroundNarrative, setBackgroundNarrative] = useState(script.background?.narrative || '');
  
  // Character management
  const [characters, setCharacters] = useState<Character[]>([]);
  
  // Scene management
  const [scenes, setScenes] = useState<Scene[]>([]);

  // Initialize data
  useEffect(() => {
    initializeData();
  }, []);

  const initializeData = () => {
    // Initialize character data
    if (script.background?.characters) {
      const chars = Object.entries(script.background.characters).map(([name, profile]) => ({
        id: name,
        profile: profile || '',
        initialMemory: script.background?.context?.[name] || ''
      }));
      setCharacters(chars);
    }

    // Initialize scene data
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

  // Character management functions
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

  // Scene management functions
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

  // Add scene character motivation
  const addSceneCharacter = (sceneIndex: number) => {
    const scene = scenes[sceneIndex];
    const allCharacterNames = characters.map(c => c.id).filter(name => !!name);
    if (allCharacterNames.length === 0) return;

    // Select a character not yet added to this scene to avoid overwriting
    const existingNames = new Set(Object.keys(scene.characters || {}));
    const candidate = allCharacterNames.find(name => !existingNames.has(name));
    if (!candidate) return; // Don't add more when all available characters are already added

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

  // Add plot chain
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

  // Save configuration
  const handleSaveConfig = async () => {
    setIsLoading(true);
    setMessage(null);

    try {
      const scriptData = {
        id: scriptName || 'untitled-script',
        background_narrative: backgroundNarrative || '',
        player_name: playerName || 'Player',
        characters: characters.filter(char => char.id && char.id.trim()).map(char => ({
          id: char.id.trim(),
          profile: char.profile || '',
          initial_memory: char.initialMemory || ''
        })) || [],
        scenes: scenes.reduce((acc, scene, index) => {
          acc[`scene${index + 1}`] = {
            sceneName: scene.name || `Scene ${index + 1}`,
            sceneInfo: scene.info || '', // Use sceneInfo field to match backend expectation
            chains: Array.isArray(scene.chains) ? scene.chains
              .filter(chain => chain && typeof chain === 'string' && chain.trim())
              .map(chain => chain.trim())
              .filter(chain => chain.length > 0) : [],
            streams: scene.streams && typeof scene.streams === 'object' ? 
              Object.fromEntries(
                Object.entries(scene.streams).map(([key, value]) => [
                  key, 
                  Array.isArray(value) ? value.filter(item => item && typeof item === 'string' && item.trim()) : []
                ])
              ) : {},
            characters: scene.characters && typeof scene.characters === 'object' ? 
              Object.fromEntries(
                Object.entries(scene.characters).map(([key, value]) => [
                  key, 
                  value === null || value === undefined ? '' : value
                ])
              ) : {},
            mode: scene.mode || 'v1'
          };
          return acc;
        }, {} as Record<string, any>),
        storageMode: true
      };

      // 验证数据完整性
      const isValidData = (data: any): boolean => {
        try {
          const jsonString = JSON.stringify(data);
          // 检查是否有截断的字符串
          if (jsonString.includes('\\n') && !jsonString.endsWith('}')) {
            console.error('Data appears to be truncated');
            return false;
          }
          return true;
        } catch (e) {
          console.error('Invalid data detected:', e);
          return false;
        }
      };

      if (!isValidData(scriptData)) {
        setMessage({ type: 'error', text: 'Invalid data detected. Please check your input.' });
        return;
      }

      console.log('Sending script data:', JSON.stringify(scriptData, null, 2));
      const response = await apiService.saveConfig(scriptData);
      if (response.success && response.data) {
        setMessage({ type: 'success', text: 'Script configuration saved successfully!' });
        // Update parent component's script data
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
              stream: scene.streams,
              characters: scene.characters,
              mode: scene.mode
            };
            return acc;
          }, {} as Record<string, any>)
        };
        onScriptChange(updatedScript);
        
        // Update gameState to refresh main page
        const updatedGameState: GameState = {
          id: scriptName,
          scene_cnt: 1, // Set to 1 because scenes start from scene1
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
        console.error('Save failed:', response.error);
        setMessage({ type: 'error', text: response.error || 'Save failed' });
      }
    } catch (error) {
      console.error('Save error:', error);
      setMessage({ type: 'error', text: 'Save failed, please try again' });
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="space-y-6">
      {/* Message notifications */}
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

        {/* Script configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5" />
                Script Configuration
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Script Name</label>
                  <Input
                    value={scriptName || ''}
                    onChange={(e) => setScriptName(e.target.value)}
                    placeholder="Enter script name..."
                  />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Player Name</label>
                  <Input
                    value={playerName || ''}
                    onChange={(e) => setPlayerName(e.target.value)}
                    placeholder="Enter player name..."
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Background Narrative</label>
                <Textarea
                  value={backgroundNarrative}
                  onChange={(e) => setBackgroundNarrative(e.target.value)}
                  placeholder="Enter background narrative..."
                  rows={4}
                />
              </div>
            </CardContent>
          </Card>

          {/* Character management */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5" />
                  Character Management
                </div>
                <Button onClick={addCharacter} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Character
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground mb-3">
                Tip: Add all characters for this script here, including the player name.
              </p>
              <ScrollArea className="h-64">
                <div className="space-y-4">
                  {characters.map((character, index) => (
                    <div key={index} className="p-4 border rounded-lg space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Character {index + 1}</h4>
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
                          <label className="text-sm font-medium mb-1 block">Character Name</label>
                          <Input
                            value={character.id || ''}
                            onChange={(e) => updateCharacter(index, 'id', e.target.value)}
                            placeholder="Character name"
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium mb-1 block">Character Profile</label>
                          <Input
                            value={character.profile || ''}
                            onChange={(e) => updateCharacter(index, 'profile', e.target.value)}
                            placeholder="Character profile"
                          />
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium mb-1 block">Initial Memory</label>
                        <Textarea
                          value={character.initialMemory}
                          onChange={(e) => updateCharacter(index, 'initialMemory', e.target.value)}
                          placeholder="Character's initial memory..."
                          rows={2}
                        />
                      </div>
                    </div>
                  ))}
                  {characters.length === 0 && (
                    <div className="text-center text-muted-foreground py-8">
                      <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                      <p>No characters yet, click "Add Character" to start creating</p>
                    </div>
                  )}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Scene management */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <MapPin className="w-5 h-5" />
                  Scene Management
                </div>
                <Button onClick={addScene} size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Scene
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-96">
                <div className="space-y-4">
                  {scenes.map((scene, sceneIndex) => (
                    <div key={sceneIndex} className="p-4 border rounded-lg space-y-4">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">Scene {sceneIndex + 1}</h4>
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
                          <label className="text-sm font-medium mb-1 block">Scene Name</label>
                          <Input
                            value={scene.name || ''}
                            onChange={(e) => updateScene(sceneIndex, 'name', e.target.value)}
                            placeholder="Scene name"
                          />
                        </div>
                        <div>
                          <label className="text-sm font-medium mb-1 block">Architecture Mode</label>
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
                        <label className="text-sm font-medium mb-1 block">Scene Information</label>
                        <Textarea
                          value={scene.info}
                          onChange={(e) => updateScene(sceneIndex, 'info', e.target.value)}
                          placeholder="Scene background information..."
                          rows={3}
                        />
                      </div>

                      {/* Character motivations */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium">Character Motivations</label>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => addSceneCharacter(sceneIndex)}
                          >
                            <Plus className="w-4 h-4 mr-1" />
                            Add Character
                          </Button>
                        </div>
                        <p className="text-xs text-muted-foreground mb-2">
                          Tip: Add all required characters for this scene (including player) and fill in their motivations when needed.
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
                                placeholder="Character motivation..."
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

                      {/* Plot chains */}
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <label className="text-sm font-medium">Plot Chains</label>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => addChain(sceneIndex)}
                          >
                            <Plus className="w-4 h-4 mr-1" />
                            Add Plot
                          </Button>
                        </div>
                        <div className="space-y-2">
                          {scene.chains.map((chain, chainIndex) => (
                            <div key={chainIndex} className="flex items-center gap-2">
                              <Input
                                value={chain || ''}
                                onChange={(e) => updateChain(sceneIndex, chainIndex, e.target.value)}
                                placeholder="Plot chain content..."
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
                      <p>No scenes yet, click "Add Scene" to start creating</p>
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
              Save Settings
            </Button>
          </div>
      </div>
    </div>
  );
};