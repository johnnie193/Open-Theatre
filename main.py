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
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()
ENGLISH_MODE = bool(os.getenv("ENGLISH_MODE") and os.getenv("ENGLISH_MODE").lower() in ["true", "1", "t", "y", "yes"])

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

class LoadRequest(BaseModel):
    script_name: Optional[str] = None
    agentMode: Optional[str] = None
    playerMode: Optional[str] = None

class Action(BaseModel):
    x: str
    bid: Optional[str] = None
    content: Optional[str] = None

class InteractRequest(BaseModel):
    type: str
    message: Optional[str] = None
    object: Optional[str] = None
    interact: Optional[str] = None

class Prompt(BaseModel):
    prompt_drama_v1: str
    prompt_drama_v2: str
    prompt_character: str
    prompt_character_v2: str

class InfoRequest(BaseModel):
    role: Optional[str] = None
    help: Optional[str] = None


class DRAMA:
    def __init__(self):
        super().__init__()
        self.cache = 'cache/'

    def init(self, script):
        
        self.dramallm = DramaLLM(script=script)
        try:
            self.dramallm.update_view(self.dramallm.player.id)
        except Exception as e:
            if ENGLISH_MODE:
                return "You have to add the player into the current scene!"
            else:
                return "你需要将玩家加入当前场景!"

    def round(self, act):
        action = []
        error = None
        print("mode",self.dramallm.mode)
        while True:
            try:
                if len(act) == 3:
                    self.dramallm.calculate(self.dramallm.player.id, x = act[0], bid = act[1], content = act[2])
                elif len(act) == 1:
                    self.dramallm.calculate(self.dramallm.player.id, x = act[0])
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
                    decision.update({"aid":char_id})
                    if decision["x"] == "-speak":
                        self.dramallm.calculate(char_id, decision["x"], decision.get("bid",None), None, content=decision.get("content",None))
                    else:
                        self.dramallm.calculate(char_id, **decision)
                    action.append(decision)
                if self.dramallm.ready_for_next_scene:
                    self.dramallm.next_scene()
                break
            except Exception as e:
                error = e
                print('Caught this error: ' , error)
                print(traceback.print_exc())
        return action, self.dramallm.ready_for_next_scene, error

    def reset(self):
        self.dramallm = None

    def update(self, data):
        if hasattr(self, 'dramallm'):
            try:
                # Case II pop player
                id_list = [character['id'] for character in data["characters"]]
                for cid in self.dramallm.script["background"]["characters"]:
                    if cid not in id_list:
                        self.dramallm.pop_characters(self.dramallm.characters[cid])

                # Case I Easy modification - change world id, player name, background narrative, character profile, scene mode, scene info, scene chain, scene stream / add initial memories, add characters
                self.dramallm.id = self.dramallm.script["id"] = data["id"]
                self.dramallm.script["background"]["player"] = data["player_name"]
                self.dramallm.player = self.dramallm.characters[data["player_name"]]
                self.dramallm.narrative = self.dramallm.script["background"]["narrative"] = data["background_narrative"]
                self.dramallm.script["background"]["characters"] = {}
                self.dramallm.script["background"]["context"] = {}
                for characters in data["characters"]:
                    self.dramallm.script["background"]["characters"].update({characters["id"]:characters["profile"]})
                    if data["characters_initial_memories"][characters["id"]] and characters["id"] in self.dramallm.script["background"]["context"] and (self.dramallm.script["background"]["context"][characters["id"]] != data["characters_initial_memories"][characters["id"]]):
                        raise Exception('Initial memories changed! reload the script!')
                    else:
                        self.dramallm.script["background"]["context"].update({characters["id"]:data["characters_initial_memories"][characters["id"]]})
                    if characters["id"] not in self.dramallm.characters:
                        character = CharacterLLM(config = characters)
                        if data["characters_initial_memories"][characters["id"]]:
                            character.update_memory(message = data["characters_initial_memories"][characters["id"]])
                        self.dramallm.add_characters(character)
                    else:
                        self.dramallm.characters[characters["id"]].profile = characters["profile"]               
                if "scene"+str(self.dramallm.scene_cnt) not in data["scenes"]:
                    self.dramallm.next_scene()
                    print("current scene deletion!")

                scenes_to_delete = []
                for sid, s in self.dramallm.script["scenes"].items():
                    if sid not in data["scenes"]:
                        print(sid, "not in data")
                        scenes_to_delete.append(sid)
                        print("scene deletion!")

                for sid in scenes_to_delete:
                    self.dramallm.script["scenes"].pop(sid)

                for sid, scenes in data["scenes"].items():
                    if sid in self.dramallm.scenes: ## for the scenes have been loaded
                        if sid == "scene"+str(self.dramallm.scene_cnt):
                            self.mode = scenes["mode"]
                        self.dramallm.scenes[sid].name = scenes["sceneName"]
                        self.dramallm.scenes[sid].info = scenes["sceneInfo"]
                    self.dramallm.script["scenes"][sid]["scene"] = scenes["sceneName"]
                    self.dramallm.script["scenes"][sid]["scene"] = scenes["sceneInfo"]
                    self.dramallm.script["scenes"][sid]["chain"] = scenes["chains"]
                    self.dramallm.script["scenes"][sid]["stream"] = scenes["streams"]
                    self.dramallm.script["scenes"][sid]["characters"] = scenes["characters"]
                    self.dramallm.script["scenes"][sid]["mode"] = scenes["mode"]
                self.dramallm.mode = self.dramallm.script["scenes"]["scene"+str(self.dramallm.scene_cnt)]["mode"]
                self.dramallm.log(dumps(self.dramallm.script), "script_new")
                return
            except Exception as error:
                print('Caught this error: ' , error)
                print(traceback.print_exc())

        # Case III reload
        try:
            script = {
                "id": data["id"],
                "background": 
                    {
                        "player": data["player_name"],
                        "narrative": data["background_narrative"],
                        "characters": {},
                        "context": {}
                    },
                "scenes": {}
            }
            for characters in data["characters"]:
                script["background"]["characters"].update({characters["id"]:characters["profile"]})
                if data["characters_initial_memories"][characters["id"]]:
                    script["background"]["context"].update({characters["id"]:data["characters_initial_memories"][characters["id"]]}) 
            for sid, scenes in data["scenes"].items():
                config = {
                    "name": scenes["sceneName"],
                    "scene": scenes["sceneInfo"],
                    "chain": scenes["chains"],
                    "stream": scenes["streams"],
                    "characters": scenes["characters"],
                    "mode": scenes["mode"]
                }
                script["scenes"].update({sid: config})
            error = self.init(script)
            if error:
                return f"Initialization failure: {error}"
        except Exception as e:
            print('Caught this error: ' , e)
            print(traceback.print_exc())
            return f"Initialization failure: {e}"

    @property
    def state(self):        
        return self.dramallm.state

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
app.mount("/static", StaticFiles(directory="static"), name="static")
# 创建 DRAMA 实例
dramaworld = DRAMA()

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

@app.get("/{filename}")
async def serve_root(filename: str):
    return FileResponse(filename)

@app.get("/api/data")
async def api_data():
    return dramaworld.state

@app.post("/api/data")
async def api_data(data: ScriptData):
    return dramaworld.update(data)

@app.post("/api/load")
async def load_script(data: LoadRequest):
    """加载剧本"""
    logger.info(f"Loading script: {data.script_name}")
    postix = "_eng" if ENGLISH_MODE else ""    
    try:
        if data.script_name == 'load-script-hp':
            with open(f"script/Harry Potter and the Philosopher's Stone{postix}.yaml", encoding = 'utf-8') as file:
                script = yaml.safe_load(file)
            dramaworld.init(script)
            return dramaworld.state
        elif data.script_name == 'load-script-station':
            with open(f"script/Seven people in the waiting room{postix}.yaml", encoding = 'utf-8') as file:
                script = yaml.safe_load(file)
            dramaworld.init(script)
            return dramaworld.state
        elif data.script_name == 'load-script-romeo':
            with open(f"script/Romeo and Juliet{postix}.yaml", encoding = 'utf-8') as file:
                script = yaml.safe_load(file)
            dramaworld.init(script)
            return dramaworld.state
        else:
            match = re.match(r"load-script-(.*)", data.script_name)
            if match:
                script_id = match.group(1)
                with open(f'{dramaworld.cache}/{script_id}.yml', encoding='utf-8') as file:
                    script = yaml.safe_load(file)
                dramaworld.init(script["script"])
                dramaworld.dramallm.load(script_id)
                return dramaworld.state
        if data.agentMode:
            dramaworld.mode = data.agentMode
            return dramaworld.state
        raise HTTPException(status_code=400, detail="Invalid script name")
    except Exception as e:
        logger.error(f"Error loading script: {str(e)}")
        logger.error(traceback.print_exc(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/save")
async def save():
    if hasattr(dramaworld, 'dramallm'):
        try:
            save_id = dramaworld.dramallm.save()
            return {"info": f"Saved in {dramaworld.cache} as {save_id} successfully!", "save_id" : save_id}
        except Exception as e:
            return {"error": f"Error message: {e}"}
    else:
        return {"error": f"Save config first to create your world, then save the script file!"}

@app.post("/api/info")
async def get_info(data: InfoRequest):
    config = {
        "error": "No valid setup! "
    }
    if data.role:
        cid = data.role
        if hasattr(dramaworld, 'dramallm'):
            if cid in dramaworld.dramallm.characters:
                config = {
                    "profile": dramaworld.dramallm.characters[cid].profile,
                    "memory": dramaworld.dramallm.characters[cid].memory
                }
                if dramaworld.dramallm.mode == 'v2' or dramaworld.dramallm.mode == "v3":
                    config.update({"prompts":dramaworld.dramallm.characters[cid].reacts})
                    print(config)
    elif data.help:
        if data.help == "allmemory":
            if hasattr(dramaworld, 'dramallm'):
                config = {
                    "allmemory": dramaworld.dramallm.raw_records
                }
        elif data.help == "dramallm":
            if hasattr(dramaworld, 'dramallm'):
                config = {
                    "dramallm": dramaworld.dramallm.reacts
                }
        elif data.help == "allscript":
            if hasattr(dramaworld, 'dramallm'):
                config = {
                    "allscript": dramaworld.dramallm.script,
                    "scene_cnt": dramaworld.dramallm.scene_cnt,
                    "nc": dramaworld.dramallm.nc
                }
        elif data.help == "characters":
            if hasattr(dramaworld, 'dramallm'):
                character = get_keys(dramaworld.dramallm.script["scenes"]["scene"+str(dramaworld.dramallm.scene_cnt)]["characters"])
                filtered_char = list(filter(lambda x: x != dramaworld.dramallm.player.id, character))
                filtered_char.append("null")
                config = {
                    "characters": filtered_char
                }
        elif data.help == "export_records":
            print("exporting records")
            if hasattr(dramaworld, 'dramallm'):
                save_id = dramaworld.dramallm.id + str(datetime.datetime.now().strftime("_%m%d_%H%M%S"))
                write_json(dramaworld.dramallm.raw_records, f'{dramaworld.dramallm.cache}/records/{save_id}.yaml')
                config = {
                    "allmemory": dramaworld.dramallm.raw_records
                }                
    return config
    
@app.post("/api/interact")
async def interact(data: InteractRequest):
    start_time = time.time()
    if data.type:
        if hasattr(dramaworld, 'dramallm'):
            input_action = {"x": data.type}
            if data.type == "-stay":
                act = ["-stay"]
            elif data.type == "-speak":
                roles, message = message_to_act(data.message)
                if data.object not in roles:
                    roles.append(data.object)
                character = get_keys(dramaworld.dramallm.script["scenes"]["scene"+str(dramaworld.dramallm.scene_cnt)]["characters"])
                filtered_roles = list(filter(lambda x: x in character, roles))
                act = ["-speak", filtered_roles, message]
                input_action = {"x": data.type, "bid": act[1], "content": act[2]}
            response, done, error = dramaworld.round(act)
            if error:
                return {"error": error}
            end_time = time.time()
            print(f"Interaction took {end_time - start_time:.2f} seconds")
            return {"input": input_action,"action": response, "done": done, "state": dramaworld.state}
        else:
            return None 
    elif data.interact:
        if hasattr(dramaworld, 'dramallm'):
            if data.interact == "next":
                dramaworld.dramallm.next_scene()
                return dramaworld.dramallm.state
            elif data.interact == "back":
                dramaworld.dramallm.back_scene()
                return dramaworld.dramallm.state
            elif data.interact == "withdraw":
                cnt = dramaworld.dramallm.withdraw()
                return {"state": dramaworld.dramallm.state, "cnt": cnt}                                
        else:
            return None 
    return None 

@app.post("/api/prompt")
async def post_prompt(data: Prompt):
    postix = "_eng" if ENGLISH_MODE else ""
    if hasattr(dramaworld, 'dramallm'):
        dramaworld.dramallm.prompt_v1 = data.prompt_drama_v1
        dramaworld.dramallm.prompt_v2 = data.prompt_drama_v2
        for c, char in dramaworld.dramallm.characters.items():
            char.prompt = data.prompt_character
            char.prompt_v2 = data.prompt_character_v2
    for filename, content in [
        (f"prompt/prompt_drama_v1{postix}.md", data.prompt_drama_v1),
        (f"prompt/prompt_drama_v2{postix}.md", data.prompt_drama_v2),
        (f"prompt/prompt_character{postix}.md", data.prompt_character),
        (f"prompt/prompt_character_v2{postix}.md", data.prompt_character_v2)
    ]:
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)
    prompts = {}
    for key, filename in [
        ("prompt_drama_v1", f"prompt/prompt_drama_v1{postix}.md"),
        ("prompt_drama_v2", f"prompt/prompt_drama_v2{postix}.md"),
        ("prompt_character", f"prompt/prompt_character{postix}.md"),
        ("prompt_character_v2", f"prompt/prompt_character_v2{postix}.md"),
    ]:
        with open(filename, 'r', encoding='utf-8') as file:
            prompts[key] = file.read()
    return prompts

@app.get("/api/prompt")
async def get_prompt():
    prompts = {}
    postix = "_eng" if ENGLISH_MODE else ""
    for key, filename in [
        ("prompt_drama_v1", f"prompt/prompt_drama_v1{postix}.md"),
        ("prompt_drama_v2", f"prompt/prompt_drama_v2{postix}.md"),
        ("prompt_character", f"prompt/prompt_character{postix}.md"),
        ("prompt_character_v2", f"prompt/prompt_character_v2{postix}.md"),
    ]:
        with open(filename, 'r', encoding='utf-8') as file:
            prompts[key] = file.read()
    return prompts

IMG_DIR = 'assets'
os.makedirs(IMG_DIR, exist_ok=True)  # Ensure the directory exists
@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    name = file.filename
    name += '.jpg'
    if not file or not name:
        return {'error': 'Invalid file or name'}
    # Save the file with the provided name
    filepath = os.path.join(IMG_DIR, name)
    try:
        file.save(filepath)
        return {'message': 'File uploaded successfully', 'path': filepath}
    except Exception as e:
        return {'error': str(e)}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000) 