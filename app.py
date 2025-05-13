import traceback
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import yaml
from frame import *
import time

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


app = Flask(__name__)
CORS(app)  
dramaworld = DRAMA()

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html') 

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/components/<path:filename>')
def serve_components(filename):
    return send_from_directory('components', filename)

@app.route('/<path:filename>')
def serve_root(filename):
    return send_from_directory('.', filename)

@app.route('/api/data', methods=['GET', 'POST'])
def api_data():
    if request.method == 'POST':
        data = request.json
        error = dramaworld.update(data)
        if error:
            return jsonify({"error": error})
        # return jsonify(response) 
    return jsonify(dramaworld.state), 200

@app.route('/load', methods=['POST'])
def load():
    data = request.json
    if data.get('script_name') == 'load-script-hp':
        with open("script/Harry Potter and the Philosopher's Stone.yaml", encoding = 'utf-8') as file:
            script = yaml.safe_load(file)
        dramaworld.init(script)
        return jsonify(dramaworld.state), 200
    elif data.get('script_name') == 'load-script-station':
        with open("script/Seven people in the waiting room.yaml", encoding = 'utf-8') as file:
            script = yaml.safe_load(file)
        dramaworld.init(script)
        return jsonify(dramaworld.state), 200
    elif data.get('script_name') == 'load-script-romeo':
        with open("script/Romeo and Juliet.yaml", encoding = 'utf-8') as file:
            script = yaml.safe_load(file)
        dramaworld.init(script)
        return jsonify(dramaworld.state), 200
    else:
        match = re.match(r"load-script-(.*)", data.get('script_name'))
        if match:
            script_id = match.group(1)
            with open(f'{dramaworld.cache}/{script_id}.yml', encoding='utf-8') as file:
                script = yaml.safe_load(file)
            dramaworld.init(script["script"])
            dramaworld.dramallm.load(script_id)
            return jsonify(dramaworld.state), 200
    if data.get('agentMode'):
        dramaworld.mode = data.get('agentMode')
        return jsonify(dramaworld.state), 200
    return None, 400

@app.route('/save', methods=['GET'])
def save():
    if hasattr(dramaworld, 'dramallm'):
        try:
            save_id = dramaworld.dramallm.save()
            return jsonify({"info": f"Saved in {dramaworld.cache} as {save_id} successfully!", "save_id" : save_id}), 200
        except Exception as e:
            return jsonify({"error": f"Error message: {e}"}), 200
    else:
        return jsonify({"error": f"Save config first to create your world, then save the script file!"}), 200

@app.route('/info', methods = ['POST'])
def get_info():
    data = request.json
    config = {
        "error": "No valid setup! "
    }
    if data.get('role'):
        cid = data.get('role')
        if hasattr(dramaworld, 'dramallm'):
            if cid in dramaworld.dramallm.characters:
                config = {
                    "profile": dramaworld.dramallm.characters[cid].profile,
                    "memory": dramaworld.dramallm.characters[cid].memory
                }
                if dramaworld.dramallm.mode == 'v2' or dramaworld.dramallm.mode == "v3":
                    config.update({"prompts":dramaworld.dramallm.characters[cid].reacts})
                    print(config)
    elif data.get('help'):
        if data["help"] == "allmemory":
            if hasattr(dramaworld, 'dramallm'):
                config = {
                    "allmemory": dramaworld.dramallm.raw_records
                }
        elif data["help"] == "dramallm":
            if hasattr(dramaworld, 'dramallm'):
                config = {
                    "dramallm": dramaworld.dramallm.reacts
                }
        elif data["help"] == "allscript":
            if hasattr(dramaworld, 'dramallm'):
                config = {
                    "allscript": dramaworld.dramallm.script,
                    "scene_cnt": dramaworld.dramallm.scene_cnt,
                    "nc": dramaworld.dramallm.nc
                }
        elif data["help"] == "characters":
            if hasattr(dramaworld, 'dramallm'):
                character = get_keys(dramaworld.dramallm.script["scenes"]["scene"+str(dramaworld.dramallm.scene_cnt)]["characters"])
                filtered_char = list(filter(lambda x: x != dramaworld.dramallm.player.id, character))
                filtered_char.append("null")
                config = {
                    "characters": filtered_char
                }
        elif data["help"] == "export_records":
            print("exporting records")
            if hasattr(dramaworld, 'dramallm'):
                save_id = dramaworld.dramallm.id + str(datetime.datetime.now().strftime("_%m%d_%H%M%S"))
                write_json(dramaworld.dramallm.raw_records, f'{dramaworld.dramallm.cache}/records/{save_id}.yaml')
                config = {
                    "allmemory": dramaworld.dramallm.raw_records
                }                
    return jsonify(config), 200

# @app.route('/interact', methods=['POST'])
# def interact():
#     data = request.json
#     print(data)
#     if data.get('dialogue'):
#         if hasattr(dramaworld, 'dramallm'):
#             if data.get('dialogue') == "-stay":
#                 act = ["-stay"]
#             else:
#                 action = message_to_act(data.get('dialogue'))
#                 act = ["-speak", action["roles"], action["message"]]
#             print(act)
#             new_action, done, error = dramaworld.round(act)
#             if error:
#                 return jsonify({"error": error})
#             return jsonify({"action": new_action, "done": done, "state": dramaworld.state}), 200
#         else:
#             return None, 400     
#     else:
#         return None, 400    

# @app.route('/next', methods=['GET'])
# def next():
#     if hasattr(dramaworld, 'dramallm'):
#         dramaworld.dramallm.next_scene()
#         print(dumps(dramaworld.dramallm.state))
#         return jsonify(dramaworld.dramallm.state), 200
#     return None, 400
    
@app.route('/interact', methods=['POST'])
def interact():
    start_time = time.time()
    data = request.json
    if data.get('type'):
        if hasattr(dramaworld, 'dramallm'):
            input_action = {"x": data.get('type')}
            if data.get('type') == "-stay":
                act = ["-stay"]
            elif data.get('type') == "-speak":
                roles, message = message_to_act(data.get('message'))
                if data.get('object') not in roles:
                    roles.append(data.get('object'))
                character = get_keys(dramaworld.dramallm.script["scenes"]["scene"+str(dramaworld.dramallm.scene_cnt)]["characters"])
                filtered_roles = list(filter(lambda x: x in character, roles))
                act = ["-speak", filtered_roles, message]
                input_action = {"x": data.get('type'), "bid": act[1], "content": act[2]}
            response, done, error = dramaworld.round(act)
            if error:
                return jsonify({"error": error})
            end_time = time.time()
            print(f"Interaction took {end_time - start_time:.2f} seconds")
            return jsonify({"input": input_action,"action": response, "done": done, "state": dramaworld.state}), 200
        else:
            return None, 400     
    elif data.get('interact'):
        if hasattr(dramaworld, 'dramallm'):
            if data.get('interact') == "next":
                dramaworld.dramallm.next_scene()
                return jsonify(dramaworld.dramallm.state), 200
            elif data.get('interact') == "back":
                dramaworld.dramallm.back_scene()
                return jsonify(dramaworld.dramallm.state), 200
            elif data.get('interact') == "withdraw":
                cnt = dramaworld.dramallm.withdraw()
                return jsonify({"state": dramaworld.dramallm.state, "cnt": cnt}), 200                                
        else:
            return None, 400
    return None, 400    

@app.route('/prompt', methods=['POST', 'GET'])
def prompt():
    if request.method == "POST":
        data = request.json
        if hasattr(dramaworld, 'dramallm'):
            dramaworld.dramallm.prompt_v1 = data['prompt_drama_v1']
            dramaworld.dramallm.prompt_v2 = data['prompt_drama_v2']
            for c, char in dramaworld.dramallm.characters.items():
                char.prompt = data['prompt_character']
                char.prompt_v2 = data['prompt_character_v2']
        for filename, content in [
            ("prompt/prompt_drama_v1.md", data['prompt_drama_v1']),
            ("prompt/prompt_drama_v2.md", data['prompt_drama_v2']),
            ("prompt/prompt_character.md", data['prompt_character']),
            ("prompt/prompt_character_v2.md", data['prompt_character_v2'])
        ]:
            with open(filename, 'w', encoding='utf-8') as file:
                file.write(content)
    prompts = {}
    for key, filename in [
        ("prompt_drama_v1", "prompt/prompt_drama_v1.md"),
        ("prompt_drama_v2", "prompt/prompt_drama_v2.md"),
        ("prompt_character", "prompt/prompt_character.md"),
        ("prompt_character_v2", "prompt/prompt_character_v2.md"),
    ]:
        with open(filename, 'r', encoding='utf-8') as file:
            prompts[key] = file.read()
    return jsonify(prompts), 200

IMG_DIR = 'assets'
os.makedirs(IMG_DIR, exist_ok=True)  # Ensure the directory exists
@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    file = request.files['file']
    name = request.form.get('name', '')  # Retrieve the name from the form data
    name += '.jpg'
    if not file or not name:
        return jsonify({'error': 'Invalid file or name'}), 400
    # Save the file with the provided name
    filepath = os.path.join(IMG_DIR, name)
    try:
        file.save(filepath)
        return jsonify({'message': 'File uploaded successfully', 'path': filepath}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
