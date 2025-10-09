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
  const [worldRecords, setWorldRecords] = useState<any>(null);
  const [systemFeedbacks, setSystemFeedbacks] = useState<any>(null);
  const [characterInfo, setCharacterInfo] = useState<any>(null);
  const [selectedCharacterName, setSelectedCharacterName] = useState<string>('');
  const [availableCharacters, setAvailableCharacters] = useState<string[]>([]);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [avatarRefreshKey, setAvatarRefreshKey] = useState<number>(Date.now());
  const [pendingUploadCharacter, setPendingUploadCharacter] = useState<string | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);

  // Initialize
  useEffect(() => {
    loadAvailableCharacters();
  }, []);

  // Reload character list when gameState changes
  useEffect(() => {
    loadAvailableCharacters();
  }, [gameState]);

  // Load character info when character is selected
  useEffect(() => {
    if (selectedCharacterName) {
      loadCharacterInfo(selectedCharacterName);
    }
  }, [selectedCharacterName]);

  // Auto refresh when switching to "system feedback" or "records" tab
  useEffect(() => {
    if (activeTab === 'system') {
      loadSystemFeedbacks();
    } else if (activeTab === 'records') {
      loadWorldRecords();
    }
  }, [activeTab]);

  // Auto refresh when gameState changes and currently in "system feedback/records"
  useEffect(() => {
    if (activeTab === 'system') {
      loadSystemFeedbacks();
    } else if (activeTab === 'records') {
      loadWorldRecords();
    }
  }, [gameState]);


  // Load world records
  const loadWorldRecords = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getWorldRecords();
      if (response.success && response.data) {
        setWorldRecords(response.data);
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to load world records' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load world records, please try again' });
    } finally {
      setIsLoading(false);
    }
  };

  // Load system feedbacks
  const loadSystemFeedbacks = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getSystemFeedbacks();
      if (response.success && response.data) {
        setSystemFeedbacks(response.data);
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to load system feedbacks' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load system feedbacks, please try again' });
    } finally {
      setIsLoading(false);
    }
  };

  // Load character info
  const loadCharacterInfo = async (characterName: string) => {
    if (!characterName) return;
    
    setIsLoading(true);
    try {
      const response = await apiService.getCharacterInfo(characterName);
      if (response.success && response.data) {
        setCharacterInfo(response.data);
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to load character info' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load character info, please try again' });
    } finally {
      setIsLoading(false);
    }
  };

  // Get available character list
  const loadAvailableCharacters = async () => {
    try {
      const response = await apiService.getCharacters();
      if (response.success && response.data) {
        // Filter out null, undefined and empty strings
        const validCharacters = (response.data.characters || [])
          .filter(char => char && char !== 'null' && char.trim() !== '');
        setAvailableCharacters(validCharacters);
      }
    } catch (error) {
      console.error('Failed to load characters:', error);
      setAvailableCharacters([]);
    }
  };

  // Handle avatar double click: open file selection
  const handleAvatarDoubleClick = (charName: string) => {
    setPendingUploadCharacter(charName);
    fileInputRef.current?.click();
  };

  // Handle file selection and upload avatar
  const handleAvatarFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !pendingUploadCharacter) return;
    try {
      const resp = await apiService.uploadCharacterAvatar(file, pendingUploadCharacter);
      if (resp.success) {
        // Refresh right side character info
        if (selectedCharacterName === pendingUploadCharacter) {
          await loadCharacterInfo(pendingUploadCharacter);
        }
        // Force avatar cache refresh
        setAvatarRefreshKey(Date.now());
        setMessage({ type: 'success', text: 'Avatar uploaded successfully!' });
      } else {
        setMessage({ type: 'error', text: resp.error || 'Avatar upload failed' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Avatar upload failed, please try again' });
    } finally {
      // Clear selection to avoid same file not triggering change again
      if (fileInputRef.current) fileInputRef.current.value = '';
      setPendingUploadCharacter(null);
    }
  };

  // Export records
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
      setMessage({ type: 'success', text: 'Records exported successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Export failed, please try again' });
    }
  };

  // Format script content: mark current scene and completed plot chains based on gameState.scene_cnt and gameState.nc
  const formatScriptContent = (scriptData: any, meta?: { scene_cnt?: number; nc?: Array<[string, boolean]> }) => {
    if (!scriptData) return 'No script information';
    
    let content = `<div class="space-y-2">`;
    content += `<div><strong>Script Name:</strong> ${scriptData.id || 'Unnamed'}</div>`;
    content += `<div><strong>Player Name:</strong> ${scriptData.background?.player || 'Not set'}</div>`;
    content += `<div><strong>Characters and Profiles:</strong></div>`;
    
    if (scriptData.background?.characters) {
      Object.entries(scriptData.background.characters).forEach(([name, profile]) => {
        content += `<div class="ml-4">${name}: ${profile || 'No profile'}</div>`;
      });
    }
    
    content += `<div><strong>Background Narrative:</strong> ${scriptData.background?.narrative || 'No background narrative'}</div>`;
    content += `<div><strong>Character Initial Memory:</strong></div>`;
    
    if (scriptData.background?.context) {
      Object.entries(scriptData.background.context).forEach(([name, memory]) => {
        content += `<div class="ml-4">${name}: ${memory || 'No memory'}</div>`;
      });
    } else {
      content += `<div class="ml-4">No initial memory</div>`;
    }
    
    if (scriptData.scenes) {
      Object.entries(scriptData.scenes).forEach(([sceneKey, scene]: [string, any]) => {
        const isCurrentScene = !!meta?.scene_cnt && sceneKey === `scene${meta.scene_cnt}`;
        const sceneClass = isCurrentScene ? 'bg-yellow-100 p-2 rounded font-bold' : '';
        
        content += `<div class="mt-4 ${sceneClass}">`;
        content += `<div><strong>${sceneKey}:</strong></div>`;
        content += `<div class="ml-4"><strong>Scene Name:</strong> ${scene.name || 'No name'}</div>`;
        content += `<div class="ml-4"><strong>Scene Info:</strong> ${scene.info || 'No info'}</div>`;
        content += `<div class="ml-4"><strong>Architecture:</strong> ${scene.mode || 'v1'}</div>`;
        content += `<div class="ml-4"><strong>Character Motivations:</strong></div>`;
        
        if (scene.characters) {
          Object.entries(scene.characters).forEach(([name, motivation]) => {
            content += `<div class="ml-8">${name}: ${motivation || 'No motivation'}</div>`;
          });
        }
        
        content += `<div class="ml-4"><strong>Plot Chains:</strong></div>`;
        if (scene.chain && scene.chain.length > 0) {
          scene.chain.forEach((item: string) => {
            const isCompleted = meta?.nc?.some(([entry, status]: [string, boolean]) => entry === item && status);
            const itemClass = isCompleted ? 'text-green-600 font-bold italic' : 'text-gray-500 italic';
            content += `<div class="ml-8 ${itemClass}">${item}</div>`;
          });
        } else {
          content += `<div class="ml-8">No plot chains</div>`;
        }
        content += `</div>`;
      });
    }
    
    content += `</div>`;
    return content;
  };

  return (
    <div className="h-full max-h-[calc(100vh-200px)] overflow-hidden flex flex-col">
      {/* Message notifications */}
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
            Current Script
          </TabsTrigger>
          <TabsTrigger value="characters" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Character Info
          </TabsTrigger>
          <TabsTrigger value="system" className="flex items-center gap-2">
            <Brain className="w-4 h-4" />
            System Feedback
          </TabsTrigger>
          <TabsTrigger value="records" className="flex items-center gap-2">
            <Database className="w-4 h-4" />
            Records
          </TabsTrigger>
        </TabsList>

        {/* Current script */}
        <TabsContent value="script" className="h-[calc(100%-60px)]">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex-shrink-0">
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-5 h-5" />
                Current Script
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
                      __html: formatScriptContent(gameState.script, { scene_cnt: gameState.scene_cnt, nc: gameState.nc }) 
                    }}
                  />
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Character info */}
        <TabsContent value="characters" className="h-[calc(100%-60px)]">
          <Card className="h-full flex flex-col">
            <CardHeader className="flex-shrink-0">
              <CardTitle className="flex items-center gap-2">
                <Users className="w-5 h-5" />
                Character Info
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto">
              <div className="flex h-full">
                {/* Left side character list */}
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
                          src={`/assets/${char}.jpg?${avatarRefreshKey}`}
                          alt={char}
                          className="w-8 h-8 rounded-full object-cover"
                          onDoubleClick={(e) => {
                            e.stopPropagation();
                            handleAvatarDoubleClick(char);
                          }}
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = '/assets/default_agent.jpg';
                          }}
                        />
                        <span className="text-sm font-medium whitespace-nowrap">{char}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Right side character details */}
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
                        <p>Select a character to view details</p>
                      </div>
                    )}
                  </ScrollArea>
                </div>
              </div>
            {/* Hidden file input for avatar upload */}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleAvatarFileChange}
            />
            </CardContent>
          </Card>
        </TabsContent>

        {/* System feedback */}
        <TabsContent value="system" className="h-[calc(100%-60px)]">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="w-5 h-5" />
                System Feedback
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
                        <p>No system feedback</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    <Button onClick={loadSystemFeedbacks} variant="outline">
                      Load System Feedback
                    </Button>
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Records */}
        <TabsContent value="records" className="h-[calc(100%-60px)]">
          <Card className="h-full">
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="w-5 h-5" />
                  Records
                </div>
                <Button onClick={handleExportRecords} size="sm" variant="outline">
                  <Download className="w-4 h-4 mr-2" />
                  Export Records
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
                        <p>No records</p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    <Button onClick={loadWorldRecords} variant="outline">
                      Load World Records
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


