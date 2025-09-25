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

  // 加载提示词设置
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
        setMessage({ type: 'error', text: response.error || '加载提示词失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '加载提示词失败，请重试' });
    } finally {
      setIsLoading(false);
    }
  };

  // 保存提示词设置
  const handleSavePrompts = async () => {
    setIsSaving(true);
    setMessage(null);

    try {
      const response = await apiService.savePromptSettings(prompts);
      if (response.success) {
        setMessage({ type: 'success', text: '提示词保存成功！' });
      } else {
        setMessage({ type: 'error', text: response.error || '保存失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '保存失败，请重试' });
    } finally {
      setIsSaving(false);
    }
  };

  // 更新提示词
  const handlePromptChange = (key: keyof PromptSettings, value: string) => {
    setPrompts(prev => ({ ...prev, [key]: value }));
  };

  const promptConfigs = [
    {
      key: 'prompt_drama_v1' as keyof PromptSettings,
      title: 'v1 - One-for-All',
      description: '圆桌模式，总导演决策',
      icon: <Brain className="w-5 h-5" />,
      color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    },
    {
      key: 'prompt_drama_v1_reflect' as keyof PromptSettings,
      title: 'v1 - Reflect',
      description: 'v1 反思提示词',
      icon: <Brain className="w-5 h-5" />,
      color: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
    },
    {
      key: 'prompt_drama_v2' as keyof PromptSettings,
      title: 'v2 - Director-Actor(single action)',
      description: '导演-演员模式',
      icon: <Users className="w-5 h-5" />,
      color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
    },
    {
      key: 'prompt_drama_v2_plus' as keyof PromptSettings,
      title: 'v2_plus - Director-Actor(multiple actions)',
      description: '多角色导演模式',
      icon: <Zap className="w-5 h-5" />,
      color: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
    },
    {
      key: 'prompt_character' as keyof PromptSettings,
      title: 'Character - Raw',
      description: '角色原始模式',
      icon: <Users className="w-5 h-5" />,
      color: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
    },
    {
      key: 'prompt_character_v2' as keyof PromptSettings,
      title: 'Character - Motivated',
      description: '角色动机模式',
      icon: <Brain className="w-5 h-5" />,
      color: 'bg-pink-100 text-pink-800 dark:bg-pink-900 dark:text-pink-200'
    },
    {
      key: 'prompt_global_character' as keyof PromptSettings,
      title: 'Global Character - v2 Prime',
      description: '全局角色主要模式',
      icon: <Settings className="w-5 h-5" />,
      color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200'
    }
    ,
    {
      key: 'prompt_director_reflect' as keyof PromptSettings,
      title: 'Director Reflect',
      description: '导演反思提示词',
      icon: <Settings className="w-5 h-5" />,
      color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200'
    }
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">加载提示词设置中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* 消息提示 */}
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

      {/* 保存按钮 */}
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">提示词管理</h2>
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
          保存提示词
        </Button>
      </div>

      {/* 提示词列表 */}
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
                placeholder={`请输入 ${config.title} 的提示词...`}
                rows={8}
                className="font-mono text-sm"
              />
              <div className="mt-2 text-xs text-muted-foreground">
                字符数: {(prompts[config.key] ?? '').length}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};



