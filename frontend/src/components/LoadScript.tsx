import { useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ScrollArea } from './ui/scroll-area';
import { Badge } from './ui/badge';
import { 
  Download, 
  FileText, 
  Play,
  Loader2,
  CheckCircle,
  AlertCircle,
  Clock,
  Save
} from 'lucide-react';
import { apiService, GameState } from '../services/api';

interface LoadScriptProps {
  onGameStateChange: (gameState: GameState) => void;
  onSaveScriptSuccess?: () => void; // 保存脚本成功后的回调
}

export interface LoadScriptRef {
  refreshScripts: () => void;
}

interface SavedScript {
  id: string;
  name: string;
  timestamp: string;
}

export const LoadScript = forwardRef<LoadScriptRef, LoadScriptProps>(({
  onGameStateChange,
  onSaveScriptSuccess
}, ref) => {
  const [savedScripts, setSavedScripts] = useState<SavedScript[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingScript, setLoadingScript] = useState<string | null>(null);
  const [savingScript, setSavingScript] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // 加载保存的脚本列表
  useEffect(() => {
    loadSavedScripts();
  }, []);

  // 暴露刷新方法给父组件
  useImperativeHandle(ref, () => ({
    refreshScripts: loadSavedScripts
  }));

  const loadSavedScripts = async () => {
    setIsLoading(true);
    try {
      const response = await apiService.getSavedScripts();
      if (response.success && response.data) {
        setSavedScripts(response.data.scripts);
      } else {
        setMessage({ type: 'error', text: response.error || '加载已保存脚本失败' });
        setSavedScripts([]);
      }
    } catch (error) {
      console.error('Failed to load saved scripts:', error);
      setMessage({ type: 'error', text: '加载已保存脚本失败' });
      setSavedScripts([]);
    } finally {
      setIsLoading(false);
    }
  };

  // 保存脚本
  const handleSaveScript = async () => {
    setSavingScript(true);
    setMessage(null);

    try {
      const response = await apiService.saveScript();
      if (response.success && response.data) {
        setMessage({ 
          type: 'success', 
          text: `脚本已保存！保存ID: ${response.data.save_id}` 
        });
        // 刷新脚本列表
        loadSavedScripts();
        // 触发父组件回调
        if (onSaveScriptSuccess) {
          onSaveScriptSuccess();
        }
      } else {
        setMessage({ type: 'error', text: response.error || '保存脚本失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '保存脚本失败，请重试' });
    } finally {
      setSavingScript(false);
    }
  };

  // 加载脚本
  const handleLoadScript = async (scriptId: string) => {
    setLoadingScript(scriptId);
    setMessage(null);

    try {
      const response = await apiService.loadScript(scriptId);
      if (response.success && response.data) {
        onGameStateChange(response.data);
        setMessage({ type: 'success', text: `脚本 ${scriptId} 加载成功！` });
      } else {
        setMessage({ type: 'error', text: response.error || '加载失败' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: '加载失败，请重试' });
    } finally {
      setLoadingScript(null);
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

      {/* 标题和操作按钮 */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Download className="w-6 h-6" />
            读取脚本
          </h2>
          <p className="text-muted-foreground mt-1">
            从已保存的脚本中选择一个来加载，或保存当前脚本
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={handleSaveScript} 
            disabled={savingScript} 
            size="sm"
            className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
          >
            {savingScript ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Save className="w-4 h-4 mr-2" />
            )}
            保存脚本
          </Button>
        </div>
        <Button 
          onClick={loadSavedScripts} 
          disabled={isLoading}
          variant="outline"
          size="sm"
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <FileText className="w-4 h-4" />
          )}
          刷新列表
        </Button>
      </div>

      {/* 脚本列表 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            已保存的脚本
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground">加载脚本列表中...</p>
              </div>
            </div>
          ) : savedScripts.length > 0 ? (
            <ScrollArea className="h-96">
              <div className="space-y-3">
                {savedScripts.map((script) => (
                  <div 
                    key={script.id} 
                    className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h4 className="font-medium text-lg">{script.name}</h4>
                        <Badge variant="outline" className="text-xs">
                          {script.id}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="w-4 h-4" />
                        <span>保存时间: {script.timestamp}</span>
                      </div>
                    </div>
                    <Button
                      onClick={() => handleLoadScript(script.id)}
                      disabled={loadingScript === script.id}
                      className="ml-4"
                    >
                      {loadingScript === script.id ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Play className="w-4 h-4" />
                      )}
                      <span className="ml-2">加载</span>
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50" />
              <h3 className="text-lg font-medium mb-2">暂无保存的脚本</h3>
              <p className="text-muted-foreground">
                请先在"当前脚本"中创建并保存脚本
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
});

LoadScript.displayName = 'LoadScript';
