import React, { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Plus, X, Upload, User, Brain, Clock } from 'lucide-react';
import { Character } from '../services/api';
import { apiService } from '../services/api';

interface CharacterManagementProps {
  characters: Character[];
  onCharactersChange: (characters: Character[]) => void;
  onCharacterSelect: (character: Character) => void;
  selectedCharacter?: Character;
}

export const CharacterManagement: React.FC<CharacterManagementProps> = ({
  characters,
  onCharactersChange,
  onCharacterSelect,
  selectedCharacter
}) => {
  const [isAddingCharacter, setIsAddingCharacter] = useState(false);
  const [newCharacter, setNewCharacter] = useState({ name: '', profile: '', memory: '' });
  const [characterInfo, setCharacterInfo] = useState<{
    profile: string;
    memory: string[];
    chunks: string[];
    retrieved: Array<{ Info: string }>;
    prompts: any[];
  } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Add new character
  const handleAddCharacter = () => {
    if (!newCharacter.name.trim()) return;

    const character: Character = {
      id: Date.now().toString(),
      name: newCharacter.name.trim(),
      profile: newCharacter.profile.trim(),
      memory: newCharacter.memory ? [newCharacter.memory.trim()] : []
    };

    onCharactersChange([...characters, character]);
    setNewCharacter({ name: '', profile: '', memory: '' });
    setIsAddingCharacter(false);
  };

  // Delete character
  const handleDeleteCharacter = (characterId: string) => {
    onCharactersChange(characters.filter(c => c.id !== characterId));
    if (selectedCharacter?.id === characterId) {
      onCharacterSelect(characters[0] || {} as Character);
    }
  };

  // Select character
  const handleSelectCharacter = async (character: Character) => {
    onCharacterSelect(character);
    setIsLoading(true);
    
    try {
      const response = await apiService.getCharacterInfo(character.name);
      if (response.success && response.data) {
        setCharacterInfo(response.data);
      }
    } catch (error) {
      console.error('Failed to load character info:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Upload avatar
  const handleAvatarUpload = async (file: File, character: Character) => {
    try {
      const response = await apiService.uploadCharacterAvatar(file, character.name);
      if (response.success) {
        // Update character avatar
        onCharactersChange(characters.map(c => 
          c.id === character.id 
            ? { ...c, avatar: URL.createObjectURL(file) }
            : c
        ));
      }
    } catch (error) {
      console.error('Failed to upload avatar:', error);
    }
  };

  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>, character: Character) => {
    const file = event.target.files?.[0];
    if (file) {
      handleAvatarUpload(file, character);
    }
  };

  return (
    <div className="flex h-full">
      {/* Character list */}
      <div className="w-1/3 border-r border-border">
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Character List</h3>
            <Button
              size="sm"
              onClick={() => setIsAddingCharacter(true)}
              className="flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Add Character
            </Button>
          </div>

          {/* Add character form */}
          {isAddingCharacter && (
            <Card className="mb-4">
              <CardContent className="p-4 space-y-3">
                <Input
                  placeholder="Character name"
                  value={newCharacter.name}
                  onChange={(e) => setNewCharacter(prev => ({ ...prev, name: e.target.value }))}
                />
                <Textarea
                  placeholder="Character profile"
                  value={newCharacter.profile}
                  onChange={(e) => setNewCharacter(prev => ({ ...prev, profile: e.target.value }))}
                  rows={3}
                />
                <Textarea
                  placeholder="Initial memory"
                  value={newCharacter.memory}
                  onChange={(e) => setNewCharacter(prev => ({ ...prev, memory: e.target.value }))}
                  rows={2}
                />
                <div className="flex gap-2">
                  <Button size="sm" onClick={handleAddCharacter}>
                    Add
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => setIsAddingCharacter(false)}
                  >
                    Cancel
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <ScrollArea className="h-[calc(100%-120px)]">
          <div className="p-2 space-y-2">
            {characters.map((character) => (
              <Card
                key={character.id}
                className={`cursor-pointer transition-all hover:shadow-md ${
                  selectedCharacter?.id === character.id 
                    ? 'ring-2 ring-primary bg-primary/5' 
                    : ''
                }`}
                onClick={() => handleSelectCharacter(character)}
              >
                <CardContent className="p-3">
                  <div className="flex items-center gap-3">
                    <div className="relative">
                      <Avatar className="w-12 h-12">
                        <AvatarImage 
                          src={character.avatar || `/assets/${character.name}.jpg`} 
                          alt={character.name}
                        />
                        <AvatarFallback>
                          <User className="w-6 h-6" />
                        </AvatarFallback>
                      </Avatar>
                      <input
                        ref={fileInputRef}
                        type="file"
                        accept="image/*"
                        className="hidden"
                        onChange={(e) => handleFileSelect(e, character)}
                      />
                      <Button
                        size="sm"
                        variant="outline"
                        className="absolute -bottom-1 -right-1 w-6 h-6 p-0"
                        onClick={(e) => {
                          e.stopPropagation();
                          fileInputRef.current?.click();
                        }}
                      >
                        <Upload className="w-3 h-3" />
                      </Button>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium truncate">{character.name}</h4>
                      <p className="text-sm text-muted-foreground truncate">
                        {character.profile || 'No profile'}
                      </p>
                    </div>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="w-8 h-8 p-0 text-destructive hover:bg-destructive/10"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteCharacter(character.id);
                      }}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Character details */}
      <div className="flex-1 p-4">
        {selectedCharacter ? (
          <ScrollArea className="h-full">
            <div className="space-y-6">
              {/* Basic info */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="w-5 h-5" />
                    {selectedCharacter.name}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium mb-2">Character Profile</h4>
                      <p className="text-sm text-muted-foreground">
                        {characterInfo?.profile || selectedCharacter.profile || 'No profile'}
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Memory info */}
              {characterInfo?.memory && characterInfo.memory.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Clock className="w-5 h-5" />
                      Timeline Memory
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {characterInfo.memory.map((memory, index) => (
                        <div key={index} className="p-3 bg-muted rounded-lg">
                          <p className="text-sm">{memory}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* System chunks */}
              {characterInfo?.chunks && characterInfo.chunks.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <Brain className="w-5 h-5" />
                      System Chunks
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {characterInfo.chunks.map((chunk, index) => (
                        <Badge key={index} className="mr-2 mb-2 bg-secondary text-secondary-foreground">
                          {chunk}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Retrieved chunks */}
              {characterInfo?.retrieved && characterInfo.retrieved.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Recent Retrieved Chunks</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {characterInfo.retrieved.map((item, index) => (
                        <div key={index} className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                          <p className="text-sm">{item.Info}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Prompts */}
              {characterInfo?.prompts && characterInfo.prompts.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>React Prompts</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {characterInfo.prompts.map((prompt, index) => (
                        <div key={index} className="space-y-2">
                          <pre className="text-xs bg-muted p-3 rounded overflow-x-auto">
                            {JSON.stringify(prompt, null, 2)}
                          </pre>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {isLoading && (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              )}
            </div>
          </ScrollArea>
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <div className="text-center">
              <User className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Select a character to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
