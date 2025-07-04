from utils import *
from copy import deepcopy
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
import json
import datetime
import asyncio
from memory.memory import MemoryStorage
from memory.base import MemoryChunk, MemoryPiece
from dotenv import load_dotenv
from models import get_llm_service

load_dotenv()
ENGLISH_MODE = bool(os.getenv("ENGLISH_MODE") and os.getenv("ENGLISH_MODE").lower() in ["true", "1", "t", "y", "yes"])
STORAGE_MODE = bool(os.getenv("STORAGE_MODE") and os.getenv("STORAGE_MODE").lower() in ["true", "1", "t", "y", "yes"])

class Scene:
    def __init__(self, id = None, config={}):
        self.id = config.get("id", id)
        self.name = config.get("name","")
        self.info = config.get("scene","")
        self.context = config.get("characters","")
        self.mode = config.get("mode","v1")
        assert self.id
        self.characters =  {}
        self.record = []

    @property
    def state(self):
        state = {
            "id": self.id,
            "name": self.name,
            "characters": {k: v.surface for k, v in self.characters.items()},
            "info": self.info,
            "mode": self.mode,
        }
        return state

    def load(self, config):
        # self.active_action = config.get("active_action")
        pass

    def withdraw(self, player_id):
        if len(self.record) == 1:
            print("withdraw one record for -stay")
            self.record.clear()
            for _, c in self.characters.items():
                c.delete_memory()
            return 1            
        if len(self.record) >= 2:
            if self.mode == "v1":
                cnt = 1
                if ENGLISH_MODE:
                    pattern1 = r"(\S+) speak to (\S+)"
                    pattern2 = r"(\S+) speak"
                else:
                    pattern1 = r"(\S+)对(\S+)说"
                    pattern2 = r"(\S+)说"

                # 使用findall方法，查找所有匹配的内容
                match = re.findall(pattern1, self.record[-2])
                print(self.record[-2])
                if match:
                    match = [match[0][0]]
                match += re.findall(pattern2, self.record[-2])
                # 打印提取的匹配结果
                print(f"matches: , {match}")
                for m in match:
                    if m == player_id:
                        cnt = 2
                for _, c in self.characters.items():
                    for _ in range(cnt):
                        c.delete_memory()
                    c.recent_memory = c.get_memory_list_from_dict()[-2:]
                for _ in range(cnt):
                    self.record.pop()                
                return cnt
            elif self.mode == "v2":
                pattern = r"(\S+)对(\S+)说" if not ENGLISH_MODE else r"(\S+) speak to (\S+)"
                # 使用findall方法，查找所有匹配的内容
                matches = [item for sublist in re.findall(pattern, self.record[-2]) for item in sublist]
                matches += [item for sublist in re.findall(pattern, self.record[-1]) for item in sublist]
                # 打印提取的匹配结果
                print("matches: ", matches)
                for m in matches:
                    if m in self.characters:
                        pattern = r"(\S+)离开了对话。" if not ENGLISH_MODE else r"(\S+) leave the conversation."
                        matches_2 = re.findall(pattern, self.characters[m].get_memory_list_from_dict()[-1])
                        if matches_2:
                            self.characters[m].delete_memory()
                        self.characters[m].delete_memory()
                        self.characters[m].delete_recent_memory()
                self.record.pop()
                self.record.pop()
                return 2

    def add_character(self, char, motivation):
        if not motivation:
            motivation = ""
        char.loc = self.id
        self.characters.update({char.id: char})
        char.motivation = motivation

    def pop_character(self, char):
        self.characters.pop(char.id)
        # if char.id in self.context:
        #     self.context.pop(char.id)
        char.loc = "W"
        # return char
        
    def update_dialogues_record(self, a="", x="", b="", c="", y="", **kwargs):
        m = {"a": a, "x": x, "b": b, "c": c, "y": y}
        m.update(kwargs)
        self.record.append(action_to_text(m))


class World:
    def __init__(self, config={}, storage_mode = STORAGE_MODE, storager = None):
        self.storage_mode = storage_mode
        self.raw_records = {}
        self.record_storage = storager

        if "scenes" in config and isinstance(config["scenes"], dict):
            for sid, s in config["scenes"].items():
                if "chain" not in config["scenes"][sid] or not config["scenes"][sid]["chain"]:
                    if "stream" in config["scenes"][sid] and config["scenes"][sid]["stream"]:
                        config["scenes"][sid].update({"chain": get_keys(config["scenes"][sid]["stream"])})
        self.script = config
        background = config.get("background")
        self.id = config.get("id")
        self.characters = {}
        self.scenes = {}
        self.narrative = ""
        if "narrative" in background:
            self.narrative = background["narrative"]
        # print("yaml_print_background", background)
        for cid, char in background.get("characters").items():    
            self.characters.update({cid: CharacterLLM(config = {"id": cid, "profile": char}, storage_mode = storage_mode)})
        self.player = self.characters[background.get("player")]
        if "context" in background and isinstance(background["context"], dict):
            for cid, message in background["context"].items():
                self.characters[cid].update_memory(text = message)
        self.scene_cnt = 0
        self.add_scene("scene1")
        self.cache = CACHE_DIR
        ## self.mode = self.script["scenes"]["scene"+str(self.scene_cnt)]["mode"] if "mode" in self.script["scenes"]["scene"+str(self.scene_cnt)] else "v1"


        # TODO: May be added when there are too many characters, so we do rag to get the relevant characters
        # if self.storage_mode:
        #     for i, char in self.characters.items():
        #         if char.profile:
        #             if ENGLISH_MODE:
        #                 self.record_storage.add_piece(f"{char.id}'s profile: {char.profile}", layer = "global", tag="profile")
        #             else:
        #                 self.record_storage.add_piece(f"{char.id}的简介: {char.profile}", layer = "global", tag="profile")

    def save(self):
        save_id = self.id+str(datetime.datetime.now().strftime("_%m%d_%H%M%S"))
        write_json(self.state, f'{self.cache}/{save_id}.yml')
        return save_id

    def load(self, save_id):
        state = read_json(f'{self.cache}/{save_id}.yml')
        if "characters" in state:
            for cid, char in state["characters"].items():
                self.characters[cid].load(char)
        if "scenes" in state:
            for sid, s in state["scenes"].items():
                self.add_scene(sid)
                self.scenes[sid].load(s)
        if "scene_cnt" in state:
            self.scene_cnt = state["scene_cnt"]
        if "raw_records" in state:
            for sid, record in state["raw_records"].items():
                self.scenes[sid].record = record
            if self.storage_mode:
                self.record_storage.reset()
                self.record_storage.load_dialogues_record(state["raw_records"], current_scene_id="scene"+str(self.scene_cnt))

    def add_characters(self, char):
        self.characters.update({char.id: char})
        for sid, scene in self.scenes.items():
            scene.add_character(char)
            self.update_view(char)

    def pop_characters(self, char):
        """Remove a character from the world and its current scene."""
        self.characters.pop(char.id, None)
        if char.loc and char.loc in self.scenes:
            self.scenes[char.loc].pop_character(char)

    def add_scene(self, scene_id=None):
        """Add a new scene to the world."""
        last_scene = self.scenes[f"scene{self.scene_cnt}"] if len(self.scenes) else None
        if self.storage_mode and last_scene:
                self.record_storage.summarize(last_scene.id)
        if not scene_id:
            scene_id = f"scene{self.scene_cnt + 1}"
            self.scene_cnt += 1
        else:
            match = re.search(r"scene(\d+)", scene_id)
            if match:
                self.scene_cnt = int(match.group(1))
            else:
                print("Error: Invalid scene ID format.")
                return

        if "scenes" not in self.script:
            return

        assert scene_id in self.script["scenes"], "Scene ID not found in script."
        scene = Scene(scene_id, self.script["scenes"][scene_id])
        self.scenes[scene.id] = scene

        if "characters" in self.script["scenes"][scene_id]:
            for cid, motivation in self.script["scenes"][scene_id]["characters"].items():
                if last_scene and cid in last_scene.characters:
                    last_scene.pop_character(self.characters[cid])
                scene.add_character(self.characters[cid], motivation)
        for cid, _ in scene.characters.items():
            self.update_view(cid)
        self.raw_records.update({scene.id: scene.record})


    @property
    def state(self):
        state = {
            "id": self.id,
            "raw_records": self.raw_records,
            "characters": {k: v.state for k, v in self.characters.items()},
            "scenes": {k: v.state for k, v in self.scenes.items()},
            "scene_cnt": self.scene_cnt,
            "script": self.script
        }
        return state

    def update_view(self, character_id):
        """Update the view for a specific character."""
        character = self.characters[character_id]
        scene = self.scenes[character.loc]
        view = {"characters": {}}
        for cid in scene.characters:
            if cid != character_id:
                view["characters"].update({cid: self.characters[cid].surface})
        character.update_view(view)

    def plan(self, action):
        if isinstance(action, dict):
            self.characters.get(action["aid"]).plan.append(action)
        for char_id in self.characters:
            self.characters[char_id].to_do = True if char_id == action["aid"] else False

    def _calculate(self, aid, x, bid=None, cid=None, **kwargs):
        src = self.characters[aid]
        if x == "-leave":
            trg = src.interact_with
            trg.update_memory(src.id, "-leave", src.interact_with.id)
            src.update_memory(src.id, "-leave", src.interact_with.id)
            trg.interact_with = None
            trg.to_do = None
            src.interact_with = None
            src.to_do = None
            trg.clear_recent_memory()
            src.clear_recent_memory()
        if x in ["-stay", "-leave"]:
            return
        if src.interact_with is not None:
            if bid is None or bid == src.interact_with.id:
                src.interact(x, cid, **kwargs)
            else:
                trg = src.interact_with
                trg.update_memory(src.id, "-leave", src.interact_with.id)
                src.update_memory(src.id, "-leave", src.interact_with.id)
                trg.interact_with = None
                trg.to_do = None
                src.interact_with = self.characters[bid]
                self.characters[bid].interact_with = src
                src.interact(x, cid, **kwargs)
        else:
            if bid is None:
                src.interact(x, cid, **kwargs)
            else:
                src.clear_recent_memory()
                self.characters[bid].clear_recent_memory()
                src.interact_with = self.characters[bid]
                self.characters[bid].interact_with = src
                src.interact(x, cid, **kwargs)
        scene = self.scenes[src.loc]
        self.update_dialogues_record(scene, aid, x, bid, cid, **kwargs)

    def calculate(self, aid, x, bid=None, cid=None, **kwargs):
        print(f"calculate, aid = {aid}, x = {x}, bid = {bid}, cid = {cid}, kwargs = {kwargs}")
        if x == "-stay":
            return
        # mode = self.script["scenes"]["scene"+str(self.scene_cnt)].get("mode","v1")
        mode = self.scenes["scene"+str(self.scene_cnt)].mode
        if mode == "v1" or mode == "v2" or mode == "v2_plus" or mode == "v2_prime":
            # assert x == "-speak"
            src = self.characters[aid]
            # print("v1_from", src.id, src.loc)
            scene = self.scenes[src.loc]
            for t in scene.characters:
                self.characters[t].update_memory(src.id, x, bid, content=kwargs["content"])
            self.update_dialogues_record(scene, aid, x, bid, cid, **kwargs)
        elif mode == "v3":
            if isinstance(bid, list):
                if bid == []:
                    bid = None
                else:
                    bid = bid[0]
            self._calculate(aid, x, bid, cid, **kwargs)

    def update_dialogues_record(self, scene, a="", x="", b="", c="", y="", **kwargs):
        # m = {"a": a, "x": x, "b": b, "c": c, "y": y}
        # m.update(kwargs)
        # scene.record.append(action_to_text(m))
        if self.storage_mode:
            m = {"a": a, "x": x, "b": b, "c": c, "y": y}
            m.update(kwargs)
            self.record_storage.add_piece(action_to_text(m), layer = "event", tag="conversation", scene_id=scene.id)
        scene.update_dialogues_record(a, x, b, c, y, **kwargs)
            
            
class Character:
    def __init__(self, id=None, config={}):
        self.id = id or config.get("id")
        self.status = config.get("status", "/idle/")
        self.profile = config.get("profile", "")
        self.loc = config.get("loc", "")
        self.view = config.get("view", [])
        self.memory = config.get("memory", {})
        self.recent_memory = config.get("recent_memory", [])

    @property
    def surface(self):
        """Return a simplified state of the character."""
        return {
            "id": self.id,
            "status": self.status,
            "loc": self.loc,
            "profile": self.profile,
            "interact_with": self.interact_with.id if self.interact_with else None,
        }

    @property
    def state(self):
        state = {
            "id": self.id,
            "status": self.status,
            "loc": self.loc,
            "view": self.view,
            "memory": self.memory,
            "recent_memory": self.recent_memory,
            "profile": self.profile,
            "interact_with": self.interact_with.id if self.interact_with else None,
        }
        return state
    
    def load(self, state):
        self.status = state["status"]
        self.loc = state["loc"]
        self.view = state["view"]
        self.memory = state["memory"]
        self.recent_memory = state["recent_memory"]
        self.profile = state["profile"]

    def update_view(self, view):
        """Update the character's view based on the current scene."""
        self.view.clear()
        for v in view["characters"].values():
            self.view.append(observation_to_text(v, self.id))

    def get_available_acts(self):
        pass

    def update_memory(self, a="", x="", b="", c="", y="", **kwargs):
        """Update the character's memory with a new action."""
        if self.status == "/faint/":
            return
        if kwargs.get("text"):
            if self.loc not in self.memory:
                self.memory.update({self.loc: [kwargs["text"]]})
            else:
                self.memory[self.loc].append(kwargs["text"])
            return
        if self.id == a:
            a = "你" if not ENGLISH_MODE else "you"
        if isinstance(b, list):
            b = "、".join(["你" if character == self.id else character for character in b]) if not ENGLISH_MODE else "、".join(["you" if character == self.id else character for character in b])
        elif b == self.id:
            b = "你" if not ENGLISH_MODE else "you"
        m = {"a": a, "x": x, "b": b, "c": c, "y": y}
        m.update(kwargs)
        if self.loc not in self.memory:
            self.memory.update({self.loc: [action_to_text(m)]})
        else:
            self.memory[self.loc].append(action_to_text(m))
        self.recent_memory.append(action_to_text(m))
        if len(self.recent_memory) > 3:
            self.recent_memory = self.recent_memory[-2:]

    def delete_memory(self, text=None):
        if text is None:
            # self.storage.delete_piece(self.id)
            if self.loc in self.memory:
                self.memory[self.loc].pop()
            else:
                self.memory.update({self.loc: []})
                logger.warning(f"Character {self.id} has no memory for scene {self.loc}")
        else:
            # self.storage.delete_piece(self.id, text)
            self.memory[self.loc] = [m for m in self.memory[self.loc] if m != text]

    def delete_recent_memory(self, text=None):
        if text is None:
            self.recent_memory.pop()
        else:
            self.recent_memory = [m for m in self.recent_memory if m != text]

    def clear_memory(self):
        self.recent_memory = []
        self.memory = {}

    def clear_recent_memory(self):
        self.recent_memory = []

class CharacterLLM(Character):
    def __init__(self, id=None, config={}, storage_mode=STORAGE_MODE, retrieve_threshold=5):
        super().__init__(id, config)
        self.plan = []
        self.decision = []
        self.prompt = PROMPT_CHARACTER
        self.prompt_v2 = PROMPT_CHARACTER_V2
        self.cache = CACHE_DIR
        self.reacts = []
        self.interact_with = None
        self.to_do = False
        self.motivation = ""
        self.memory = {}
        
        self.storage_mode = storage_mode
        self.storage = MemoryStorage()
        self.retrieve_threshold = retrieve_threshold
        self.last_retrieved = []

    def clear_memory(self):
        self.recent_memory = []
        if self.storage_mode:
            self.storage.reset()
        self.memory = {}


    def load(self, state):
        self.status = state["status"]
        self.loc = state["loc"]
        self.view = state["view"]
        self.memory = state["memory"]
        self.recent_memory = state["recent_memory"]
        self.motivation = state["motivation"]
        self.plan = state["plan"]
        if self.storage_mode:
            self.storage.reset()
            self.storage.load_dialogues_record(state["raw_records"], current_scene_id=self.loc)

    @property
    def state(self):
        state = {
            "id": self.id,
            "status": self.status,
            "loc": self.loc,
            "view": self.view,
            "interact_with": self.interact_with.id if self.interact_with else None,
            "memory": self.memory,
            "recent_memory": self.recent_memory,
            "plan": self.plan,
            "profile": self.profile,
            "motivation": self.motivation,
            "chunks": self.storage.all_chunks_values(),
            "last_retrieved": self.last_retrieved
        }
        return state
    
    def get_memory_list_from_dict(self):
        memory_dict = self.memory
        if len(self.loc.split("scene")) >= 2:
            cnt = self.loc.split("scene")[1]
        else:
            logger.warning(f"Character {self.id} is not here.")
            return []
        memory_list = []
        for i in range(int(cnt)): # from 0 to cnt-1
            scene_id = "scene"+str(i+1)
            if scene_id in memory_dict:
                memory_list.extend(memory_dict[scene_id])
        return memory_list

    def get_memory(self, query=None, scene_id=None):
        if self.storage_mode and len(self.get_memory_list_from_dict()) >= self.retrieve_threshold:
            if not query:
                query = self.get_memory_list_from_dict()[-1]
            retrieved = self.storage.retrieve(query, ["event"], scene_id)
            self.last_retrieved = []
            records = "The script records are too long, so we get some chunks which may be relevant to the current dialogues from the record storage.\n"
            for _, last_list in retrieved.items():
                records += "\n\nChunk:"
                for last in last_list:
                    self.last_retrieved.append({"Score": last['score'], "Info": last["chunk"].text})
                    records += f"\n{last['chunk'].to_text()}"
            return records
        return dumps(self.get_memory_list_from_dict())
        
    def into_memory(self, text, layer="event", tag=""):
        if self.storage_mode:
            self.storage.add_piece(f"{self.id} 's {tag} memory: {text}", layer = layer, tag = tag, scene_id = self.loc)
        if self.loc not in self.memory:
            self.memory.update({self.loc: [text]})
        else:
            self.memory[self.loc].append(text)

    def act(self, narrative, info, scene_id=None, plot = None):
        print(f"{self.id} act: {self.decision}")
        while not self.decision:
            self.make_plan(narrative=narrative, info=info, scene_id=scene_id,plot=plot)        
        next_act = self.decision.pop(0)
        return next_act

    def log(self, content, tag):
        with open(os.path.join(self.cache, f'{self.id}_{tag}.log'), "a+", encoding = 'utf-8') as f:
            f.write(content)


    def update_memory(self, a="", x="", b="", c="", y="", **kwargs):
        """Update the character's memory with a new action."""
        if self.status == "/faint/":
            return
        if kwargs.get("text"):
            self.into_memory(kwargs["text"])
            return
        if self.id == a:
            a = "你" if not ENGLISH_MODE else "you"
        if isinstance(b, list):
            if ENGLISH_MODE:
                b = "、".join(["you" if character == self.id else character for character in b])
            else:
                b = ",".join(["你" if character == self.id else character for character in b])
        elif b == self.id:
            b = "你" if not ENGLISH_MODE else "you"
        m = {"a": a, "x": x, "b": b, "c": c, "y": y}
        m.update(kwargs)
        self.into_memory(action_to_text(m))
        self.recent_memory.append(action_to_text(m))
        if len(self.recent_memory) > 3:
            self.recent_memory = self.recent_memory[-2:]

    def make_plan(self, narrative, info, scene_id=None, plot = None):
        prompt = self.prompt.format(
                    id=self.id,
                    profile=self.profile,
                    motivation=self.motivation,
                    memory=self.get_memory(scene_id=scene_id),
                    narrative = narrative,
                    scene_info = info,
                    view = dumps(self.view),
                    interact_with=self.interact_with.id if self.interact_with else "",
                    recent_memory=dumps(self.recent_memory),
                    plot=dumps(plot))

        try:
            response = get_llm_service().query(prompt)
            self.log("\n".join([prompt, response]), "plan")
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = [response, prompt]
        except:
            response = get_llm_service().query(prompt)
            self.log("\n".join([prompt, response]), "plan")
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = [response, prompt]
        plan = response["预设的情节"] if not ENGLISH_MODE else response["Preset Plot"]
        decision = response["决策"] if not ENGLISH_MODE else response["Decision"]
        self.plan = plan
        self.decision += [decision]

    def v2(self, narrative, info, scene_id=None, plot = None):
        prompt = self.prompt_v2.format(
            id=self.id,
            profile=self.profile,
            memory=self.get_memory(scene_id=scene_id),
            narrative = narrative,
            scene_info = info,
            view=dumps(self.view),
            motivation=self.motivation,
            recent=dumps(self.recent_memory),
            plot=dumps(plot)
        )
        try:
            response = get_llm_service().query(prompt)
            self.log("\n".join([prompt, response]), "v2")
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = [response, prompt]
        except:
            response = get_llm_service().query(prompt)
            self.log("\n".join([prompt, response]), "v2")
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = [response, prompt]
        plan = response["预设的情节"] if not ENGLISH_MODE else response["Preset Plot"]
        decision = response["决策"] if not ENGLISH_MODE else response["Decision"]
        self.plan = plan
        self.decision += [decision]

    async def av2(self, narrative, info, scene_id=None, plot = None):
        """异步版本的v2方法"""
        prompt = self.prompt_v2.format(
            id=self.id,
            profile=self.profile,
            memory=self.get_memory(scene_id=scene_id),
            narrative = narrative,
            scene_info = info,
            view=dumps(self.view),
            motivation=self.motivation,
            recent=dumps(self.recent_memory),
            plot=dumps(plot)
        )
        try:
            response = await get_llm_service().aquery(prompt)
            self.log("\n".join([prompt, response]), "av2")
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = [response, prompt]
        except:
            response = await get_llm_service().aquery(prompt)
            self.log("\n".join([prompt, response]), "av2")
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = [response, prompt]
        plan = response["预设的情节"] if not ENGLISH_MODE else response["Preset Plot"]
        decision = response["决策"] if not ENGLISH_MODE else response["Decision"]
        self.plan = plan
        self.decision += [decision]

    def interact(self, x, cid=None, **kwargs):
        if x == "-speak":
            print(f"interact, x: {x}, cid: {cid}, kwargs: {kwargs}")
            trg = self.interact_with
            trg.update_memory(self.id, "-speak", trg.id, content=kwargs["content"])
            self.update_memory(self.id, "-speak", trg.id, content=kwargs["content"])
            trg.to_do = True
            self.to_do = False            

class DramaLLM(World):
    def __init__(self, script, storage_mode = False, storager = MemoryStorage(), retrieve_threshold=5):
        super().__init__(script, storage_mode, storager)
        self.sum_records = []
        self.reacts = []
        current_scene = self.script["scenes"]["scene"+str(self.scene_cnt)]
        self.nc = [[item, False] for item in current_scene["chain"]]
        self.prompt_v1 = PROMPT_DRAMA_V1
        self.prompt_v2 = PROMPT_DRAMA_V2
        self.prompt_v2_plus = PROMPT_DRAMA_V2_PLUS
        self.prompt_global_character = PROMPT_GLOBAL_CHARACTER
        self.mode = current_scene["mode"] if "mode" in current_scene else "v1"
        self.ready_for_next_scene = False
        self.last_retrieved = []
        self.retrieve_threshold = retrieve_threshold

    @property
    def state(self):
        state = {
            "id": self.id,
            "player_name": self.player.id,
            "background_narrative": self.narrative,
            "raw_records": self.raw_records,
            "characters": {k: v.state for k, v in self.characters.items()},
            "scenes": {k: v.state for k, v in self.scenes.items()},
            "scene_cnt": self.scene_cnt,
            "script": self.script,
            "nc": self.nc,
            "chunks": self.record_storage.all_chunks_values(),
            "last_retrieved": self.last_retrieved,
        }
        return state

    def log(self, content, tag):
        with open(os.path.join(self.cache, f'drama_{tag}.log'), "a+", encoding = 'utf-8') as f:
            f.write(content)
            
    def v1_react(self):
        all_records = sum(self.raw_records.values(), [])
        # logger.info(f"storage {self.storage_mode}, records {len(all_records)}, {self.retrieve_threshold}")
        if not self.storage_mode or len(all_records) < self.retrieve_threshold:
            prompt = self.prompt_v1.format(
                narrative = self.narrative,
                npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
                player_id=self.player.id,
                player_profile = self.player.profile,
                script = dump_script(self.script["scenes"], self.scene_cnt),
                scene_id = "scene"+str(self.scene_cnt),
                nc = self.nc,
                records = "\n".join([line for line in all_records]),
                recent = "\n".join([line for line in all_records[-2:]]),
            )
        else:
            # do rag to get the relevant records
            retrieved = self.record_storage.retrieve(all_records[-1], ["event"], "scene"+str(self.scene_cnt))
            self.last_retrieved = []
            records = "The script records are too long, so we get some chunks which may be relevant to the current dialogues from the record storage.\n"
            for _, last_list in retrieved.items():
                records += "\n\nChunk:"
                for last in last_list:
                    self.last_retrieved.append({"Score": last['score'], "Info": last["chunk"].text})
                    records += f"\n{last['chunk'].to_text()}"
            # logger.info(f"last retrieve {self.last_retrieved}")
            
            prompt = self.prompt_v1.format(
                narrative = self.narrative,
                npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
                player_id=self.player.id,
                player_profile = self.player.profile,
                script = dump_script(self.script["scenes"], self.scene_cnt),
                scene_id = "scene"+str(self.scene_cnt),
                nc = self.nc,
                records = records,
                recent = "\n".join([line for line in all_records[-2:]]),
            )
    
        try:
            response = get_llm_service().query(prompt)
            self.log("\n".join([prompt, response]), 'v1')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v1", response]
        except:
            print("v1 react error", response)
            response = get_llm_service().query(prompt)
            self.log("\n".join([prompt, response]), 'v1')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v1", response]
        self.reacts.append(prompt)
        if ENGLISH_MODE:
            self.nc = response["Chain"]
            action = response.get("Decision")
        else:
            self.nc = response["当前的情节链"]
            action = response.get("决策")
        for char_id in self.characters:
            self.characters[char_id].to_do = True if char_id == action["aid"] else False
        # logger.info(f"next action: {action["aid"]}")
        self.characters.get(action["aid"]).decision.append(action)
        if all([t == True for _, t in self.nc]):
            self.ready_for_next_scene = True

    def v2_react(self):
        all_records = sum(self.raw_records.values(), [])
        if not self.storage_mode or len(all_records) < self.retrieve_threshold:
            prompt = self.prompt_v2.format(
                narrative = self.narrative,
                npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
                player_id=self.player.id,
                player_profile = self.player.profile,
                script = dump_script(self.script["scenes"], self.scene_cnt),
                scene_id = "scene"+str(self.scene_cnt),
                nc = self.nc,
                records = "\n".join([line for line in all_records]),
                recent = "\n".join([line for line in all_records[-2:]]),
            )
        else:
            # do rag to get the relevant records
            retrieved = self.record_storage.retrieve(all_records[-1], ["event"], "scene"+str(self.scene_cnt))
            self.last_retrieved = []
            records = "The script records are too long, so we get some chunks which may be relevant to the current dialogues from the record storage.\n"
            for _, last_list in retrieved.items():
                records += "\n\nChunk:"
                for last in last_list:
                    self.last_retrieved.append({"Score": last['score'], "Info": last["chunk"].text})
                    records += f"\n{last['chunk'].to_text()}"
            # logger.info(f"last retrieve {self.last_retrieved}")

            prompt = self.prompt_v2.format(
                narrative = self.narrative,
                npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
                player_id=self.player.id,
                player_profile = self.player.profile,
                script = dump_script(self.script["scenes"], self.scene_cnt),
                scene_id = "scene"+str(self.scene_cnt),
                nc = self.nc,
                records = records,
                recent = "\n".join([line for line in all_records[-2:]]),
            )
        try:
            response = get_llm_service().query(prompt)
            self.log("\n".join([prompt, response]), 'v2')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v2", response]
        except:
            print("v2 react error", response)
            response = get_llm_service().query(prompt)
            self.log("\n".join([prompt, response]), 'v2')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v2", response]
        self.reacts.append(prompt)
        self.nc = response["当前的情节链"] if not ENGLISH_MODE else response["Chain"]
        for char_id in self.characters:
            if (not ENGLISH_MODE and char_id == response["下一个行动人"]) or (ENGLISH_MODE and char_id == response["Next Action Character"]) :
                self.characters[char_id].to_do = True
                self.characters[char_id].motivation = response["行动人的指令"] if not ENGLISH_MODE else response["Action Character's Instruction"]
                self.characters[char_id].v2(self.narrative, self.scenes["scene"+str(self.scene_cnt)].info, scene_id="scene"+str(self.scene_cnt))
            else:
                self.characters[char_id].to_do = False
        if all([t == True for _, t in self.nc]):
            self.ready_for_next_scene = True

    def v2_plus_react(self):
        all_records = sum(self.raw_records.values(), [])
        if not self.storage_mode or len(all_records) < self.retrieve_threshold:
            prompt = self.prompt_v2_plus.format(
                narrative = self.narrative,
                npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
                player_id=self.player.id,
                player_profile = self.player.profile,
                script = dump_script(self.script["scenes"], self.scene_cnt),
                scene_id = "scene"+str(self.scene_cnt),
                nc = self.nc,
                records = "\n".join([line for line in all_records]),
                recent = "\n".join([line for line in all_records[-2:]]),
            )
        else:
            # do rag to get the relevant records
            retrieved = self.record_storage.retrieve(all_records[-1], ["event"], "scene"+str(self.scene_cnt))
            self.last_retrieved = []
            records = "The script records are too long, so we get some chunks which may be relevant to the current dialogues from the record storage.\n"
            for _, last_list in retrieved.items():
                records += "\n\nChunk:"
                for last in last_list:
                    self.last_retrieved.append({"Score": last['score'], "Info": last["chunk"].text})
                    records += f"\n{last['chunk'].to_text()}"
            
            prompt = self.prompt_v2_plus.format(
                narrative = self.narrative,
                npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
                player_id=self.player.id,
                player_profile = self.player.profile,
                script = dump_script(self.script["scenes"], self.scene_cnt),
                scene_id = "scene"+str(self.scene_cnt),
                nc = self.nc,
                records = records,
                recent = "\n".join([line for line in all_records[-2:]]),
            )
        try:
            response = get_llm_service().query(prompt)
            self.log("\n".join([prompt, response]), 'v2_plus')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v2_plus", response]
        except:
            print("v2_plus react error", response)
            response = get_llm_service().query(prompt)
            self.log("\n".join([prompt, response]), 'v2_plus')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v2_plus", response]
        self.reacts.append(prompt)
        self.nc = response["当前的情节链"] if not ENGLISH_MODE else response["Current Plot Chain"]

        # Reset all characters to not active
        for char_id in self.characters:
            self.characters[char_id].to_do = False

        # Process multiple actors from the response with async parallel calls
        actor_list_key = "行动人列表" if not ENGLISH_MODE else "Actor List"
        if actor_list_key in response:
            for actor_info in response[actor_list_key]:
                char_name_key = "角色" if not ENGLISH_MODE else "Character"
                instruction_key = "指令" if not ENGLISH_MODE else "Instruction"

                char_name = actor_info.get(char_name_key)
                instruction = actor_info.get(instruction_key)

                if char_name in self.characters:
                    self.characters[char_name].to_do = True
                    self.characters[char_name].motivation = instruction
                    self.characters[char_name].v2(
                        self.narrative,
                        self.scenes["scene"+str(self.scene_cnt)].info,
                        scene_id="scene"+str(self.scene_cnt)
                    )

        if all([t == True for _, t in self.nc]):
            self.ready_for_next_scene = True

    async def av2_plus_react(self):
        """异步版本的v2_plus_react，支持并行处理多个角色"""
        all_records = sum(self.raw_records.values(), [])
        if not self.storage_mode or len(all_records) < self.retrieve_threshold:
            prompt = self.prompt_v2_plus.format(
                narrative = self.narrative,
                npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
                player_id=self.player.id,
                player_profile = self.player.profile,
                script = dump_script(self.script["scenes"], self.scene_cnt),
                scene_id = "scene"+str(self.scene_cnt),
                nc = self.nc,
                records = "\n".join([line for line in all_records]),
                recent = "\n".join([line for line in all_records[-2:]]),
            )
        else:
            # do rag to get the relevant records
            retrieved = self.record_storage.retrieve(all_records[-1], ["event"], "scene"+str(self.scene_cnt))
            self.last_retrieved = []
            records = "The script records are too long, so we get some chunks which may be relevant to the current dialogues from the record storage.\n"
            for _, last_list in retrieved.items():
                records += "\n\nChunk:"
                for last in last_list:
                    self.last_retrieved.append({"Score": last['score'], "Info": last["chunk"].text})
                    records += f"\n{last['chunk'].to_text()}"
            
            prompt = self.prompt_v2_plus.format(
                narrative = self.narrative,
                npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
                player_id=self.player.id,
                player_profile = self.player.profile,
                script = dump_script(self.script["scenes"], self.scene_cnt),
                scene_id = "scene"+str(self.scene_cnt),
                nc = self.nc,
                records = records,
                recent = "\n".join([line for line in all_records[-2:]]),
            )
        try:
            response = await get_llm_service().aquery(prompt)
            self.log("\n".join([prompt, response]), 'av2_plus')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v2_plus", response]
        except:
            print("av2_plus react error", response)
            response = await get_llm_service().aquery(prompt)
            self.log("\n".join([prompt, response]), 'av2_plus')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v2_plus", response]
        self.reacts.append(prompt)
        self.nc = response["当前的情节链"] if not ENGLISH_MODE else response["Current Plot Chain"]

        # Reset all characters to not active
        for char_id in self.characters:
            self.characters[char_id].to_do = False

        # Process multiple actors from the response with async parallel calls
        actor_list_key = "行动人列表" if not ENGLISH_MODE else "Actor List"
        if actor_list_key in response:
            # Prepare tasks for parallel execution
            tasks = []

            for actor_info in response[actor_list_key]:
                char_name_key = "角色" if not ENGLISH_MODE else "Character"
                instruction_key = "指令" if not ENGLISH_MODE else "Instruction"

                char_name = actor_info.get(char_name_key)
                instruction = actor_info.get(instruction_key)

                if char_name in self.characters:
                    self.characters[char_name].to_do = True
                    self.characters[char_name].motivation = instruction

                    # Create async task for this character
                    task = self.characters[char_name].av2(
                        self.narrative,
                        self.scenes["scene"+str(self.scene_cnt)].info,
                        scene_id="scene"+str(self.scene_cnt)
                    )
                    tasks.append(task)

            # Execute all character v2 calls in parallel
            if tasks:
                await asyncio.gather(*tasks)

        if all([t == True for _, t in self.nc]):
            self.ready_for_next_scene = True

    def v2_prime_react(self):
        # First, get director instructions using v2_plus prompt
        # director_prompt = self.prompt_v2_plus.format(
        #     narrative = self.narrative,
        #     npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
        #     player_id=self.player.id,
        #     player_profile = self.player.profile,
        #     script = dump_script(self.script["scenes"], self.scene_cnt),
        #     scene_id = "scene"+str(self.scene_cnt),
        #     nc = self.nc,
        #     records = "\n".join([line for line in all_records]),
        #     recent = "\n".join([line for line in all_records[-2:]]),
        # )
        all_records = sum(self.raw_records.values(), [])
        if not self.storage_mode or len(all_records) < self.retrieve_threshold:
            director_prompt = self.prompt_v2_plus.format(
                narrative = self.narrative,
                npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
                player_id=self.player.id,
                player_profile = self.player.profile,
                script = dump_script(self.script["scenes"], self.scene_cnt),
                scene_id = "scene"+str(self.scene_cnt),
                nc = self.nc,
                records = "\n".join([line for line in all_records]),
                recent = "\n".join([line for line in all_records[-2:]]),
            )
        else:
            # do rag to get the relevant records
            retrieved = self.record_storage.retrieve(all_records[-1], ["event"], "scene"+str(self.scene_cnt))
            self.last_retrieved = []
            records = "The script records are too long, so we get some chunks which may be relevant to the current dialogues from the record storage.\n"
            for _, last_list in retrieved.items():
                records += "\n\nChunk:"
                for last in last_list:
                    self.last_retrieved.append({"Score": last['score'], "Info": last["chunk"].text})
                    records += f"\n{last['chunk'].to_text()}"
            
            director_prompt = self.prompt_v2_plus.format(
                narrative = self.narrative,
                npcs="\n\n".join(["\n".join([char_id, char.profile, char.motivation]) for char_id, char in self.characters.items() if char_id != self.player.id]),
                player_id=self.player.id,
                player_profile = self.player.profile,
                script = dump_script(self.script["scenes"], self.scene_cnt),
                scene_id = "scene"+str(self.scene_cnt),
                nc = self.nc,
                records = records,
                recent = "\n".join([line for line in all_records[-2:]]),
            )
        try:
            director_response = get_llm_service().query(director_prompt)
            self.log("\n".join([director_prompt, director_response]), 'v2_prime_director')
            director_response = json.loads(director_response.split("```json\n")[-1].split("\n```")[0])
        except:
            print("v2_prime director react error", director_response)
            director_response = get_llm_service().query(director_prompt)
            self.log("\n".join([director_prompt, director_response]), 'v2_prime_director')
            director_response = json.loads(director_response.split("```json\n")[-1].split("\n```")[0])

        self.nc = director_response["当前的情节链"] if not ENGLISH_MODE else director_response["Current Plot Chain"]

        # Get actor list from director response
        actor_list_key = "行动人列表" if not ENGLISH_MODE else "Actor List"
        if actor_list_key not in director_response:
            return

        # Prepare global character prompt
        all_characters_info = []
        all_memories_info = []
        director_instructions = []

        for char_id, char in self.scenes["scene"+str(self.scene_cnt)].characters.items():
            if char_id != self.player.id:
                all_characters_info.append(f"**{char_id}**: {char.profile}")
                scene_key = "scene" + str(self.scene_cnt)
                memory_content = char.get_memory(scene_id=scene_key)
                memory_info = f"**{char_id}的记忆**: {memory_content}" if not ENGLISH_MODE else f"**{char_id}'s memory**: {memory_content}"
                all_memories_info.append(memory_info)

        for actor_info in director_response[actor_list_key]:
            char_name_key = "角色" if not ENGLISH_MODE else "Character"
            instruction_key = "指令" if not ENGLISH_MODE else "Instruction"
            char_name = actor_info.get(char_name_key)
            instruction = actor_info.get(instruction_key)
            director_instructions.append(f"**{char_name}**: {instruction}")

        global_prompt = self.prompt_global_character.format(
            narrative = self.narrative,
            scene_info = self.scenes["scene"+str(self.scene_cnt)].info,
            all_characters = "\n".join(all_characters_info),
            all_memories = "\n".join(all_memories_info),
            recent_memory = "\n".join([line for line in all_records[-5:]]),
            director_instructions = "\n".join(director_instructions)
        )

        try:
            global_response = get_llm_service().query(global_prompt)
            self.log("\n".join([global_prompt, global_response]), 'v2_prime_global')
            global_response = json.loads(global_response.split("```json\n")[-1].split("\n```")[0])
            all_response = f"Director: {json.dumps(director_response, ensure_ascii=False)}\nGlobal Character: {json.dumps(global_response, ensure_ascii=False)}"
            self.reacts = ["v2_prime", all_response]
        except:
            print("v2_prime global react error", global_response)
            global_response = get_llm_service().query(global_prompt)
            self.log("\n".join([global_prompt, global_response]), 'v2_prime_global')
            global_response = json.loads(global_response.split("```json\n")[-1].split("\n```")[0])
            all_response = f"Director: {json.dumps(director_response, ensure_ascii=False)}\nGlobal Character: {json.dumps(global_response, ensure_ascii=False)}"
            self.reacts = ["v2_prime", all_response]
        all_prompt = f"Director: {director_prompt}\nGlobal Character: {global_prompt}"
        self.reacts.append(all_prompt)
        # Reset all characters to not active
        for char_id in self.characters:
            self.characters[char_id].to_do = False

        # Process actions from global character response
        action_list_key = "行动列表" if not ENGLISH_MODE else "Action List"
        if action_list_key in global_response:
            for action_info in global_response[action_list_key]:
                char_name_key = "角色" if not ENGLISH_MODE else "Character"
                action_key = "行动" if not ENGLISH_MODE else "Action"

                char_name = action_info.get(char_name_key)
                action = action_info.get(action_key)

                if char_name in self.characters:
                    self.characters[char_name].to_do = True
                    self.characters[char_name].decision.append(action)

        if all([t == True for _, t in self.nc]):
            self.ready_for_next_scene = True

    def withdraw(self):
        current_scene = self.script["scenes"]["scene"+str(self.scene_cnt)]
        self.nc = [[item, False] for item in current_scene["chain"]]
        for _, char in self.characters.items():
            char.interact_with = None
            char.to_do = False
            char.decision = []
        ans = self.scenes["scene"+str(self.scene_cnt)].withdraw(self.player.id)
        if self.storage_mode:
            self.record_storage.reset()
            self.record_storage.load_dialogues_record(self.raw_records, current_scene_id=self.loc)
        return ans

    def back_scene(self):
        for _, char in self.characters.items():
            char.interact_with = None
            char.to_do = False
            char.decision = []
        if self.scene_cnt > 1:
            self.scene_cnt -= 1
        else:
            return
        self.mode = self.script["scenes"]["scene"+str(self.scene_cnt)]["mode"]
        if isinstance(self.script["scenes"]["scene"+str(self.scene_cnt)]["chain"], list):
            self.nc = [[item, False] for item in self.script["scenes"]["scene"+str(self.scene_cnt)]["chain"]]
        self.ready_for_next_scene = False
        if "characters" in self.script["scenes"]["scene"+str(self.scene_cnt)]:
            character_list = self.script["scenes"]["scene"+str(self.scene_cnt)]["characters"]
            for cid, motivation in character_list.items():
                if self.characters[cid].loc != self.id:
                    self.scenes[self.characters[cid].loc].pop_character(self.characters[cid])
                    self.scenes["scene"+str(self.scene_cnt)].add_character(self.characters[cid], motivation)
            for cid, motivation in character_list.items():
                self.update_view(cid)
        if self.storage_mode:
            self.record_storage.reset()
            self.record_storage.load_dialogues_record(self.raw_records, current_scene_id="scene"+str(self.scene_cnt))


    def next_scene(self, scene_id = None):
        for _, char in self.characters.items():
            char.interact_with = None
            char.to_do = False
        self.add_scene(scene_id)
        self.mode = self.script["scenes"]["scene"+str(self.scene_cnt)]["mode"]
        if isinstance(self.script["scenes"]["scene"+str(self.scene_cnt)]["chain"], list):
            self.nc = [[item, False] for item in self.script["scenes"]["scene"+str(self.scene_cnt)]["chain"]]
        self.ready_for_next_scene = False

    def save(self):
        save_id = self.id+str(datetime.datetime.now().strftime("_%m%d_%H%M%S"))
        write_json(self.state, f'{self.cache}/{save_id}.yml')
        return save_id

    def load(self, save_id):
        state = read_json(f'{self.cache}/{save_id}.yml')
        if "characters" in state:
            for cid, char in state["characters"].items():
                self.characters[cid].load(char)
                self.characters[cid].interact_with = self.characters[char.get("interact_with")] if char.get("interact_with") in self.characters else None
        if "scenes" in state:
            for sid, s in state["scenes"].items():
                self.add_scene(sid)
                self.scenes[sid].load(s)
        if "scene_cnt" in state:
            self.scene_cnt = state["scene_cnt"]
        if "raw_records" in state:
            for sid, record in state["raw_records"].items():
                self.raw_records[sid] = self.scenes[sid].record = record
            if self.storage_mode:
                self.record_storage.reset()
                self.record_storage.load_dialogues_record(state["raw_records"], current_scene_id="scene"+str(self.scene_cnt))

        if "nc" in state:
            self.nc = state["nc"]
        else:
            current_scene = self.script["scenes"]["scene"+str(self.scene_cnt)]
            self.nc = [[item, False] for item in current_scene["chain"]]
        self.mode = self.scenes["scene"+str(self.scene_cnt)].mode

