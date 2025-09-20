import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { Button } from './ui/button';
import { 
  FileText, 
  Users, 
  Brain, 
  Database,
  Download,
  Loader2,
  AlertCircle,
  CheckCircle,
  Clock,
  HardDrive
} from 'lucide-react';
import { apiService, GameState } from '../services/api';

interface InfoPanelsProps {
  gameState: GameState;
}

export const InfoPanels: React.FC<InfoPanelsProps> = ({
  gameState
}) => {
  const [activeTab, setActiveTab] = useState('script');
  const [isLoading, setIsLoading] = useState(false);
  const [scriptInfo] = useState<any>(null);
  const [worldRecords, setWorldRecords] = useState<any>(null);
  const [systemFeedbacks, setSystemFeedbacks] = useState<any>(null);
  const [characterInfo, setCharacterInfo] = useState<any>(null);
  const [selectedCharacterName, setSelectedCharacterName] = useState<string>('');
  const [availableCharacters, setAvailableCharacters] = useState<string[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 初始化
  useEffect(() => {
    loadAvailableCharacters();
  }, []);

  // 当gameState变化时重新加载角色列表
  useEffect(() => {
    loadAvailableCharacters();
  }, [gameState]);

  // 当选择角色时加载角色信息
  useEffect(() => {
    if (selectedCharacterName) {
      loadCharacterInfo(selectedCharacterName);
    }
  }, [selectedCharacterName]);


  // 加载世界记录
  const loadWorldRecords = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getWorldRecords();
      if (response.success && response.data) {
        setWorldRecords(response.data);
      } else {
        setMessage({ type: 'error', text: response.error || '加载世界记录失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '加载世界记录失败，请重试' });
    } finally {
      setIsLoading(false);
    }
  };

  // 加载系统反馈
  const loadSystemFeedbacks = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getSystemFeedbacks();
      if (response.success && response.data) {
        setSystemFeedbacks(response.data);
      } else {
        setMessage({ type: 'error', text: response.error || '加载系统反馈失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '加载系统反馈失败，请重试' });
    } finally {
      setIsLoading(false);
    }
  };

  // 加载角色信息
  const loadCharacterInfo = async (characterName: string) => {
    if (!characterName) return;
    
    setIsLoading(true);
    try {
      const response = await apiService.getCharacterInfo(characterName);
      if (response.success && response.data) {
        setCharacterInfo(response.data);
      } else {
        setMessage({ type: 'error', text: response.error || '加载角色信息失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '加载角色信息失败，请重试' });
    } finally {
      setIsLoading(false);
    }
  };

  // 获取可用角色列表
  const loadAvailableCharacters = async () => {
    try {
      const response = await apiService.getCharacters();
      if (response.success && response.data) {
        // 过滤掉null、undefined和空字符串
        const validCharacters = (response.data.characters || [])
          .filter(char => char && char !== 'null' && char.trim() !== '');
        setAvailableCharacters(validCharacters);
      }
    } catch (error) {
      console.error('Failed to load characters:', error);
      setAvailableCharacters([]);
    }
  };

  // 导出记录
  const handleExportRecords = async () => {
    try {
      const blob = await apiService.exportRecords();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `drama_records_${new Date().toISOString().split('T')[0]}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setMessage({ type: 'success', text: '记录导出成功！' });
    } catch (error) {
      setMessage({ type: 'error', text: '导出失败，请重试' });
    }
  };

  // 格式化脚本内容
  const formatScriptContent = (data: any) => {
    if (!data) return '暂无脚本信息';
    
    let content = `<div class="space-y-2">`;
    content += `<div><strong>脚本名称：</strong> ${data.id || '未命名'}</div>`;
    content += `<div><strong>玩家名称：</strong> ${data.background?.player || '未设置'}</div>`;
    content += `<div><strong>角色及其档案：</strong></div>`;
    
    if (data.background?.characters) {
      Object.entries(data.background.characters).forEach(([name, profile]) => {
        content += `<div class="ml-4">${name}: ${profile || '无档案'}</div>`;
      });
    }
    
    content += `<div><strong>背景叙述：</strong> ${data.background?.narrative || '无背景叙述'}</div>`;
    content += `<div><strong>角色初始记忆：</strong></div>`;
    
    if (data.background?.context) {
      Object.entries(data.background.context).forEach(([name, memory]) => {
        content += `<div class="ml-4">${name}: ${memory || '无记忆'}</div>`;
      });
    } else {
      content += `<div class="ml-4">无初始记忆</div>`;
    }
    
    if (data.scenes) {
      Object.entries(data.scenes).forEach(([sceneKey, scene]: [string, any]) => {
        const isCurrentScene = sceneKey === `scene${data.scene_cnt}`;
        const sceneClass = isCurrentScene ? 'bg-yellow-100 p-2 rounded font-bold' : '';
        
        content += `<div class="mt-4 ${sceneClass}">`;
        content += `<div><strong>${sceneKey}:</strong></div>`;
        content += `<div class="ml-4"><strong>场景名称：</strong> ${scene.name || '无名称'}</div>`;
        content += `<div class="ml-4"><strong>场景信息：</strong> ${scene.info || '无信息'}</div>`;
        content += `<div class="ml-4"><strong>架构：</strong> ${scene.mode || 'v1'}</div>`;
        content += `<div class="ml-4"><strong>角色动机：</strong></div>`;
        
        if (scene.characters) {
          Object.entries(scene.characters).forEach(([name, motivation]) => {
            content += `<div class="ml-8">${name}: ${motivation || '无动机'}</div>`;
          });
        }
        
        content += `<div class="ml-4"><strong>剧情链：</strong></div>`;
        if (scene.chain && scene.chain.length > 0) {
          scene.chain.forEach((item: string) => {
            const isCompleted = data.nc?.some(([entry, status]: [string, boolean]) => entry === item && status);
            const itemClass = isCompleted ? 'text-green-600 font-bold italic' : 'text-gray-500 italic';
            content += `<div class="ml-8 ${itemClass}">${item}</div>`;
          });
        } else {
          content += `<div class="ml-8">无剧情链</div>`;
        }
        content += `</div>`;
      });
    }
    
    content += `</div>`;
    return content;
  };

  return (
    <div className="h-full max-h-[calc(100vh-200px)] overflow-hidden flex flex-col">
      {/* 消息提示 */}
      {message && (
        <Card className={`mb-4 ${message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
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

      <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="script" className="flex items-center gap-2">
            <FileText className="w-4 h-4" />
            当前脚本
          </TabsTrigger>
          <TabsTrigger value="characters" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            角色信息
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            系统反馈
          </TabsTrigger>
          <TabsTrigger value="records" className="flex items-center gap-2">
            <Database className="w-4 h-4" />
            记录
          </TabsTrigger>
        </TabsList>

        {/* 当前脚本 */}
        <TabsContent value="script" className="h-[calc(100%-60px)]">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex-shrink-0">
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                当前脚本
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-4">
              <ScrollArea className="h-full">
                {isLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <Loader2 className="w-6 h-6 animate-spin" />
                  </div>
                ) : (
                  <div 
                    className="text-sm space-y-2"
                    dangerouslySetInnerHTML={{ 
                      __html: formatScriptContent(scriptInfo || gameState.script) 
                    }}
                  />
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 角色信息 */}
        <TabsContent value="characters" className="h-[calc(100%-60px)]">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex-shrink-0">
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                角色信息
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto">
              <div className="flex h-full">
                {/* 左侧角色列表 */}
                <div className="w-2/5 border-r pr-4">
                  <div className="space-y-2">
                    {availableCharacters.map((char) => (
                      <div
                        key={char}
                        className={`flex items-center gap-3 p-2 rounded-lg cursor-pointer transition-colors ${
                          selectedCharacterName === char 
                            ? 'bg-blue-100 dark:bg-blue-900/20' 
                            : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                        }`}
                        onClick={() => setSelectedCharacterName(char)}
                      >
                        <img
                          src={`/assets/${char}.jpg`}
                          alt={char}
                          className="w-8 h-8 rounded-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/assets/default_agent.jpg';
                          }}
                        />
                        <span className="text-sm font-medium whitespace-nowrap">{char}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* 右侧角色详细信息 */}
                <div className="flex-1 pl-4 min-w-0">
                  <ScrollArea className="h-full">
                    {isLoading ? (
                      <div className="flex items-center justify-center py-8">
                        <Loader2 className="w-6 h-6 animate-spin" />
                      </div>
                    ) : characterInfo ? (
                      <div className="space-y-4">
                        <div>
                          <h3 className="text-lg font-bold mb-2">{selectedCharacterName}</h3>
                          <h4 className="font-semibold mb-2">Profile</h4>
                          <p className="text-sm text-muted-foreground">{characterInfo.profile}</p>
                        </div>
                        
                        {characterInfo.memory && characterInfo.memory.length > 0 && (
                          <div>
                            <h4 className="font-semibold mb-2 flex items-center gap-2">
                              <Clock className="w-4 h-4" />
                              Chronological Memory
                            </h4>
                            <div className="space-y-1">
                              {characterInfo.memory.map((memory: string, index: number) => (
                                <p key={index} className="text-sm text-muted-foreground">{memory}</p>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {characterInfo.chunks && characterInfo.chunks.length > 0 && (
                          <div>
                            <h4 className="font-semibold mb-2 flex items-center gap-2">
                              <HardDrive className="w-4 h-4" />
                              System Chunks
                            </h4>
                            <div className="space-y-1">
                              {characterInfo.chunks.map((chunk: string, index: number) => (
                                <li key={index} className="text-sm text-muted-foreground">{chunk}</li>
                              ))}
                            </div>
                          </div>
                        )}

                        {characterInfo.retrieved && characterInfo.retrieved.length > 0 && (
                          <div>
                            <h4 className="font-semibold mb-2">System Last Retrieved Chunks</h4>
                            <div className="space-y-1">
                              {characterInfo.retrieved.map((retrieve: any, index: number) => (
                                <li key={index} className="text-sm text-muted-foreground">
                                  {retrieve.Info}
                                </li>
                              ))}
                            </div>
                          </div>
                        )}

                        {characterInfo.prompts && characterInfo.prompts.length > 0 && (
                          <div>
                            <h4 className="font-semibold mb-2">React</h4>
                            <div className="space-y-2">
                              <div className="text-sm">
                                <pre className="whitespace-pre-wrap bg-muted p-2 rounded text-xs">
                                  {JSON.stringify(characterInfo.prompts[0], null, 2)}
                                </pre>
                              </div>
                              <div>
                                <b className="text-sm">Prompt</b>
                                <pre className="text-xs whitespace-pre-wrap bg-muted p-2 rounded mt-1">
                                  {characterInfo.prompts[1]}
                                </pre>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center text-muted-foreground py-8">
                        <Users className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>选择一个角色查看详细信息</p>
                      </div>
                    )}
                  </ScrollArea>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 系统反馈 */}
        <TabsContent value="system" className="h-[calc(100%-60px)]">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5" />
                系统反馈
              </CardTitle>
            </CardHeader>
            <CardContent className="h-[calc(100%-80px)]">
              <ScrollArea className="h-full">
                {isLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <Loader2 className="w-6 h-6 animate-spin" />
                  </div>
                ) : systemFeedbacks ? (
                  <div className="space-y-4">
                    <h3 className="font-semibold">System Feedbacks</h3>
                    {systemFeedbacks.dramallm && systemFeedbacks.dramallm.length > 0 ? (
                      <div className="space-y-4">
                        {(() => {
                          const items = [];
                          for (let i = 0; i < systemFeedbacks.dramallm.length; i++) {
                            const item = systemFeedbacks.dramallm[i];
                            if (typeof item === 'string' && ['v1', 'v2', 'v2_plus', 'v2_prime'].includes(item)) {
                              const version = item;
                              const config = systemFeedbacks.dramallm[i + 1];
                              const prompt = systemFeedbacks.dramallm[i + 2];
                              
                              items.push(
                                <div key={i} className="space-y-2">
                                  <b className="text-sm font-semibold">{version}</b>
                                  <div className="text-sm">
                                    <pre className="whitespace-pre-wrap bg-muted p-2 rounded text-xs">
                                      {JSON.stringify(config, null, 2)}
                                    </pre>
                                  </div>
                                  <div>
                                    <b className="text-sm">Prompt</b>
                                    <pre className="text-xs whitespace-pre-wrap bg-muted p-2 rounded mt-1">
                                      {prompt}
                                    </pre>
                                  </div>
                                </div>
                              );
                              i += 2; // Skip the next two items as they're config and prompt
                            }
                          }
                          return items;
                        })()}
                      </div>
                    ) : (
                      <div className="text-center text-muted-foreground py-8">
                        <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>暂无系统反馈</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    <Button onClick={loadSystemFeedbacks} variant="outline">
                      加载系统反馈
                    </Button>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 记录 */}
        <TabsContent value="records" className="h-[calc(100%-60px)]">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  记录
                </div>
                <Button onClick={handleExportRecords} size="sm" variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  导出记录
                </Button>
              </CardTitle>
            </CardHeader>
            <CardContent className="h-[calc(100%-80px)]">
              <ScrollArea className="h-full">
                {isLoading ? (
                  <div className="flex items-center justify-center h-32">
                    <Loader2 className="w-6 h-6 animate-spin" />
                  </div>
                ) : worldRecords ? (
                  <div className="space-y-4">
                    <h3 className="font-semibold">Records</h3>
                    {worldRecords.allmemory && Object.keys(worldRecords.allmemory).length > 0 ? (
                      <div className="space-y-4">
                        {Object.entries(worldRecords.allmemory).map(([scene, records]) => (
                          <div key={scene}>
                            <h4 className="font-semibold mb-2">{scene}</h4>
                            <ul className="space-y-1">
                              {(records as string[]).map((record, index) => (
                                <li key={index} className="text-sm text-muted-foreground">
                                  {record}
                                </li>
                              ))}
                            </ul>
                          </div>
                        ))}
                      </div>
                    ) : null}
                    
                    {worldRecords.chunks && worldRecords.chunks.length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-2">Chunks</h3>
                        <ul className="space-y-1">
                          {worldRecords.chunks.map((chunk: string, index: number) => (
                            <li key={index} className="text-sm text-muted-foreground">
                              {chunk}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {worldRecords.retrieved && worldRecords.retrieved.length > 0 && (
                      <div>
                        <h3 className="font-semibold mb-2">Last Retrieved Chunks</h3>
                        <ul className="space-y-1">
                          {worldRecords.retrieved.map((retrieve: any, index: number) => (
                            <li key={index} className="text-sm text-muted-foreground">
                              {retrieve.Info}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {(!worldRecords.allmemory || Object.keys(worldRecords.allmemory).length === 0) && 
                     (!worldRecords.chunks || worldRecords.chunks.length === 0) && 
                     (!worldRecords.retrieved || worldRecords.retrieved.length === 0) && (
                      <div className="text-center text-muted-foreground py-8">
                        <Database className="w-12 h-12 mx-auto mb-4 opacity-50" />
                        <p>暂无记录</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    <Button onClick={loadWorldRecords} variant="outline">
                      加载世界记录
                    </Button>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};


