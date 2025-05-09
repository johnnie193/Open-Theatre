import traceback
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import yaml
from frame import *
import time
import re
import os

# 定义数据模型
class Character(BaseModel):
    id: Optional[str] = None
    profile: Optional[str] = None

class Scene(BaseModel):
    sceneName: Optional[str] = None
    sceneInfo: Optional[str] = None
    chains: Optional[List[str]] = None
    streams: Optional[List[str]] = None
    characters: Optional[List[str]] = None
    mode: Optional[str] = None

class ScriptData(BaseModel):
    id: Optional[str] = None
    player_name: Optional[str] = None
    background_narrative: Optional[str] = None
    characters: Optional[List[Character]] = None
    characters_initial_memories: Optional[Dict[str, str]] = None
    scenes: Optional[Dict[str, Scene]] = None

class Action(BaseModel):
    x: str
    bid: Optional[str] = None
    content: Optional[str] = None

class Prompt(BaseModel):
    name: str
    content: str

class InteractRequest(BaseModel):
    type: str
    message: Optional[str] = None
    object: Optional[str] = None

class DRAMA:
    def __init__(self):
        super().__init__()
        self.cache = 'cache/'

    def init(self, script):
        self.dramallm = DramaLLM(script=script)
        try:
            self.dramallm.update_view(self.dramallm.player.id)
        except Exception as e:
            return "请将玩家加入当前场景!"

    def round(self, act):
        action = []
        error = None
        print("mode", self.dramallm.mode)
        while True:
            try:
                if len(act) == 3:
                    self.dramallm.calculate(self.dramallm.player.id, x=act[0], bid=act[1], content=act[2])
                elif len(act) == 1:
                    self.dramallm.calculate(self.dramallm.player.id, x=act[0])
                if self.dramallm.mode == 'v1':
                    self.dramallm.v1_react()
                elif self.dramallm.mode == "v2":
                    self.dramallm.v2_react()
                for char_id, char in self.dramallm.scenes["scene"+str(self.dramallm.scene_cnt)].characters.items():
                    self.dramallm.update_view(char_id)
                    if char_id == self.dramallm.player.id:
                        continue
                    if char.status == "/faint/":
                        continue
                    if not char.to_do:
                        continue
                    scene = self.dramallm.scenes["scene"+str(self.dramallm.scene_cnt)]
                    decision = char.act(self.dramallm.narrative, scene.info)
                    decision.update({"aid": char_id})
                    if decision["x"] == "-speak":
                        self.dramallm.calculate(char_id, decision["x"], decision.get("bid", None), None, content=decision.get("content", None))
                    else:
                        self.dramallm.calculate(char_id, **decision)
                    action.append(decision)
                if self.dramallm.ready_for_next_scene:
                    self.dramallm.next_scene()
                break
            except Exception as e:
                error = e
                print('Caught this error: ', error)
                print(traceback.print_exc())
        return action, self.dramallm.ready_for_next_scene, error

    def reset(self):
        self.dramallm = None
    
    def update(self, data: ScriptData):
        if hasattr(self, 'dramallm'):
            try:
                # Case II pop player
                id_list = [character.id for character in data.characters]
                for cid in self.dramallm.script["background"]["characters"]:
                    if cid not in id_list:
                        self.dramallm.pop_characters(self.dramallm.characters[cid])
                        
                # Case I Easy modification
                self.dramallm.id = self.dramallm.script["id"] = data.id
                self.dramallm.script["background"]["player"] = data.player_name
                self.dramallm.player = self.dramallm.characters[data.player_name]
                self.dramallm.narrative = self.dramallm.script["background"]["narrative"] = data.background_narrative
                self.dramallm.script["background"]["characters"] = {}
                self.dramallm.script["background"]["context"] = {}
                
                for character in data.characters:
                    self.dramallm.script["background"]["characters"].update({character.id: character.profile})
                    if data.characters_initial_memories[character.id] and character.id in self.dramallm.script["background"]["context"] and (self.dramallm.script["background"]["context"][character.id] != data.characters_initial_memories[character.id]):
                        raise Exception('Initial memories changed! reload the script!')
                    else:
                        self.dramallm.script["background"]["context"].update({character.id: data.characters_initial_memories[character.id]})
                    if character.id not in self.dramallm.characters:
                        character_config = {"id": character.id, "profile": character.profile}
                        character_llm = CharacterLLM(config=character_config)
                        if data.characters_initial_memories[character.id]:
                            character_llm.update_memory(message=data.characters_initial_memories[character.id])
                        self.dramallm.add_characters(character_llm)
                    else:
                        self.dramallm.characters[character.id].profile = character.profile

                if "scene"+str(self.dramallm.scene_cnt) not in data.scenes:
                    self.dramallm.next_scene()
                    print("current scene deletion!")
                
                scenes_to_delete = []
                for sid, s in self.dramallm.script["scenes"].items():
                    if sid not in data.scenes:
                        print(sid, "not in data")
                        scenes_to_delete.append(sid)
                        print("scene deletion!")
                
                for sid in scenes_to_delete:
                    self.dramallm.script["scenes"].pop(sid)

                for sid, scene in data.scenes.items():
                    if sid in self.dramallm.scenes:
                        if sid == "scene"+str(self.dramallm.scene_cnt):
                            self.mode = scene.mode
                        self.dramallm.scenes[sid].name = scene.sceneName
                        self.dramallm.scenes[sid].info = scene.sceneInfo
                    self.dramallm.script["scenes"][sid] = {
                        "scene": scene.sceneName,
                        "info": scene.sceneInfo,
                        "chain": scene.chains,
                        "stream": scene.streams,
                        "characters": scene.characters,
                        "mode": scene.mode
                    }
                self.dramallm.mode = self.dramallm.script["scenes"]["scene"+str(self.dramallm.scene_cnt)]["mode"]
                self.dramallm.log(dumps(self.dramallm.script), "script_new")
                return
            except Exception as error:
                print('Caught this error: ', error)
                print(traceback.print_exc())
                
        # Case III reload
        try:
            script = {
                "id": data.id,
                "background": {
                    "player": data.player_name,
                    "narrative": data.background_narrative,
                    "characters": {},
                    "context": {}
                },
                "scenes": {}
            }
            for character in data.characters:
                script["background"]["characters"].update({character.id: character.profile})
                if data.characters_initial_memories[character.id]:
                    script["background"]["context"].update({character.id: data.characters_initial_memories[character.id]})
            for sid, scene in data.scenes.items():
                config = {
                    "name": scene.sceneName,
                    "scene": scene.sceneInfo,
                    "chain": scene.chains,
                    "stream": scene.streams,
                    "characters": scene.characters,
                    "mode": scene.mode
                }
                script["scenes"].update({sid: config})
            error = self.init(script)
            if error:
                return f"Initialization failure: {error}"
        except Exception as e:
            print('Caught this error: ', e)
            print(traceback.print_exc())
            return f"Initialization failure: {e}"

    @property
    def state(self):        
        return self.dramallm.state

# 创建 FastAPI 应用
app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/components", StaticFiles(directory="components"), name="components")

# 创建 DRAMA 实例
dramaworld = DRAMA()

# 预设的剧本和提示词
PRESET_SCRIPTS = {
    'hp': "Harry Potter and the Philosopher's Stone.yaml",
    'station': "Seven people in the waiting room.yaml",
    'romeo': "Romeo and Juliet.yaml"
}

PRESET_PROMPTS = {
    'v1': {
        'name': 'v1 - One-for-All',
        'content': 'You are a character in a drama...'
    },
    'v2': {
        'name': 'v2 - Director-Actor',
        'content': 'You are a director in a drama...'
    },
    'character_raw': {
        'name': 'Character - Raw',
        'content': 'You are a raw character...'
    },
    'character_motivated': {
        'name': 'Character - Motivated',
        'content': 'You are a motivated character...'
    }
}

# API 路由
@app.get("/api/scripts")
async def get_scripts():
    """获取所有预设剧本"""
    return PRESET_SCRIPTS

@app.get("/api/presets")
async def get_presets():
    """获取所有预设提示词"""
    return PRESET_PROMPTS

@app.get("/api/prompts")
async def get_prompts():
    """获取当前提示词"""
    if not hasattr(dramaworld, 'dramallm'):
        raise HTTPException(status_code=400, detail="No valid setup!")
    return {
        'v1': dramaworld.dramallm.prompt_v1,
        'v2': dramaworld.dramallm.prompt_v2
    }

@app.post("/api/prompts")
async def update_prompts(prompt: Prompt):
    """更新提示词"""
    if not hasattr(dramaworld, 'dramallm'):
        raise HTTPException(status_code=400, detail="No valid setup!")
    if prompt.name == 'v1':
        dramaworld.dramallm.prompt_v1 = prompt.content
    elif prompt.name == 'v2':
        dramaworld.dramallm.prompt_v2 = prompt.content
    return {"status": "success"}

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

@app.get("/{filename}")
async def serve_root(filename: str):
    return FileResponse(filename)

@app.post("/api/data")
async def api_data(data: ScriptData):
    error = dramaworld.update(data)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return dramaworld.state

@app.post("/api/load")
async def load_script(script_name: str):
    """加载剧本"""
    if script_name in PRESET_SCRIPTS:
        with open(f"script/{PRESET_SCRIPTS[script_name]}", encoding='utf-8') as file:
            script = yaml.safe_load(file)
        dramaworld.init(script)
        return dramaworld.state
    else:
        match = re.match(r"load-script-(.*)", script_name)
        if match:
            script_id = match.group(1)
            with open(f'{dramaworld.cache}/{script_id}.yml', encoding='utf-8') as file:
                script = yaml.safe_load(file)
            dramaworld.init(script["script"])
            dramaworld.dramallm.load(script_id)
            return dramaworld.state
    raise HTTPException(status_code=400, detail="Invalid script name")

@app.get("/api/save")
async def save_script():
    """保存当前剧本"""
    if hasattr(dramaworld, 'dramallm'):
        try:
            save_id = dramaworld.dramallm.save()
            return {"info": f"Saved in {dramaworld.cache} as {save_id} successfully!", "save_id": save_id}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Save config first to create your world, then save the script file!")

@app.post("/api/info")
async def get_info(role: str):
    """获取角色信息"""
    if not hasattr(dramaworld, 'dramallm'):
        raise HTTPException(status_code=400, detail="No valid setup!")
    if role not in dramaworld.dramallm.characters:
        raise HTTPException(status_code=404, detail="Character not found")
    return {
        "profile": dramaworld.dramallm.characters[role].profile,
        "memory": dramaworld.dramallm.characters[role].memory
    }

@app.post("/api/interact")
async def interact(action: Action):
    """角色交互"""
    if not hasattr(dramaworld, 'dramallm'):
        raise HTTPException(status_code=400, detail="No valid setup!")
    act = [action.x]
    if action.bid:
        act.append(action.bid)
    if action.content:
        act.append(action.content)
    actions, ready_for_next_scene, error = dramaworld.round(act)
    if error:
        raise HTTPException(status_code=500, detail=str(error))
    return {
        "actions": actions,
        "ready_for_next_scene": ready_for_next_scene,
        "state": dramaworld.state
    }

@app.post("/api/upload")
async def upload_script(file: UploadFile = File(...)):
    """上传剧本文件"""
    try:
        content = await file.read()
        script = yaml.safe_load(content)
        dramaworld.init(script)
        return dramaworld.state
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000) 