import traceback
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field # Import Field for Pydantic v2
from typing import Dict, List, Optional, Any
import yaml
from frame import * # Assuming frame.py contains DRAMALLM, CharacterLLM, MemoryStorage, etc.
from utils import message_to_act, dumps, write_json
import time
import re
import os
import logging
from dotenv import load_dotenv
import datetime # Import datetime for use in save() function
from models import init_llm_service, get_llm_service

logging.basicConfig(level=logging.WARNING)  # 设置日志级别为WARNING
logger = logging.getLogger(__name__)
load_dotenv()
ENGLISH_MODE = bool(os.getenv("ENGLISH_MODE") and os.getenv("ENGLISH_MODE").lower() in ["true", "1", "t", "y", "yes"])
STORAGE_MODE = bool(os.getenv("STORAGE_MODE") and os.getenv("STORAGE_MODE").lower() in ["true", "1", "t", "y", "yes"])

# 初始化全局LLM服务
llm_service = init_llm_service()

# Define data models (using Pydantic v2 conventions like Field for Optional)
class CharacterRequest(BaseModel):
    id: Optional[str] = Field(None)
    profile: Optional[str] = Field(None)
    initial_memory: Optional[str] = Field(None)

class SceneRequest(BaseModel):
    sceneName: Optional[str] = Field(None)
    sceneInfo: Optional[str] = Field(None)
    chains: Optional[List[str]] = Field(None)
    streams: Optional[Dict[str, List[str]]] = Field(None)
    characters: Optional[Dict[str, str]] = Field(None)
    mode: Optional[str] = Field(None)

class ScriptData(BaseModel):
    id: Optional[str] = Field(None)
    player_name: Optional[str] = Field(None)
    background_narrative: Optional[str] = Field(None)
    characters: Optional[List[CharacterRequest]] = Field(None)
    scenes: Optional[Dict[str, SceneRequest]] = Field(None)
    storageMode: Optional[bool] = Field(False)

class LoadRequest(BaseModel):
    script_name: Optional[str] = Field(None)
    storageMode: Optional[bool] = Field(None)

class Action(BaseModel):
    x: str
    bid: Optional[str] = Field(None)
    content: Optional[str] = Field(None)

class InteractRequest(BaseModel):
    type: Optional[str] = Field(None)
    message: Optional[str] = Field(None)
    object: Optional[str] = Field(None)
    interact: Optional[str] = Field(None)

class Prompt(BaseModel):
    prompt_drama_v1: str
    prompt_drama_v2: str
    prompt_drama_v2_plus: str
    prompt_character: str
    prompt_character_v2: str
    prompt_global_character: str
    prompt_global_character: str

class InfoRequest(BaseModel):
    role: Optional[str] = Field(None)
    help: Optional[str] = Field(None)

class DRAMA:
    def __init__(self):
        self.storage = MemoryStorage()
        self.dramallm: Optional[DramaLLM] = None # Initialize as None
        self.cache = 'cache/'
        self.script_dir = 'script/'

    def init(self, script, storage_mode: bool = STORAGE_MODE):
        self.storage.reset() # Reset the storage for a clean start
        self.dramallm = DramaLLM(script=script, storage_mode=storage_mode, storager=self.storage)
        try:
            # Ensure player exists before updating view
            if not hasattr(self.dramallm, 'player') or self.dramallm.player is None:
                raise ValueError("Player character not found after script initialization.")
            self.dramallm.update_view(self.dramallm.player.id)
        except Exception as e:
            error_message = "You have to add the player into the current scene!" if ENGLISH_MODE else "你需要将玩家加入当前场景!"
            logger.error(f"DRAMA initialization error: {e}")
            logger.error(traceback.format_exc())
            return error_message
        return None # No error

    async def round(self, act):
        action = []
        error = None
        if not self.dramallm:
            return [], False, "DramaLLM not initialized. Load a script first."

        print("mode", self.dramallm.mode)
        try:
            if len(act) == 3:
                self.dramallm.calculate(self.dramallm.player.id, x=act[0], bid=act[1], content=act[2])
            elif len(act) == 1:
                self.dramallm.calculate(self.dramallm.player.id, x=act[0])

            if self.dramallm.mode == 'v1':
                self.dramallm.v1_react()
            elif self.dramallm.mode == "v2":
                self.dramallm.v2_react()
            # elif self.dramallm.mode == "v2_plus":
            #     # 使用同步版本的v2_plus
            #     self.dramallm.v2_plus_react()
            elif self.dramallm.mode == "v2_plus":
                # 异步版本的v2_plus，使用并行处理
                await self.dramallm.av2_plus_react()
            elif self.dramallm.mode == "v2_prime":
                self.dramallm.v2_prime_react()

            reflect_interval = int(os.getenv("REFLECT_INTERVAL", "5"))
            reflect = False
            if (self.dramallm.timestamp + 1) % reflect_interval == 0:
                reflect = True

            # Iterate through characters in the current scene
            current_scene_key = "scene" + str(self.dramallm.scene_cnt)
            if current_scene_key not in self.dramallm.scenes:
                raise ValueError(f"Current scene {current_scene_key} not found.")

            for char_id, char in list(self.dramallm.scenes[current_scene_key].characters.items()): # Use list() to avoid RuntimeError if dict changes during iteration
                self.dramallm.update_view(char_id)
                if char_id == self.dramallm.player.id:
                    continue
                if char.status == "/faint/":
                    continue
                if not char.to_do:
                    continue
                
                scene = self.dramallm.scenes[current_scene_key]
                decision = char.act(narrative=self.dramallm.narrative, info=scene.info, scene_id=current_scene_key)
                decision.update({"aid": char_id})
                
                if decision["x"] == "-speak":
                    # Ensure bid is a list if it's a single string for -speak
                    bid_val = decision.get("bid")
                    if isinstance(bid_val, str):
                        bid_val = [bid_val] # Convert to list for message_to_act consistency if needed
                    self.dramallm.calculate(char_id, decision["x"], bid_val, None, content=decision.get("content", None))
                else:
                    # self.dramallm.calculate(char_id, **decision)
                    pass
                action.append(decision)
                logger.info(f"successfully add action: {action}")

            if reflect:
                self.dramallm.reflect()

            if self.dramallm.ready_for_next_scene:
                self.dramallm.next_scene()
            return action, self.dramallm.ready_for_next_scene, None # No error

        except Exception as e:
            error = e
            logger.error(f'Caught this error in round: {error}')
            logger.error(traceback.format_exc())
            return action, self.dramallm.ready_for_next_scene, str(error)

    def reset(self):
        self.dramallm = None
        self.storage.reset() # Also reset the storage

    def update(self, data: ScriptData):
        if not hasattr(self, 'dramallm') or self.dramallm is None:
            # If dramallm is not initialized, treat this as a full reload
            logger.warning("DramaLLM not initialized during update. Performing full script reload.")
            return self._reload_script_from_data(data)

        try:
            # Handle storageMode change directly
            if data.storageMode is not None:
                self.dramallm.storage_mode = data.storageMode
            
            # Case II: Pop characters no longer in data
            if data.characters:
                id_list = {char.id for char in data.characters} # Use a set for faster lookup
                # Iterate over a copy of characters to allow modification during iteration
                for cid in list(self.dramallm.script["background"]["characters"].keys()):
                    if cid not in id_list:
                        if cid in self.dramallm.characters:
                            self.dramallm.pop_characters(self.dramallm.characters[cid])
                            logger.info(f"Popped character: {cid}")
            else: # If no characters are provided in data, consider all existing characters for removal
                 for cid in list(self.dramallm.script["background"]["characters"].keys()):
                    if cid in self.dramallm.characters:
                        self.dramallm.pop_characters(self.dramallm.characters[cid])
                        logger.info(f"Popped character: {cid} (no characters provided in update data)")


            # Case I: Easy modification - change world id, player name, background narrative,
            # character profile, scene mode, scene info, scene chain, scene stream / add initial memories, add characters
            if data.id is not None:
                self.dramallm.id = self.dramallm.script["id"] = data.id
            if data.player_name is not None:
                self.dramallm.script["background"]["player"] = data.player_name
                # Update player object reference if name changes and character exists
                if data.player_name in self.dramallm.characters:
                    self.dramallm.player = self.dramallm.characters[data.player_name]
                else:
                    logger.warning(f"Player '{data.player_name}' not found after update. Player object might be stale.")

            if data.background_narrative is not None:
                self.dramallm.narrative = self.dramallm.script["background"]["narrative"] = data.background_narrative

            # Update characters
            if data.characters:
                self.dramallm.script["background"]["characters"] = {} # Clear and rebuild
                self.dramallm.script["background"]["context"] = {} # Clear and rebuild initial contexts

                for char_req in data.characters:
                    # Update background characters in script
                    if char_req.id:
                        self.dramallm.script["background"]["characters"].update({char_req.id: char_req.profile})
                        if char_req.initial_memory:
                            self.dramallm.script["background"]["context"].update({char_req.id: char_req.initial_memory})

                        if char_req.id in self.dramallm.characters:
                            # Character exists, update profile
                            self.dramallm.characters[char_req.id].profile = char_req.profile
                            # Handle initial memory: if changed, it might require a full reload or careful handling
                            # Your original code raised an exception, which is a valid strategy for immutable initial memories
                            # For now, we'll allow it if it's the same, or handle new characters.
                            if char_req.initial_memory and self.dramallm.script["background"]["context"].get(char_req.id) != char_req.initial_memory:
                                logger.warning(f"Initial memory for {char_req.id} changed. Consider full script reload for consistency.")
                        else:
                            # New character, add to characters and scenes
                            character = CharacterLLM(config={"id": char_req.id, "profile": char_req.profile})
                            if char_req.initial_memory:
                                character.update_memory(text=char_req.initial_memory)
                            
                            # Add to global characters list in DramaLLM
                            self.dramallm.characters[char_req.id] = character

                            # Add to relevant scenes
                            if data.scenes: # Check provided scenes for character presence
                                for sid, scene_req in data.scenes.items():
                                    if scene_req.characters and char_req.id in scene_req.characters:
                                        if sid in self.dramallm.scenes: # Only add if scene is already loaded
                                            self.dramallm.scenes[sid].add_character(character, scene_req.characters[char_req.id])
                                        # Also ensure script's scene config is updated
                                        if sid not in self.dramallm.script["scenes"]:
                                            self.dramallm.script["scenes"][sid] = {} # Initialize if new scene
                                        if "characters" not in self.dramallm.script["scenes"][sid]:
                                            self.dramallm.script["scenes"][sid]["characters"] = []
                                        if char_req.id not in self.dramallm.script["scenes"][sid]["characters"]:
                                            self.dramallm.script["scenes"][sid]["characters"].append(char_req.id)
                            logger.info(f"Added new character: {char_req.id}")
            
            # Update scenes
            if data.scenes:
                # Remove scenes not in the update data
                scenes_to_delete = []
                for sid_existing in self.dramallm.script["scenes"].keys():
                    if sid_existing not in data.scenes:
                        scenes_to_delete.append(sid_existing)
                for sid_del in scenes_to_delete:
                    self.dramallm.script["scenes"].pop(sid_del)
                    if sid_del in self.dramallm.scenes: # If scene was loaded, remove it too
                        del self.dramallm.scenes[sid_del]
                    logger.info(f"Removed scene: {sid_del}")

                # Update/add scenes
                for sid, scenes_req in data.scenes.items():
                    if sid not in self.dramallm.script["scenes"]:
                        self.dramallm.script["scenes"][sid] = {} # Add new scene to script
                        logger.info(f"Added new scene to script: {sid}")

                    script_scene = self.dramallm.script["scenes"][sid]
                    if scenes_req.sceneName is not None:
                        script_scene["name"] = scenes_req.sceneName
                    if scenes_req.sceneInfo is not None:
                        script_scene["info"] = scenes_req.sceneInfo
                    if scenes_req.chains is not None:
                        script_scene["chain"] = scenes_req.chains
                    if scenes_req.streams is not None:
                        script_scene["stream"] = scenes_req.streams
                    else:
                        script_scene["stream"] = {} # Ensure it's an empty dict if None
                    if scenes_req.characters is not None:
                        script_scene["characters"] = scenes_req.characters
                    if scenes_req.mode is not None:
                        script_scene["mode"] = scenes_req.mode

                    # If the scene is already loaded (in self.dramallm.scenes), update its properties
                    if sid in self.dramallm.scenes:
                        scene_obj = self.dramallm.scenes[sid]
                        if scenes_req.sceneName is not None:
                            scene_obj.name = scenes_req.sceneName
                        if scenes_req.sceneInfo is not None:
                            scene_obj.info = scenes_req.sceneInfo
                        if scenes_req.mode is not None:
                            scene_obj.mode = scenes_req.mode
                        
                        # Handle characters within the loaded scene object
                        if scenes_req.characters is not None:
                            # Remove characters no longer in scene_req.characters
                            current_scene_chars = list(scene_obj.characters.keys())
                            for char_id_in_scene in current_scene_chars:
                                if char_id_in_scene not in scenes_req.characters:
                                    if char_id_in_scene in scene_obj.characters:
                                        scene_obj.pop_character(scene_obj.characters[char_id_in_scene])
                                        logger.info(f"Removed character {char_id_in_scene} from loaded scene {sid}")
                            # Add characters newly in scene_req.characters
                            for char_id_req, char_profile in scenes_req.characters.items():
                                if char_id_req not in scene_obj.characters:
                                    if char_id_req in self.dramallm.characters:
                                        scene_obj.add_character(self.dramallm.characters[char_id_req], char_profile)
                                        logger.info(f"Added character {char_id_req} to loaded scene {sid}")
                                    else:
                                        logger.warning(f"Attempted to add non-existent character {char_id_req} to loaded scene {sid}")
                                else:
                                    scene_obj.characters[char_id_req].motivation = char_profile
            # Special handling for current scene's mode (if the current scene was updated)
            current_scene_key = "scene" + str(self.dramallm.scene_cnt)
            if data.scenes and current_scene_key in data.scenes and data.scenes[current_scene_key].mode is not None:
                self.dramallm.mode = data.scenes[current_scene_key].mode
                logger.info(f"DramaLLM mode updated to: {self.dramallm.mode} based on current scene's mode.")

            # If the current scene configuration was entirely removed or becomes invalid
            if not data.scenes or current_scene_key not in data.scenes:
                logger.warning(f"Current scene '{current_scene_key}' configuration removed or not provided. Advancing to next scene.")
                # This could imply current scene deletion, in which case next_scene() will attempt to load a new one
                # Or, if this is not desired, a different handling is needed (e.g., reset, error)
                # For now, following original logic: if current scene data is gone, advance
                if self.dramallm.ready_for_next_scene: # Only advance if game state allows
                    self.dramallm.next_scene()
                else:
                    logger.warning("Not ready for next scene, cannot auto-advance after current scene config deletion.")
            
            # Log new script state (ensure dumps is defined or imported from somewhere)
            self.dramallm.log(dumps(self.dramallm.script), "script_new")
            
            return self.state # Return the updated state

        except Exception as error:
            logger.error(f'Caught this error during partial update: {error}')
            logger.error(traceback.format_exc())
            # If a partial update fails critically, fall back to full reload or return error
            logger.info("Attempting full script reload as fallback after partial update failure.")
            return self._reload_script_from_data(data, error_on_partial_update=str(error))

    def _reload_script_from_data(self, data: ScriptData, error_on_partial_update: Optional[str] = None):
        """Helper to fully re-initialize dramallm from ScriptData."""
        try:
            script = {
                "id": data.id if data.id is not None else "default_id",
                "background": {
                    "player": data.player_name if data.player_name is not None else "player",
                    "narrative": data.background_narrative if data.background_narrative is not None else "",
                    "characters": {},
                    "context": {}
                },
                "scenes": {}
            }
            if data.characters:
                for char_req in data.characters:
                    if char_req.id:
                        script["background"]["characters"].update({char_req.id: char_req.profile})
                        if char_req.initial_memory:
                            script["background"]["context"].update({char_req.id: char_req.initial_memory}) 
            if data.scenes:
                for sid, scenes_req in data.scenes.items():
                    config = {
                        "name": scenes_req.sceneName,
                        "info": scenes_req.sceneInfo,
                        "chain": scenes_req.chains,
                        "stream": scenes_req.streams if scenes_req.streams is not None else {},
                        "characters": scenes_req.characters,
                        "mode": scenes_req.mode
                    }
                    script["scenes"].update({sid: config})
            
            # Reset current dramallm before initializing a new one
            self.reset() # This sets self.dramallm to None and resets storage

            init_error = self.init(script, storage_mode=data.storageMode if data.storageMode is not None else True)
            if init_error:
                raise Exception(init_error)
            
            logger.info("Full script reload successful.")
            return self.state # Return the new state
        except Exception as e:
            logger.error(f'Caught this error during full reload: {e}')
            logger.error(traceback.format_exc())
            final_error_message = f"Initialization failure: {e}"
            if error_on_partial_update:
                final_error_message += f" (Original partial update error: {error_on_partial_update})"
            raise HTTPException(status_code=500, detail=final_error_message)

    @property
    def state(self): 
        if not self.dramallm:
            return {"error": "DramaLLM not initialized."} # Handle uninitialized state
        # Convert DramaLLM's internal state to a serializable dict
        # state_dict = {
        #     "id": self.dramallm.id,
        #     "player_name": self.dramallm.script["background"]["player"],
        #     "background_narrative": self.dramallm.narrative,
        #     "scene_cnt": self.dramallm.scene_cnt,
        #     "ready_for_next_scene": self.dramallm.ready_for_next_scene,
        #     "storageMode": self.dramallm.storage_mode,
        #     "mode": self.dramallm.mode, # Add current dramallm mode
        #     "script": self.dramallm.script, # Full script is useful for debugging/transforming back
        #     "characters": {cid: {"profile": char.profile} for cid, char in self.dramallm.characters.items()},
        #     "scenes": {sid: {"name": scene.name, "info": scene.info, "mode": scene.mode, "characters": {c_id: {} for c_id in scene.characters.keys()}} 
        #                for sid, scene in self.dramallm.scenes.items()},
        #     "all_records": self.dramallm.raw_records # Include raw records for easier export
        # }
        return self.dramallm.state

# Initialize DRAMA globally
_global_dramaworld_instance = DRAMA()

# Dependency that provides the DRAMA instance
def get_dramaworld() -> DRAMA:
    return _global_dramaworld_instance

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/assets", StaticFiles(directory="assets"), name="assets")
app.mount("/components", StaticFiles(directory="components"), name="components")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

@app.get("/{filename}")
async def serve_root(filename: str):
    return FileResponse(filename)

@app.get("/api/data")
async def api_data(dramaworld: DRAMA = Depends(get_dramaworld)):
    return dramaworld.state

@app.post("/api/data")
async def api_data_post(data: ScriptData, dramaworld: DRAMA = Depends(get_dramaworld)):
    try:
        updated_state = dramaworld.update(data)
        if isinstance(updated_state, str): # If update returns an error string
            raise HTTPException(status_code=500, detail=updated_state)
        return updated_state
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error in /api/data POST: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to update data: {str(e)}")

@app.post("/api/load")
async def load_script(data: LoadRequest, dramaworld: DRAMA = Depends(get_dramaworld)):
    """加载剧本"""
    logger.info(f"Loading script: {data.script_name}, StorageMode: {data.storageMode}")
    postix = "_eng" if ENGLISH_MODE else ""    
    print(f"Loading script: {data.script_name}, StorageMode: {data.storageMode}")
    print(f"Script directory: {dramaworld.script_dir}")
    try:
        storageMode = data.storageMode if data.storageMode is not None else True
        
        # 处理预定义的脚本
        if data.script_name == 'load-script-hp':
            with open(f"{dramaworld.script_dir}/Harry Potter and the Philosopher's Stone{postix}.yaml", encoding = 'utf-8') as file:
                script = yaml.safe_load(file)
            dramaworld.init(script, storage_mode=storageMode)
            return dramaworld.state
        elif data.script_name == 'load-script-station':
            with open(f"{dramaworld.script_dir}/Seven people in the waiting room{postix}.yaml", encoding = 'utf-8') as file:
                script = yaml.safe_load(file)
            dramaworld.init(script, storage_mode=storageMode)
            return dramaworld.state
        elif data.script_name == 'load-script-romeo':
            with open(f"{dramaworld.script_dir}/Romeo and Juliet{postix}.yaml", encoding = 'utf-8') as file:
                script = yaml.safe_load(file)
            dramaworld.init(script, storage_mode=storageMode)
            return dramaworld.state
        else:
            # 处理保存的脚本文件（前端现在直接发送文件名）
            script_filename = data.script_name
            script_path = f'{dramaworld.script_dir}/{script_filename}'
            
            # 检查文件是否存在
            if not os.path.exists(script_path):
                raise HTTPException(status_code=404, detail=f"Script file not found: {script_filename}")
            
            with open(script_path, encoding='utf-8') as file:
                script_data = yaml.safe_load(file)
            
            # 如果文件包含script字段，使用script字段；否则直接使用整个文件内容
            if isinstance(script_data, dict) and 'script' in script_data:
                script = script_data['script']
            else:
                script = script_data
                
            dramaworld.init(script, storage_mode=storageMode)
            
            # 如果是保存的脚本，尝试加载dramallm状态
            if isinstance(script_data, dict) and 'script' in script_data:
                # 从文件名提取脚本ID（去掉扩展名）
                script_id = os.path.splitext(script_filename)[0]
                dramaworld.dramallm.load(script_id)
            
            return dramaworld.state
            
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error loading script: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/save")
async def save(dramaworld: DRAMA = Depends(get_dramaworld)):
    if hasattr(dramaworld, 'dramallm') and dramaworld.dramallm:
        try:
            save_id = dramaworld.dramallm.save()
            return {"info": f"Saved in {dramaworld.script_dir} as {save_id} successfully!", "save_id": save_id}
        except Exception as e:
            logger.error(f"Error saving script: {e}")
            logger.error(traceback.format_exc())
            return {"error": f"Error message: {e}"}
    else:
        return {"error": "Save config first to create your world, then save the script file!"}

@app.get("/api/saved-scripts")
async def get_saved_scripts(dramaworld: DRAMA = Depends(get_dramaworld)):
    """获取已保存的脚本列表"""
    try:
        import os
        import glob
        from datetime import datetime
        
        scripts = []
        
        # 检查script目录
        script_dir = dramaworld.script_dir
        if os.path.exists(script_dir):
            yml_files = glob.glob(os.path.join(script_dir, "*.yml"))
            yaml_files = glob.glob(os.path.join(script_dir, "*.yaml"))
            all_files = yml_files + yaml_files
            
            for file_path in all_files:
                filename = os.path.basename(file_path)
                    
                # 获取文件修改时间
                mtime = os.path.getmtime(file_path)
                timestamp = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                # 从文件名提取脚本名称（去掉时间戳部分）
                name = filename.replace('.yml', '').replace('.yaml', '')
                # 去掉时间戳部分（格式：_MMDD_HHMMSS）
                import re
                name = re.sub(r'_\d{4}_\d{6}$', '', name)
                
                scripts.append({
                    "id": filename,
                    "name": name,
                    "timestamp": timestamp,
                    "filename": filename
                })
        

        scripts.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {"scripts": scripts}
    except Exception as e:
        logger.error(f"Error getting saved scripts: {e}")
        return {"error": f"Failed to get saved scripts: {str(e)}"}

@app.post("/api/info")
async def get_info(data: InfoRequest, dramaworld: DRAMA = Depends(get_dramaworld)):
    config = {"error": "No valid setup!"}
    if not hasattr(dramaworld, 'dramallm') or dramaworld.dramallm is None:
        return config # Return default error if dramallm is not initialized

    if data.role:
        cid = data.role
        if cid in dramaworld.dramallm.characters:
            config = {
                "profile": dramaworld.dramallm.characters[cid].profile,
                "memory": dramaworld.dramallm.characters[cid].get_memory_list_from_dict(),
                "chunks": dramaworld.dramallm.characters[cid].storage.all_chunks_values() if dramaworld.dramallm.characters[cid].storage_mode else None,
                "retrieved": dramaworld.dramallm.characters[cid].last_retrieved
            }
            if dramaworld.dramallm.mode in ['v2', 'v2_plus', 'v3']:
                config.update({"prompts": dramaworld.dramallm.characters[cid].reacts})
    elif data.help:
        if data.help == "allmemory":
            config = {
                "allmemory": dramaworld.dramallm.raw_records,
                "chunks": dramaworld.dramallm.record_storage.all_chunks_values() if dramaworld.dramallm.storage_mode else None,
                "retrieved": dramaworld.dramallm.last_retrieved if dramaworld.dramallm.storage_mode else None
            }
        elif data.help == "dramallm":
            config = {"dramallm": dramaworld.dramallm.reacts}
        elif data.help == "allscript":
            config = {
                "allscript": dramaworld.dramallm.script,
                "scene_cnt": dramaworld.dramallm.scene_cnt,
                "nc": dramaworld.dramallm.nc
            }
        elif data.help == "characters":
            current_scene_key = "scene" + str(dramaworld.dramallm.scene_cnt)
            if current_scene_key in dramaworld.dramallm.script["scenes"] and \
               "characters" in dramaworld.dramallm.script["scenes"][current_scene_key]:
                character_ids = dramaworld.dramallm.script["scenes"][current_scene_key]["characters"]
                filtered_char = list(filter(lambda x: x != dramaworld.dramallm.player.id, character_ids))
                filtered_char.append("null")
                config = {"characters": filtered_char}
            else:
                config = {"characters": []} # No characters in current scene or scene not found
        elif data.help == "export_records":
            logger.info("exporting records")
            save_id = dramaworld.dramallm.id + datetime.datetime.now().strftime("_%m%d_%H%M%S")
            write_json(dramaworld.dramallm.raw_records, f'{dramaworld.dramallm.cache}/record_{save_id}.yaml')            
            config = {
                "allmemory": dramaworld.dramallm.raw_records,
                "chunks": dramaworld.dramallm.record_storage.all_chunks_values() if dramaworld.dramallm.storage_mode else None
            }
    logger.info(config)                 
    return config
    
@app.post("/api/interact")
async def interact(data: InteractRequest, dramaworld: DRAMA = Depends(get_dramaworld)):
    start_time = time.time()
    if not hasattr(dramaworld, 'dramallm') or dramaworld.dramallm is None:
        return {"error": "DramaLLM not initialized. Please load a script first."}

    if data.type and data.type != "operation":
        input_action = {"x": data.type}
        act = []
        if data.type == "-stay":
            act = ["-stay"]
        elif data.type == "-speak":
            roles, message = message_to_act(data.message)
            if data.object and data.object not in roles:
                roles.append(data.object)

            current_scene_key = "scene" + str(dramaworld.dramallm.scene_cnt)
            if current_scene_key not in dramaworld.dramallm.script["scenes"] or \
               "characters" not in dramaworld.dramallm.script["scenes"][current_scene_key]:
                raise HTTPException(status_code=400, detail="Current scene or its characters are not defined in script.")

            # Filter roles to only include characters currently in the scene
            scene_characters = set(dramaworld.dramallm.script["scenes"][current_scene_key]["characters"])
            filtered_roles = [role for role in roles if role in scene_characters]

            act = ["-speak", filtered_roles, message]
            input_action = {"x": data.type, "bid": act[1], "content": act[2]}

        response_actions, done_status, error_message = await dramaworld.round(act)
        if error_message:
            return {"error": error_message}

        end_time = time.time()
        response_time = end_time - start_time
        print(f"Interaction took {response_time:.2f} seconds")
        return {"input": input_action, "action": response_actions, "done": done_status, "state": dramaworld.state, "response_time": response_time}
    
    elif data.interact:
        if data.interact == "next":
            dramaworld.dramallm.next_scene()
            return dramaworld.state
        elif data.interact == "back":
            dramaworld.dramallm.back_scene()
            return dramaworld.state
        elif data.interact == "withdraw":
            cnt = dramaworld.dramallm.withdraw()
            return {"state": dramaworld.dramallm.state, "cnt": cnt}
        elif data.interact == "reflect":
            dramaworld.dramallm.reflect()
            return {"state": dramaworld.dramallm.state, "message": "reflect done"} 
    
    return {"error": "Invalid interaction request."} # Default error for unhandled cases

# @app.post("/api/set_storage_mode")
# async def set_storage_mode(data: SetStorageModeRequest, dramaworld: DRAMA = Depends(get_dramaworld)):
#     """
#     独立设置 DRAMALLM 的 storage_mode。
#     需要在剧本加载后调用。
#     """
#     if not hasattr(dramaworld, 'dramallm') or dramaworld.dramallm is None:
#         raise HTTPException(status_code=400, detail="DRAMA world not initialized. Please load a script first.")
    
#     try:
#         dramaworld.dramallm.storage_mode = data.world_storageMode
#         save_id = dramaworld.dramallm.save()
#         with open(f'{dramaworld.cache}/{save_id}.yml', encoding='utf-8') as file:
#             script = yaml.safe_load(file)
#         dramaworld.init(script["script"], storage_mode=data.world_storageMode)
#         dramaworld.dramallm.load(save_id)
#         for cid, char in dramaworld.dramallm.characters.items():
#             char.storage_mode = data.character_storageMode
#         logger.info(f"Storage mode successfully set to: {data.world_storageMode}")
#         return {"message": f"Storage mode set to {data.world_storageMode} successfully.", "current_storage_mode": dramaworld.dramallm.storage_mode}
#     except Exception as e:
#         logger.error(f"Error setting storage mode: {str(e)}")
#         logger.error(traceback.format_exc())
#         raise HTTPException(status_code=500, detail=f"Failed to set storage mode: {str(e)}")

@app.post("/api/prompt")
async def post_prompt(data: Prompt, dramaworld: DRAMA = Depends(get_dramaworld)):
    postix = "_eng" if ENGLISH_MODE else ""
    if hasattr(dramaworld, 'dramallm') and dramaworld.dramallm:
        dramaworld.dramallm.prompt_v1 = data.prompt_drama_v1
        dramaworld.dramallm.prompt_v2 = data.prompt_drama_v2
        dramaworld.dramallm.prompt_v2_plus = data.prompt_drama_v2_plus
        dramaworld.dramallm.prompt_global_character = data.prompt_global_character
        for c, char in dramaworld.dramallm.characters.items():
            char.prompt = data.prompt_character
            char.prompt_v2 = data.prompt_character_v2
        
    
    # Save prompts to files
    prompt_files = {
        "prompt_drama_v1": f"prompt/prompt_drama_v1{postix}.md",
        "prompt_drama_v2": f"prompt/prompt_drama_v2{postix}.md",
        "prompt_drama_v2_plus": f"prompt/prompt_drama_v2_plus{postix}.md",
        "prompt_character": f"prompt/prompt_character{postix}.md",
        "prompt_character_v2": f"prompt/prompt_character_v2{postix}.md",        
        "prompt_global_character": f"prompt/prompt_global_character{postix}.md"
    }
    
    for key, filename in prompt_files.items():
        # Ensure 'prompt' directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(getattr(data, key)) # Access prompt data using getattr
    
    # Read back and return prompts (for confirmation)
    prompts = {}
    for key, filename in prompt_files.items():
        with open(filename, 'r', encoding='utf-8') as file:
            prompts[key] = file.read()
    return prompts

@app.get("/api/prompt")
async def get_prompt():
    prompts = {}
    postix = "_eng" if ENGLISH_MODE else ""
    # Define prompt file paths
    prompt_files = {
        "prompt_drama_v1": f"prompt/prompt_drama_v1{postix}.md",
        "prompt_drama_v2": f"prompt/prompt_drama_v2{postix}.md",
        "prompt_drama_v2_plus": f"prompt/prompt_drama_v2_plus{postix}.md",
        "prompt_character": f"prompt/prompt_character{postix}.md",
        "prompt_character_v2": f"prompt/prompt_character_v2{postix}.md",        
        "prompt_global_character": f"prompt/prompt_global_character{postix}.md"
    }

    for key, filename in prompt_files.items():
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as file:
                prompts[key] = file.read()
        else:
            prompts[key] = "" # Return empty string if file not found
            logger.warning(f"Prompt file not found: {filename}")
    return prompts

@app.get("/api/model-config")
async def get_model_config():
    """获取模型配置"""
    try:
        config = {
            "provider": os.getenv("LLM_PROVIDER", "azure_openai"),
            "azure_openai": {
                "api_key": os.getenv("AZURE_API_KEY", ""),
                "api_version": os.getenv("AZURE_API_VERSION", "2024-02-15-preview"),
                "endpoint": os.getenv("AZURE_ENDPOINT", ""),
                "deployment": os.getenv("AZURE_DEPLOYMENT", "gpt-4o")
            },
            "openai": {
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                "model": os.getenv("OPENAI_MODEL", "gpt-4o")
            },
            "deepseek": {
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "api_url": os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com"),
                "model": os.getenv("DEEPSEEK_MODEL", "DeepSeek-V3")
            }
        }
        return config
    except Exception as e:
        logger.error(f"Error getting model config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/model-config")
async def save_model_config(config: dict):
    """保存模型配置"""
    try:
        import json
        
        # 验证配置
        if "provider" not in config:
            raise HTTPException(status_code=400, detail="Provider is required")
        
        provider = config["provider"]
        if provider not in ["azure_openai", "openai", "deepseek"]:
            raise HTTPException(status_code=400, detail="Invalid provider")
        
        # 更新环境变量
        env_updates = {}
        
        if provider == "azure_openai":
            azure_config = config.get("azure_openai", {})
            env_updates.update({
                "AZURE_API_KEY": azure_config.get("api_key", ""),
                "AZURE_API_VERSION": azure_config.get("api_version", "2024-02-15-preview"),
                "AZURE_ENDPOINT": azure_config.get("endpoint", ""),
                "AZURE_DEPLOYMENT": azure_config.get("deployment", "gpt-4o")
            })
        elif provider == "openai":
            openai_config = config.get("openai", {})
            env_updates.update({
                "OPENAI_API_KEY": openai_config.get("api_key", ""),
                "OPENAI_BASE_URL": openai_config.get("base_url", "https://api.openai.com/v1"),
                "OPENAI_MODEL": openai_config.get("model", "gpt-4o")
            })
        elif provider == "deepseek":
            deepseek_config = config.get("deepseek", {})
            env_updates.update({
                "DEEPSEEK_API_KEY": deepseek_config.get("api_key", ""),
                "DEEPSEEK_API_URL": deepseek_config.get("api_url", "https://api.deepseek.com"),
                "DEEPSEEK_MODEL": deepseek_config.get("model", "DeepSeek-V3")
            })
        
        # 更新LLM_PROVIDER
        env_updates["LLM_PROVIDER"] = provider
        
        # 保存到.env文件
        env_file_path = ".env"
        env_lines = []
        
        # 读取现有.env文件
        if os.path.exists(env_file_path):
            with open(env_file_path, 'r', encoding='utf-8') as f:
                env_lines = f.readlines()
        
        # 更新或添加配置项
        updated_keys = set()
        for i, line in enumerate(env_lines):
            if '=' in line:
                key = line.split('=')[0].strip()
                if key in env_updates:
                    env_lines[i] = f"{key}={env_updates[key]}\n"
                    updated_keys.add(key)
        
        # 添加新的配置项
        for key, value in env_updates.items():
            if key not in updated_keys:
                env_lines.append(f"{key}={value}\n")
        
        # 写入.env文件
        with open(env_file_path, 'w', encoding='utf-8') as f:
            f.writelines(env_lines)
        
        # 重新加载环境变量
        load_dotenv(override=True)
        
        # 重新初始化LLM服务
        global _global_llm_service
        _global_llm_service = None
        init_llm_service(provider)
        
        return {"message": "Model configuration saved successfully"}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error saving model config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

IMG_DIR = 'assets'
os.makedirs(IMG_DIR, exist_ok=True)  # Ensure the directory exists
@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    name = file.filename
    # No need to add '.jpg' if it's already part of the filename or not guaranteed to be jpg
    # if you want to force .jpg, you might need to handle other extensions
    # name += '.jpg' # Only add if you explicitly want to append .jpg
    if not file or not name:
        raise HTTPException(status_code=400, detail='Invalid file or name')
    
    filepath = os.path.join(IMG_DIR, name)
    try:
        # FastAPI's UploadFile has an async write method
        with open(filepath, "wb") as buffer:
            while contents := await file.read(1024 * 1024): # Read in chunks of 1MB
                buffer.write(contents)
        return {'message': 'File uploaded successfully', 'path': filepath}
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)