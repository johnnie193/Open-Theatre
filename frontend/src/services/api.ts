// API service layer - communicates with backend Flask API
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  success: boolean;
}

export interface Character {
  id: string;
  name: string;
  profile: string;
  avatar?: string;
  memory?: string[];
  chunks?: string[];
  retrieved?: Array<{ Info: string }>;
  prompts?: any[];
}

export interface Scene {
  id: string;
  name: string;
  info: string; // Scene description info
  mode: string;
  characters: Record<string, string>;
  chain: string[];
  stream?: Record<string, string[]>;
}

export interface Script {
  id: string;
  background: {
    narrative: string;
    player: string;
    characters: Record<string, string>;
    context?: Record<string, string>;
  };
  scenes: Record<string, Scene>;
}

export interface GameState {
  id: string;
  scene_cnt: number;
  nc: Array<[string, boolean]>;
  characters: Record<string, Character>;
  scenes: Record<string, Scene>;
  script: Script;
}

export interface Message {
  id: string;
  character: string;
  content: string;
  timestamp: Date;
  type: 'speak' | 'stay';
  bid?: string[];
}

export interface InteractionRequest {
  type?: string;
  message?: string;
  object?: string;
  interact?: 'next' | 'back' | 'withdraw';
}

export interface PromptSettings {
  prompt_drama_v1: string;
  prompt_drama_v1_reflect?: string;
  prompt_drama_v2: string;
  prompt_drama_v2_plus: string;
  prompt_character: string;
  prompt_character_v2: string;
  prompt_global_character: string;
  prompt_director_reflect?: string;
}

class ApiService {
  private baseUrl = ''; // Use relative path, proxy to Flask backend through Vite

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseUrl}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return { data, success: true };
    } catch (error) {
      console.error('API request failed:', error);
      return { 
        error: error instanceof Error ? error.message : 'Unknown error',
        success: false 
      };
    }
  }

  // Initialize game
  async initGame(): Promise<ApiResponse<GameState>> {
    return this.request<GameState>('/api/data', { method: 'GET' });
  }

  // Calculate interaction
  async calculateInteraction(request: InteractionRequest): Promise<ApiResponse<{
    done: boolean;
    state?: GameState;
    action?: Message[];
    input?: Message;
    error?: string;
    cnt?: number;
  }>> {
    return this.request('/api/interact', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }


  // Get all character list
  async getCharacters(): Promise<ApiResponse<{ characters: string[] }>> {
    return this.request<{ characters: string[] }>('/api/info', {
      method: 'POST',
      body: JSON.stringify({ help: 'characters' }),
    });
  }

  // Get world records
  async getWorldRecords(): Promise<ApiResponse<{
    allmemory: Record<string, string[]>;
    chunks: string[];
    retrieved: Array<{ Info: string }>;
  }>> {
    return this.request('/api/info', {
      method: 'POST',
      body: JSON.stringify({ help: 'allmemory' }),
    });
  }

  // Get system feedbacks
  async getSystemFeedbacks(): Promise<ApiResponse<{
    dramallm: any[];
  }>> {
    return this.request('/api/info', {
      method: 'POST',
      body: JSON.stringify({ help: 'dramallm' }),
    });
  }

  // Get script info
  async getScriptInfo(): Promise<ApiResponse<{
    allscript: string;
    scene_cnt: number;
    nc: Array<[string, boolean]>;
  }>> {
    return this.request('/api/info', {
      method: 'POST',
      body: JSON.stringify({ help: 'allscript' }),
    });
  }

  // Get character info
  async getCharacterInfo(characterName: string): Promise<ApiResponse<{
    profile: string;
    memory: string[];
    chunks: string[];
    retrieved: Array<{ Info: string }>;
    prompts: any[];
  }>> {
    return this.request('/api/info', {
      method: 'POST',
      body: JSON.stringify({ role: characterName }),
    });
  }

  // Save script configuration
  async saveScriptConfig(config: {
    id: string;
    background_narrative: string;
    player_name: string;
    characters: Array<{
      id: string;
      profile: string;
      initial_memory: string;
    }>;
    scenes: Record<string, any>;
    storageMode: boolean;
  }): Promise<ApiResponse<GameState>> {
    return this.request<GameState>('/api/data', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // Load script
  async loadScript(scriptName: string): Promise<ApiResponse<GameState>> {
    return this.request<GameState>('/api/load', {
      method: 'POST',
      body: JSON.stringify({ 
        script_name: scriptName,
        storageMode: true 
      }),
    });
  }

  // Save script
  async saveScript(): Promise<ApiResponse<{
    save_id: string;
    info: string;
  }>> {
    return this.request('/api/save', { method: 'GET' });
  }

  // Get saved script list
  async getSavedScripts(): Promise<ApiResponse<{ scripts: Array<{ id: string; name: string; timestamp: string; filename: string }> }>> {
    return this.request<{ scripts: Array<{ id: string; name: string; timestamp: string; filename: string }> }>('/api/saved-scripts', {
      method: 'GET',
    });
  }

  // Get prompt settings
  async getPromptSettings(): Promise<ApiResponse<PromptSettings>> {
    return this.request<PromptSettings>('/api/prompt', { method: 'GET' });
  }

  // Save prompt settings
  async savePromptSettings(prompts: PromptSettings): Promise<ApiResponse> {
    return this.request('/api/prompt', {
      method: 'POST',
      body: JSON.stringify(prompts),
    });
  }

  // Get model configuration
  async getModelConfig(): Promise<ApiResponse<{
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
  }>> {
    return this.request('/api/model-config', { method: 'GET' });
  }

  // Save model configuration
  async saveModelConfig(config: {
    provider: string;
    azure_openai?: {
      api_key: string;
      api_version: string;
      endpoint: string;
      deployment: string;
    };
    openai?: {
      api_key: string;
      base_url: string;
      model: string;
    };
    deepseek?: {
      api_key: string;
      api_url: string;
      model: string;
    };
  }): Promise<ApiResponse> {
    return this.request('/api/model-config', {
      method: 'POST',
      body: JSON.stringify(config),
    });
  }

  // Upload character avatar
  async uploadCharacterAvatar(file: File, characterName: string): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('name', characterName);
    
    try {
      const response = await fetch(`${this.baseUrl}/api/upload`, {
        method: 'POST',
        body: formData,
      });
      
      const data = await response.json();
      return { data, success: true };
    } catch (error) {
      return { 
        error: error instanceof Error ? error.message : 'Upload failed',
        success: false 
      };
    }
  }

  // Save settings (only update current script configuration, no file operations)
  async saveConfig(scriptData: {
    id: string;
    background_narrative: string;
    player_name: string;
    characters: Array<{
      id: string;
      profile: string;
      initial_memory: string;
    }>;
    scenes: Record<string, {
      sceneName: string;
      sceneInfo: string;
      chains: string[];
      streams: Record<string, string[]>;
      characters: Record<string, string>;
      mode: string;
    }>;
  }): Promise<ApiResponse<GameState>> {
    return this.request<GameState>('/api/data', {
      method: 'POST',
      body: JSON.stringify({
        id: scriptData.id,
        player_name: scriptData.player_name,
        background_narrative: scriptData.background_narrative,
        characters: scriptData.characters,
        scenes: scriptData.scenes,
        storageMode: true
      }),
    });
  }

  // Export records
  async exportRecords(): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/info`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ help: "export_records" })
    });
    
    if (!response.ok) {
      throw new Error('Export failed');
    }
    
    return response.blob();
  }
}

export const apiService = new ApiService();
