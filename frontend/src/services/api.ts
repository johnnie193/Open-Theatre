// API服务层 - 与后端Flask API通信
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
  info: string; // 场景描述信息
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
  private baseUrl = ''; // 使用相对路径，通过Vite代理到Flask后端

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

  // 初始化游戏
  async initGame(): Promise<ApiResponse<GameState>> {
    return this.request<GameState>('/api/data', { method: 'GET' });
  }

  // 交互计算
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


  // 获取所有角色列表
  async getCharacters(): Promise<ApiResponse<{ characters: string[] }>> {
    return this.request<{ characters: string[] }>('/api/info', {
      method: 'POST',
      body: JSON.stringify({ help: 'characters' }),
    });
  }

  // 获取世界记录
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

  // 获取系统反馈
  async getSystemFeedbacks(): Promise<ApiResponse<{
    dramallm: any[];
  }>> {
    return this.request('/api/info', {
      method: 'POST',
      body: JSON.stringify({ help: 'dramallm' }),
    });
  }

  // 获取脚本信息
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

  // 获取角色信息
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

  // 保存脚本配置
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

  // 加载脚本
  async loadScript(scriptName: string): Promise<ApiResponse<GameState>> {
    return this.request<GameState>('/api/load', {
      method: 'POST',
      body: JSON.stringify({ 
        script_name: scriptName,
        storageMode: true 
      }),
    });
  }

  // 保存脚本
  async saveScript(): Promise<ApiResponse<{
    save_id: string;
    info: string;
  }>> {
    return this.request('/api/save', { method: 'GET' });
  }

  // 获取已保存的脚本列表
  async getSavedScripts(): Promise<ApiResponse<{ scripts: Array<{ id: string; name: string; timestamp: string; filename: string }> }>> {
    return this.request<{ scripts: Array<{ id: string; name: string; timestamp: string; filename: string }> }>('/api/saved-scripts', {
      method: 'GET',
    });
  }

  // 获取提示词设置
  async getPromptSettings(): Promise<ApiResponse<PromptSettings>> {
    return this.request<PromptSettings>('/api/prompt', { method: 'GET' });
  }

  // 保存提示词设置
  async savePromptSettings(prompts: PromptSettings): Promise<ApiResponse> {
    return this.request('/api/prompt', {
      method: 'POST',
      body: JSON.stringify(prompts),
    });
  }

  // 获取模型配置
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

  // 保存模型配置
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

  // 上传角色头像
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

  // 保存设置（只更新当前剧本配置，不涉及文件操作）
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

  // 导出记录
  async exportRecords(): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/info`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ help: "export_records" })
    });
    
    if (!response.ok) {
      throw new Error('导出失败');
    }
    
    return response.blob();
  }
}

export const apiService = new ApiService();
