from utils import *
from copy import deepcopy
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import re
import json
import datetime

class Scene:
    def __init__(self, id = None, config={}):
        self.id = config.get("id", id)
        self.name = config.get("name","")
        self.info = config.get("scene","")
        self.context = config.get("characters","")
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
        }
        return state

    def load(self, config):
        # self.active_action = config.get("active_action")
        pass

    def withdraw(self, mode, player_id):
        if len(self.record) == 1:
            print("withdraw one record for -stay")
            self.record.clear()
            for _, c in self.characters.items():
                c.memory.pop()
            return 1            
        if len(self.record) >= 2:
            if mode == "v1":
                cnt = 1
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
                        c.memory.pop()
                    c.recent_memory = c.memory[-2:]
                for _ in range(cnt):
                    self.record.pop()                
                return cnt
            elif mode == "v2":
                pattern = r"(\S+)对(\S+)说"
                # 使用findall方法，查找所有匹配的内容
                matches = [item for sublist in re.findall(pattern, self.record[-2]) for item in sublist]
                matches += [item for sublist in re.findall(pattern, self.record[-1]) for item in sublist]
                # 打印提取的匹配结果
                print("matches: ", matches)
                for m in matches:
                    if m in self.characters:
                        pattern = r"(\S+)离开了对话。"
                        matches_2 = re.findall(pattern, self.characters[m].memory[-1])
                        if matches_2:
                            self.characters[m].memory.pop()
                        self.characters[m].memory.pop()
                        self.characters[m].recent_memory.pop()
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
        
    def update_record(self, a="", x="", b="", c="", y="", **kwargs):
        m = {"a": a, "x": x, "b": b, "c": c, "y": y}
        m.update(kwargs)
        self.record.append(action_to_text(m))

class World:
    def __init__(self, config={}):
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
        self.raw_records = {}
        self.narrative = ""
        if "narrative" in background:
            self.narrative = background["narrative"]
        # print("yaml_print_background", background)
        for cid, char in background.get("characters").items():    
            self.characters.update({cid: CharacterLLM(config = {"id": cid, "profile": char})})
        self.player = self.characters[background.get("player")]
        if "context" in background and isinstance(background["context"], dict):
            for cid, message in background["context"].items():
                self.characters[cid].update_memory(text = message)
        self.scene_cnt = 0
        self.add_scene("scene1")
        self.cache = CACHE_DIR
        self.mode = self.script["scenes"]["scene"+str(self.scene_cnt)]["mode"] if "mode" in self.script["scenes"]["scene"+str(self.scene_cnt)] else "v1"

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

    # def add_characters(self, char):
    #     self.characters.update({char.id: char})
    #     for sid, scene in self.scenes.items():
    #         scene.add_character(char)
    #         self.update_view(char)

    def pop_characters(self, char):
        """Remove a character from the world and its current scene."""
        self.characters.pop(char.id, None)
        if char.loc and char.loc in self.scenes:
            self.scenes[char.loc].pop_character(char)

    def add_scene(self, scene_id=None):
        """Add a new scene to the world."""
        last_scene = self.scenes[f"scene{self.scene_cnt}"] if len(self.scenes) else None
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
            trg.recent_memory.clear()
            src.recent_memory.clear()
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
                src.recent_memory.clear()
                self.characters[bid].recent_memory.clear()
                src.interact_with = self.characters[bid]
                self.characters[bid].interact_with = src
                src.interact(x, cid, **kwargs)
        scene = self.scenes[src.loc]
        scene.update_record(aid, x, bid, cid, **kwargs)

    def calculate(self, aid, x, bid=None, cid=None, **kwargs):
        print(f"calculate, aid = {aid}, x = {x}, bid = {bid}, cid = {cid}, kwargs = {kwargs}")
        if x == "-stay":
            return
        if self.mode == "v1" or self.mode == "v2":
            # assert x == "-speak"
            src = self.characters[aid]
            # print("v1_from", src.id, src.loc)
            scene = self.scenes[src.loc]
            for t in scene.characters:
                self.characters[t].update_memory(src.id, x, bid, content=kwargs["content"])
            scene.update_record(aid, x, bid, cid, **kwargs)
        elif self.mode == "v3":
            if isinstance(bid, list):
                if bid == []:
                    bid = None
                else:
                    bid = bid[0]
            self._calculate(aid, x, bid, cid, **kwargs)
        
class Character:
    def __init__(self, id=None, config={}):
        self.id = id or config.get("id")
        self.status = config.get("status", "/idle/")
        self.profile = config.get("profile", "")
        self.loc = config.get("loc", "")
        self.view = config.get("view", [])
        self.memory = config.get("memory", [])
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
            self.memory.append(kwargs["text"])
            return
        if self.id == a:
            a = "你"
        if isinstance(b, list):
            b = "、".join(["你" if character == self.id else character for character in b])
        elif b == self.id:
            b = "你"
        m = {"a": a, "x": x, "b": b, "c": c, "y": y}
        m.update(kwargs)
        self.memory.append(action_to_text(m))
        self.recent_memory.append(action_to_text(m))
        if len(self.recent_memory) > 3:
            self.recent_memory = self.recent_memory[-2:]

class CharacterLLM(Character):
    def __init__(self, id=None, config={}, query_fct=query_gpt4):
        super().__init__(id, config)
        self.query_fct = query_fct
        self.plan = []
        self.decision = []
        self.prompt = PROMPT_CHARACTER
        self.prompt_v2 = PROMPT_CHARACTER_V2
        self.cache = CACHE_DIR
        self.reacts = []
        self.interact_with = None
        self.to_do = False
        self.sum_memory = []
        self.motivation = ""

    def load(self, state):
        self.status = state["status"]
        self.loc = state["loc"]
        self.view = state["view"]
        self.memory = state["memory"]
        self.recent_memory = state["recent_memory"]
        self.motivation = state["motivation"]
        self.plan = state["plan"]

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
            "motivation": self.motivation
        }
        return state

    def act(self, narrative, info, plot = None):
        print(f"{self.id} act: {self.decision}")
        while not self.decision:
            self.make_plan(narrative, info, plot)        
        next_act = self.decision.pop(0)
        return next_act

    def log(self, content, tag):
        with open(os.path.join(self.cache, f'{self.id}_{tag}.log'), "a+", encoding = 'utf-8') as f:
            f.write(content)

    def make_plan(self, narrative, info, plot = None):
        prompt = self.prompt.format(
                    id=self.id,
                    profile=self.profile,
                    motivation=self.motivation,
                    memory=dumps(self.memory),
                    narrative = narrative,
                    scene_info = info,
                    view = dumps(self.view),
                    interact_with=self.interact_with.id if self.interact_with else "",
                    recent_memory=dumps(self.recent_memory),
                    plot=dumps(plot))

        try:
            response = self.query_fct(prompt)
            self.log("\n".join([prompt, response]), "plan")
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = [response, prompt]
        except:
            response = self.query_fct(prompt)
            self.log("\n".join([prompt, response]), "plan")
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = [response, prompt]
        plan = response["预设的情节"]
        decision = response["决策"]
        self.plan = plan
        self.decision += [decision]

    def v2(self, narrative, info, plot = None):
        prompt = self.prompt_v2.format(
            id=self.id,
            profile=self.profile,
            memory=dumps(self.memory),
            narrative = narrative,
            scene_info = info,
            view=dumps(self.view),
            motivation=self.motivation,
            recent=dumps(self.memory[-2:]),
            plot=dumps(plot)
        )
        try:
            response = self.query_fct(prompt)
            self.log("\n".join([prompt, response]), "v2")
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = [response, prompt]
        except:
            response = self.query_fct(prompt)
            self.log("\n".join([prompt, response]), "v2")
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = [response, prompt]
        plan = response["预设的情节"]
        decision = response["决策"]
        self.plan = plan
        self.decision += [decision]
        # response = self.query_fct([{"role": "user", "content": prompt}])
        # self.log("\n".join([prompt, response]), "plan")

        # response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
        # plan = response.get("当前的计划", self.plan)
        # decision = response["决策"]

        # self.plan = plan
        # self.decision += [decision]

    def interact(self, x, cid=None, **kwargs):
        if x == "-speak":
            print(f"interact, x: {x}, cid: {cid}, kwargs: {kwargs}")
            trg = self.interact_with
            trg.update_memory(self.id, "-speak", trg.id, content=kwargs["content"])
            self.update_memory(self.id, "-speak", trg.id, content=kwargs["content"])
            trg.to_do = True
            self.to_do = False            

class DramaLLM(World):
    def __init__(self, script, query_fct=query_gpt4):
        super().__init__(script)
        self.query_fct = query_fct
        self.sum_records = []
        self.reacts = []
        current_scene = self.script["scenes"]["scene"+str(self.scene_cnt)]
        self.nc = [[item, False] for item in current_scene["chain"]]
        self.prompt_v1 = PROMPT_DRAMA_V1
        self.prompt_v2 = PROMPT_DRAMA_V2
        self.mode = current_scene["mode"] if "mode" in current_scene else "v1"
        self.ready_for_next_scene = False

    @property
    def state(self):
        state = {
            "id": self.id,
            "raw_records": self.raw_records,
            "characters": {k: v.state for k, v in self.characters.items()},
            "scenes": {k: v.state for k, v in self.scenes.items()},
            "scene_cnt": self.scene_cnt,
            "script": self.script,
            "nc": self.nc
        }
        return state

    def log(self, content, tag):
        with open(os.path.join(self.cache, f'drama_{tag}.log'), "a+", encoding = 'utf-8') as f:
            f.write(content)
            
    def v1_react(self):
        all_records = sum(self.raw_records.values(), [])
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
        try:
            response = self.query_fct(prompt)
            self.log("\n".join([prompt, response]), 'v1')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v1", response]
        except:
            print("v1 react error", response)
            response = self.query_fct(prompt)
            self.log("\n".join([prompt, response]), 'v1')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v1", response]
        self.reacts.append(prompt)
        self.nc = response["当前的情节链"]
        action = response.get("决策")
        for char_id in self.characters:
            self.characters[char_id].to_do = True if char_id == action["aid"] else False
        self.characters.get(action["aid"]).decision.append(action)
        if all([t == True for _, t in self.nc]):
            self.ready_for_next_scene = True

    def v2_react(self):
        all_records = sum(self.raw_records.values(), [])
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
        try:
            response = self.query_fct(prompt)
            self.log("\n".join([prompt, response]), 'v2')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v2", response]
        except:
            print("v2 react error", response)
            response = self.query_fct(prompt)
            self.log("\n".join([prompt, response]), 'v2')
            response = json.loads(response.split("```json\n")[-1].split("\n```")[0])
            self.reacts = ["v2", response]
        self.reacts.append(prompt)
        self.nc = response["当前的情节链"]
        for char_id in self.characters:
            if char_id == response["下一个行动人"]:
                self.characters[char_id].to_do = True
                self.characters[char_id].motivation = response["行动人的指令"]
                self.characters[char_id].v2(self.narrative, self.scenes["scene"+str(self.scene_cnt)].info)
            else:
                self.characters[char_id].to_do = False
        if all([t == True for _, t in self.nc]):
            self.ready_for_next_scene = True

    def withdraw(self):
        current_scene = self.script["scenes"]["scene"+str(self.scene_cnt)]
        self.nc = [[item, False] for item in current_scene["chain"]]
        for _, char in self.characters.items():
            char.interact_with = None
            char.to_do = False
            char.decision = []
        return self.scenes["scene"+str(self.scene_cnt)].withdraw(self.mode, self.player.id)

    def back_scene(self):
        for _, char in self.characters.items():
            char.interact_with = None
            char.to_do = False
            char.decision = []
        if self.scene_cnt > 1:
            self.scene_cnt -= 1
        else:
            return
        self.mode = self.script["scenes"]["scene"+str(self.scene_cnt)]["mode"] if "mode" in self.script["scenes"]["scene"+str(self.scene_cnt)] else "v1"
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

    def next_scene(self, scene_id = None):
        for _, char in self.characters.items():
            char.interact_with = None
            char.to_do = False
        self.add_scene(scene_id)
        self.mode = self.script["scenes"]["scene"+str(self.scene_cnt)]["mode"] if "mode" in self.script["scenes"]["scene"+str(self.scene_cnt)] else "v1"
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
        if "nc" in state:
            self.nc = state["nc"]
        else:
            current_scene = self.script["scenes"]["scene"+str(self.scene_cnt)]
            self.nc = [[item, False] for item in current_scene["chain"]]
        self.mode = self.script["scenes"]["scene"+str(self.scene_cnt)]["mode"] if "mode" in self.script["scenes"]["scene"+str(self.scene_cnt)] else "v1"
