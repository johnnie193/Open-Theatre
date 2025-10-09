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
  Save,
  FilePlus
} from 'lucide-react';
import { apiService, GameState } from '../services/api';

interface LoadScriptProps {
  onGameStateChange: (gameState: GameState) => void;
  onSaveScriptSuccess?: () => void; // Callback after successful script save
  onNewScript?: () => void; // Callback for creating a new script
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
  onSaveScriptSuccess,
  onNewScript
}, ref) => {
  const [savedScripts, setSavedScripts] = useState<SavedScript[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [loadingScript, setLoadingScript] = useState<string | null>(null);
  const [savingScript, setSavingScript] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Load saved script list
  useEffect(() => {
    loadSavedScripts();
  }, []);

  // Expose refresh method to parent component
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
        setMessage({ type: 'error', text: response.error || 'Failed to load saved scripts' });
        setSavedScripts([]);
      }
    } catch (error) {
      console.error('Failed to load saved scripts:', error);
      setMessage({ type: 'error', text: 'Failed to load saved scripts' });
      setSavedScripts([]);
    } finally {
      setIsLoading(false);
    }
  };

  // Save script
  const handleSaveScript = async () => {
    setSavingScript(true);
    setMessage(null);

    try {
      const response = await apiService.saveScript();
      if (response.success && response.data) {
        setMessage({ 
          type: 'success', 
          text: `Script saved! Save ID: ${response.data.save_id}` 
        });
        // Refresh script list
        loadSavedScripts();
        // Trigger parent component callback
        if (onSaveScriptSuccess) {
          onSaveScriptSuccess();
        }
      } else {
        setMessage({ type: 'error', text: response.error || 'Failed to save script' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save script, please try again' });
    } finally {
      setSavingScript(false);
    }
  };

  // Load script
  const handleLoadScript = async (scriptId: string) => {
    setLoadingScript(scriptId);
    setMessage(null);

    try {
      const response = await apiService.loadScript(scriptId);
      if (response.success && response.data) {
        onGameStateChange(response.data);
        setMessage({ type: 'success', text: `Script ${scriptId} loaded successfully!` });
      } else {
        setMessage({ type: 'error', text: response.error || 'Load failed' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'Load failed, please try again' });
    } finally {
      setLoadingScript(null);
    }
  };

  // Create new script
  const handleNewScript = () => {
    if (onNewScript) {
      onNewScript();
      setMessage({ type: 'success', text: 'New script created! Please configure it in the Script Management tab.' });
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

      {/* Title and action buttons */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Download className="w-6 h-6" />
            Load Script
          </h2>
          <p className="text-muted-foreground mt-1">
            Select a saved script to load, or save the current script
          </p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={handleNewScript} 
            size="sm"
            variant="outline"
            className="border-blue-200 hover:bg-blue-50"
          >
            <FilePlus className="w-4 h-4 mr-2" />
            New Script
          </Button>
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
            Save Script
          </Button>
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
            Refresh List
          </Button>
        </div>
      </div>

      {/* Script list */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            Saved Scripts
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-32">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4" />
                <p className="text-muted-foreground">Loading script list...</p>
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
                        <span>Saved time: {script.timestamp}</span>
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
                      <span className="ml-2">Load</span>
                    </Button>
                  </div>
                ))}
              </div>
            </ScrollArea>
          ) : (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 mx-auto mb-4 text-muted-foreground/50" />
              <h3 className="text-lg font-medium mb-2">No saved scripts</h3>
              <p className="text-muted-foreground">
                Please create and save a script in "Current Script" first
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
});

LoadScript.displayName = 'LoadScript';
