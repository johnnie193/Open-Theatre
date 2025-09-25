import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { 
  Settings, 
  Loader2,
  CheckCircle,
  AlertCircle,
  Key,
  Server,
  Brain
} from 'lucide-react';
import { apiService } from '../services/api';

interface ModelConfigProps {
  onConfigChange?: () => void;
}

interface ModelConfigData {
  provider: string;
  azure_openai: {
    api_key: string;
    api_version: string;
    endpoint: string;
    deployment: string;
  };
  openai: {
    api_key: string;
    base_url: string;
    model: string;
  };
  deepseek: {
    api_key: string;
    api_url: string;
    model: string;
  };
}

export const ModelConfig: React.FC<ModelConfigProps> = ({ onConfigChange }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [config, setConfig] = useState<ModelConfigData | null>(null);

  // 加载模型配置
  useEffect(() => {
    loadModelConfig();
  }, []);

  const loadModelConfig = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getModelConfig();
      if (response.success && response.data) {
        setConfig(response.data);
      } else {
        setMessage({ type: 'error', text: response.error || '加载模型配置失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '加载模型配置失败，请重试' });
    } finally {
      setIsLoading(false);
    }
  };

  // 保存模型配置
  const handleSaveConfig = async () => {
    if (!config) return;

    setIsLoading(true);
    setMessage(null);

    try {
      const response = await apiService.saveModelConfig(config);
      if (response.success) {
        setMessage({ type: 'success', text: '模型配置保存成功！' });
        if (onConfigChange) {
          onConfigChange();
        }
      } else {
        setMessage({ type: 'error', text: response.error || '保存失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '保存失败，请重试' });
    } finally {
      setIsLoading(false);
    }
  };

  // 更新配置
  const updateConfig = (provider: string, field: string, value: string) => {
    if (!config) return;
    
    setConfig(prev => {
      if (!prev) return prev;
      
      const newConfig = { ...prev };
      if (provider === 'main') {
        (newConfig as any)[field] = value;
      } else {
        if (!newConfig[provider as keyof ModelConfigData]) {
          (newConfig as any)[provider] = {};
        }
        (newConfig as any)[provider][field] = value;
      }
      return newConfig;
    });
  };

  if (!config) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    );
  }

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

      {/* 模型提供商选择 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            模型提供商
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <Label htmlFor="provider">选择提供商</Label>
              <Select 
                value={config.provider} 
                onValueChange={(value) => updateConfig('main', 'provider', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="选择模型提供商" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="azure_openai">Azure OpenAI</SelectItem>
                  <SelectItem value="openai">OpenAI</SelectItem>
                  <SelectItem value="deepseek">DeepSeek</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 配置详情 */}
      <Tabs value={config.provider} onValueChange={(value) => updateConfig('main', 'provider', value)}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="azure_openai">Azure OpenAI</TabsTrigger>
          <TabsTrigger value="openai">OpenAI</TabsTrigger>
          <TabsTrigger value="deepseek">DeepSeek</TabsTrigger>
        </TabsList>

        {/* Azure OpenAI 配置 */}
        <TabsContent value="azure_openai">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="w-5 h-5" />
                Azure OpenAI 配置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="azure_api_key">API Key</Label>
                <div className="relative">
                  <Key className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="azure_api_key"
                    type="password"
                    value={config.azure_openai.api_key}
                    onChange={(e) => updateConfig('azure_openai', 'api_key', e.target.value)}
                    placeholder="输入 Azure OpenAI API Key"
                    className="pl-10"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="azure_endpoint">Endpoint</Label>
                <Input
                  id="azure_endpoint"
                  value={config.azure_openai.endpoint}
                  onChange={(e) => updateConfig('azure_openai', 'endpoint', e.target.value)}
                  placeholder="https://your-resource.openai.azure.com/"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="azure_api_version">API Version</Label>
                  <Input
                    id="azure_api_version"
                    value={config.azure_openai.api_version}
                    onChange={(e) => updateConfig('azure_openai', 'api_version', e.target.value)}
                    placeholder="2024-02-15-preview"
                  />
                </div>
                <div>
                  <Label htmlFor="azure_deployment">Deployment</Label>
                  <Input
                    id="azure_deployment"
                    value={config.azure_openai.deployment}
                    onChange={(e) => updateConfig('azure_openai', 'deployment', e.target.value)}
                    placeholder="gpt-4o"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* OpenAI 配置 */}
        <TabsContent value="openai">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="w-5 h-5" />
                OpenAI 配置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="openai_api_key">API Key</Label>
                <div className="relative">
                  <Key className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="openai_api_key"
                    type="password"
                    value={config.openai.api_key}
                    onChange={(e) => updateConfig('openai', 'api_key', e.target.value)}
                    placeholder="输入 OpenAI API Key"
                    className="pl-10"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="openai_base_url">Base URL</Label>
                <Input
                  id="openai_base_url"
                  value={config.openai.base_url}
                  onChange={(e) => updateConfig('openai', 'base_url', e.target.value)}
                  placeholder="https://api.openai.com/v1"
                />
              </div>
              <div>
                <Label htmlFor="openai_model">Model</Label>
                <Input
                  id="openai_model"
                  value={config.openai.model}
                  onChange={(e) => updateConfig('openai', 'model', e.target.value)}
                  placeholder="gpt-4o"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* DeepSeek 配置 */}
        <TabsContent value="deepseek">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Server className="w-5 h-5" />
                DeepSeek 配置
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="deepseek_api_key">API Key</Label>
                <div className="relative">
                  <Key className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="deepseek_api_key"
                    type="password"
                    value={config.deepseek.api_key}
                    onChange={(e) => updateConfig('deepseek', 'api_key', e.target.value)}
                    placeholder="输入 DeepSeek API Key"
                    className="pl-10"
                  />
                </div>
              </div>
              <div>
                <Label htmlFor="deepseek_api_url">API URL</Label>
                <Input
                  id="deepseek_api_url"
                  value={config.deepseek.api_url}
                  onChange={(e) => updateConfig('deepseek', 'api_url', e.target.value)}
                  placeholder="https://api.deepseek.com"
                />
              </div>
              <div>
                <Label htmlFor="deepseek_model">Model</Label>
                <Input
                  id="deepseek_model"
                  value={config.deepseek.model}
                  onChange={(e) => updateConfig('deepseek', 'model', e.target.value)}
                  placeholder="DeepSeek-V3"
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* 保存按钮 */}
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
          保存配置
        </Button>
      </div>
    </div>
  );
};

