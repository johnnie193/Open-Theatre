import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { 
  Save, 
  Settings, 
  Brain, 
  Users, 
  Zap,
  Loader2,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { apiService, PromptSettings } from '../services/api';

export const PromptManagement: React.FC = () => {
  const [prompts, setPrompts] = useState<PromptSettings>({
    prompt_drama_v1: '',
    prompt_drama_v1_reflect: '',
    prompt_drama_v2: '',
    prompt_drama_v2_plus: '',
    prompt_character: '',
    prompt_character_v2: '',
    prompt_global_character: '',
    prompt_director_reflect: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Load prompt settings
  useEffect(() => {
    loadPrompts();
  }, []);

  const loadPrompts = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getPromptSettings();
      if (response.success && response.data) {
        setPrompts(response.data);
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to load prompts' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to load prompts, please try again' });
    } finally {
      setIsLoading(false);
    }
  };

  // Save prompt settings
  const handleSavePrompts = async () => {
    setIsSaving(true);
    setMessage(null);

    try {
      const response = await apiService.savePromptSettings(prompts);
      if (response.success) {
        setMessage({ type: 'success', text: 'Prompts saved successfully!' });
      } else {
        setMessage({ type: 'error', text: response.error || 'Save failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Save failed, please try again' });
    } finally {
      setIsSaving(false);
    }
  };

  // Update prompts
  const handlePromptChange = (key: keyof PromptSettings, value: string) => {
    setPrompts(prev => ({ ...prev, [key]: value }));
  };

  const promptConfigs = [
    {
      key: 'prompt_drama_v1' as keyof PromptSettings,
      title: 'v1 - One-for-All',
      description: 'Round table mode, general director decision',
      icon: <Brain className="w-5 h-5" />,
      color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    },
    {
      key: 'prompt_drama_v1_reflect' as keyof PromptSettings,
      title: 'v1 - Reflect',
      description: 'v1 reflection prompt',
      icon: <Brain className="w-5 h-5" />,
      color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    },
    {
      key: 'prompt_drama_v2' as keyof PromptSettings,
      title: 'v2 - Director-Actor(single action)',
      description: 'Director-actor mode',
      icon: <Users className="w-5 h-5" />,
      color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
    },
    {
      key: 'prompt_drama_v2_plus' as keyof PromptSettings,
      title: 'v2_plus - Director-Actor(multiple actions)',
      description: 'Multi-character director mode',
      icon: <Zap className="w-5 h-5" />,
      color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
    },
    {
      key: 'prompt_character' as keyof PromptSettings,
      title: 'Character - Raw',
      description: 'Character raw mode',
      icon: <Users className="w-5 h-5" />,
      color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
    },
    {
      key: 'prompt_character_v2' as keyof PromptSettings,
      title: 'Character - Motivated',
      description: 'Character motivation mode',
      icon: <Brain className="w-5 h-5" />,
      color: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200'
    },
    {
      key: 'prompt_global_character' as keyof PromptSettings,
      title: 'Global Character - v2 Prime',
      description: 'Global character main mode',
      icon: <Settings className="w-5 h-5" />,
      color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200'
    }
    ,
    {
      key: 'prompt_director_reflect' as keyof PromptSettings,
      title: 'Director Reflect',
      description: 'Director reflection prompt',
      icon: <Settings className="w-5 h-5" />,
      color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200'
    }
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading prompt settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Message notifications */}
      {message && (
        <Card className={message.type === 'success' ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}>
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

      {/* Save button */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Prompt Management</h2>
        <Button 
          onClick={handleSavePrompts} 
          disabled={isSaving}
          className="flex items-center gap-2"
        >
          {isSaving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          Save Prompts
        </Button>
      </div>

      {/* Prompt list */}
      <div className="space-y-4">
        {promptConfigs.map((config) => (
          <Card key={config.key}>
            <CardHeader>
              <div className="flex items-center gap-3">
                {config.icon}
                <div>
                  <CardTitle className="flex items-center gap-2">
                    {config.title}
                    <Badge className={config.color}>
                      {config.description}
                    </Badge>
                  </CardTitle>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <Textarea
                value={prompts[config.key] ?? ''}
                onChange={(e) => handlePromptChange(config.key, e.target.value)}
                placeholder={`Enter prompt for ${config.title}...`}
                rows={8}
                className="font-mono text-sm"
              />
              <div className="mt-2 text-xs text-muted-foreground">
                Character count: {(prompts[config.key] ?? '').length}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};



