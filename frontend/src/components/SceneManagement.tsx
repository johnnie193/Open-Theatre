import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Separator } from './ui/separator';
import { Plus, X, Trash2, Settings, Users, BookOpen, Zap } from 'lucide-react';
import { Scene, Character } from '../services/api';

interface SceneManagementProps {
  scenes: Record<string, Scene>;
  characters: Character[];
  onScenesChange: (scenes: Record<string, Scene>) => void;
  onCharactersChange: (characters: Character[]) => void;
}

interface SceneMemory {
  characterId: string;
  motivation: string;
}

interface PlotChain {
  id: string;
  content: string;
  details: string[];
}

export const SceneManagement: React.FC<SceneManagementProps> = ({
  scenes,
  characters,
  onScenesChange,
  onCharactersChange
}) => {
  const [isAddingScene, setIsAddingScene] = useState(false);
  const [newScene, setNewScene] = useState({
    name: '',
    info: '',
    mode: 'v1',
    characters: {} as Record<string, string>,
    chain: [] as PlotChain[]
  });
  const [editingScene, setEditingScene] = useState<string | null>(null);

  // 添加新场景
  const handleAddScene = () => {
    if (!newScene.name.trim()) return;

    const sceneId = `scene${Object.keys(scenes).length + 1}`;
    const scene: Scene = {
      id: sceneId,
      name: newScene.name.trim(),
      info: newScene.info.trim(),
      mode: newScene.mode,
      characters: newScene.characters,
      chain: newScene.chain.map(c => c.content)
    };

    onScenesChange({ ...scenes, [sceneId]: scene });
    setNewScene({
      name: '',
      info: '',
      mode: 'v1',
      characters: {},
      chain: []
    });
    setIsAddingScene(false);
  };

  // 删除场景
  const handleDeleteScene = (sceneId: string) => {
    const newScenes = { ...scenes };
    delete newScenes[sceneId];
    onScenesChange(newScenes);
  };

  // 更新场景
  const handleUpdateScene = (sceneId: string, updates: Partial<Scene>) => {
    onScenesChange({
      ...scenes,
      [sceneId]: { ...scenes[sceneId], ...updates }
    });
  };

  // 添加角色动机
  const handleAddCharacterMotivation = (sceneId: string) => {
    const scene = scenes[sceneId];
    const newCharacterId = `character_${Date.now()}`;
    const updatedCharacters = {
      ...scene.characters,
      [newCharacterId]: ''
    };
    handleUpdateScene(sceneId, { characters: updatedCharacters });
  };

  // 更新角色动机
  const handleUpdateCharacterMotivation = (sceneId: string, characterId: string, motivation: string) => {
    const scene = scenes[sceneId];
    const updatedCharacters = {
      ...scene.characters,
      [characterId]: motivation
    };
    handleUpdateScene(sceneId, { characters: updatedCharacters });
  };

  // 删除角色动机
  const handleDeleteCharacterMotivation = (sceneId: string, characterId: string) => {
    const scene = scenes[sceneId];
    const updatedCharacters = { ...scene.characters };
    delete updatedCharacters[characterId];
    handleUpdateScene(sceneId, { characters: updatedCharacters });
  };

  // 添加剧情链
  const handleAddPlotChain = (sceneId: string) => {
    const scene = scenes[sceneId];
    const newChain: PlotChain = {
      id: `chain_${Date.now()}`,
      content: '',
      details: []
    };
    const updatedChain = [...scene.chain, newChain.content];
    handleUpdateScene(sceneId, { chain: updatedChain });
  };

  // 更新剧情链
  const handleUpdatePlotChain = (sceneId: string, chainIndex: number, content: string) => {
    const scene = scenes[sceneId];
    const updatedChain = [...scene.chain];
    updatedChain[chainIndex] = content;
    handleUpdateScene(sceneId, { chain: updatedChain });
  };

  // 删除剧情链
  const handleDeletePlotChain = (sceneId: string, chainIndex: number) => {
    const scene = scenes[sceneId];
    const updatedChain = scene.chain.filter((_, index) => index !== chainIndex);
    handleUpdateScene(sceneId, { chain: updatedChain });
  };

  const sceneEntries = Object.entries(scenes);

  return (
    <div className="space-y-6">
      {/* 添加场景按钮 */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">场景管理</h2>
        <Button
          onClick={() => setIsAddingScene(true)}
          className="flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          添加场景
        </Button>
      </div>

      {/* 添加场景表单 */}
      {isAddingScene && (
        <Card>
          <CardHeader>
            <CardTitle>添加新场景</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">场景名称</label>
                <Input
                  placeholder="请输入场景名称"
                  value={newScene.name}
                  onChange={(e) => setNewScene(prev => ({ ...prev, name: e.target.value }))}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">架构模式</label>
                <Select
                  value={newScene.mode}
                  onValueChange={(value) => setNewScene(prev => ({ ...prev, mode: value }))}
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
              <label className="text-sm font-medium mb-2 block">场景信息</label>
              <Textarea
                placeholder="请输入场景背景信息"
                value={newScene.info}
                onChange={(e) => setNewScene(prev => ({ ...prev, info: e.target.value }))}
                rows={4}
              />
            </div>

            <div className="flex gap-2">
              <Button onClick={handleAddScene}>添加场景</Button>
              <Button 
                variant="outline" 
                onClick={() => setIsAddingScene(false)}
              >
                取消
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 场景列表 */}
      <div className="space-y-4">
        {sceneEntries.map(([sceneId, scene]) => (
          <Card key={sceneId}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="w-5 h-5" />
                  {scene.name || sceneId}
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant="outline">{scene.mode}</Badge>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setEditingScene(editingScene === sceneId ? null : sceneId)}
                  >
                    <Settings className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDeleteScene(sceneId)}
                    className="text-destructive hover:bg-destructive/10"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            
            <CardContent>
              <div className="space-y-4">
                {/* 场景信息 */}
                <div>
                  <h4 className="font-medium mb-2">场景信息</h4>
                  <p className="text-sm text-muted-foreground">
                    {scene.info || '暂无场景信息'}
                  </p>
                </div>

                {/* 角色动机 */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium flex items-center gap-2">
                      <Users className="w-4 h-4" />
                      角色动机
                    </h4>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleAddCharacterMotivation(sceneId)}
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                  <p className="text-xs text-muted-foreground mb-2">
                    小提示：请添加该场景所需的所有角色（包括玩家）。如有需要，请为他们填写对应的角色动机。
                  </p>
                  <div className="space-y-2">
                    {Object.entries(scene.characters).map(([characterId, motivation]) => (
                      <div key={characterId} className="flex items-center gap-2">
                        <Select
                          value={characterId}
                          onValueChange={(value) => {
                            const newCharacters = { ...scene.characters };
                            delete newCharacters[characterId];
                            newCharacters[value] = motivation;
                            handleUpdateScene(sceneId, { characters: newCharacters });
                          }}
                        >
                          <SelectTrigger className="w-48">
                            <SelectValue placeholder="选择角色" />
                          </SelectTrigger>
                          <SelectContent>
                            {characters.map((char) => (
                              <SelectItem key={char.id} value={char.name}>
                                {char.name}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                        <Textarea
                          placeholder="角色动机"
                          value={motivation}
                          onChange={(e) => handleUpdateCharacterMotivation(sceneId, characterId, e.target.value)}
                          rows={2}
                          className="flex-1"
                        />
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeleteCharacterMotivation(sceneId, characterId)}
                          className="text-destructive hover:bg-destructive/10"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 剧情链 */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium flex items-center gap-2">
                      <Zap className="w-4 h-4" />
                      剧情链
                    </h4>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleAddPlotChain(sceneId)}
                    >
                      <Plus className="w-4 h-4" />
                    </Button>
                  </div>
                  <div className="space-y-2">
                    {scene.chain.map((chainContent, index) => (
                      <div key={index} className="flex items-center gap-2">
                        <Textarea
                          placeholder="请输入剧情链内容"
                          value={chainContent}
                          onChange={(e) => handleUpdatePlotChain(sceneId, index, e.target.value)}
                          rows={2}
                          className="flex-1"
                        />
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => handleDeletePlotChain(sceneId, index)}
                          className="text-destructive hover:bg-destructive/10"
                        >
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {sceneEntries.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          <BookOpen className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>还没有场景，点击上方按钮添加第一个场景</p>
        </div>
      )}
    </div>
  );
};


