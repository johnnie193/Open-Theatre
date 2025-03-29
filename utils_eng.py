import random
import yaml
import json
import os
import re
from copy import deepcopy
from openai import OpenAI
from gradio_client import Client
from datetime import datetime


def date():
    return datetime.now().date()

def rndsuf(k=3):
    return "".join(chr(random.randint(65, 90)) if random.randint(0, 1) else chr(random.randint(97, 122)) for _ in range(k))

def rnd():
    return random.random()

def rndc(choose4m, k=1):
    if not isinstance(choose4m, list):
        choose4m = list(choose4m)
    return random.choice(choose4m) if k == 1 else random.sample(choose4m, k)

def get_keys(content):
    if isinstance(content, dict):
        return list(content.keys())
    
def get_values(content):
    if isinstance(content, dict):
        return list(content.values())

def yaml_print(content):
    if not isinstance(content, dict):
        content = eval(content.__repr__())

def read_json(filename):
    with open(filename, encoding='utf-8') as f:
        content = json.load(f)
    return content

def write_json(content, filename):
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=2)

def read(filename):
    with open(filename, encoding='utf-8') as f:
        contet = f.read().strip()
    return contet

def write(content, filename):
    with open(filename, "w") as f:
        f.write(content.strip())
        f.write("\n")

def read_jsonl(filename):
    content = []
    with open(filename) as f:
        for line in f:
            content += [json.loads(line.strip())]
    return content

def write_jsonl(content, filename, mode="w"):
    with open(filename, mode, encoding='utf-8') as f:
        for line in content:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")

def dumps(content):
    return json.dumps(content, ensure_ascii=False, indent=2)

def yamld(content):
    return yaml.dump(content, allow_unicode=True, indent=2, sort_keys=False)

def query_gpt4(prompt, sys = None):
    KEY = read("openai_key.txt")
    client = OpenAI(api_key=KEY)
    if sys:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": sys,
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )
    else:
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ]
        )
    prediction = completion.choices[0].message.content
    return prediction

def query_qwen(query, history=[]):
    response = Client("Qwen/Qwen1.5-110B-Chat-demo").predict(
        query=query,
        history=history,
        api_name="/model_chat"
    )
    return response[1][-1][-1]

def action_to_text(m):
    text = ""
    if "message" in m:
        text = m["message"]
        return text
    if m["x"] == "-move":
        text = "{} go to {}。".format(m["a"], m["b"])
    elif m["x"] == "-take":
        text = "{} take away {}。".format(m["a"], m["b"])
    elif m["x"] == "-put":
        if m["c"]:
            text = "{} put {} on {}。".format(m["a"], m["b"], m["c"])
        else:
            text = "{} put {}。".format(m["a"], m["b"])
    elif m["x"] == "-leave":
        text = "{} leave the conversation.".format(m["a"])
    elif m["x"] == "-speak":
        # print("text_target",m["b"])
        if "b" not in m or not m["b"] or m["b"] == "null":
            text = "{} speak: {}".format(m["a"], m["content"])
        elif isinstance(m["b"], list):
            text = "{} speak to {}: {}".format(m["a"], "、".join(m["b"]), m["content"])
        else:
            text = "{} speak to {}: {}".format(m["a"], m["b"], m["content"])
    elif m["x"] == "-exit":
        text = "{} exit.".format(m["a"])
    else:
        if m["c"]:
            text = "{} {} {} {}。".format(m["a"], m["c"], m["x"], m["b"])
        else:
            text = "{} {} {}。".format(m["a"], m["x"], m["b"])
    return text

def message_to_act(text):
    pattern = r"@([\u4e00-\u9fa5\w]+(?:[，,]\s*[\u4e00-\u9fa5\w]+)*)"
    matches = re.findall(pattern, text)
    if not matches:
        return [], text
    cleaned_roles = []
    for match in matches:
        cleaned_roles.extend([role.strip() for role in re.split(r"[，,]\s*", match) if role.strip()])
    message = re.sub(r"@[\u4e00-\u9fa5\w]+(?:[，,]\s*[\u4e00-\u9fa5\w]+)*", "", text).strip()
    return cleaned_roles, message
    # {
    #     "roles": cleaned_roles,  
    #     "message": message       
    # }

def sample_script(scene_script, x):
    _samples = {}
    for v in get_values(scene_script["stream"]):
        for li in v:
            k, li = li.split("$")
            if k in _samples:
                _samples[k] += [li]
            else:
                _samples[k] = [li]
    x = x.split("$")[0] if x else x
    return _samples.get(x, [])

CACHE_DIR = "cache"
PROMPT_DRAMA_V1 = read("prompt/prompt_drama_v1_eng.md")
PROMPT_DRAMA_V2 = read("prompt/prompt_drama_v2_eng.md")
PROMPT_CHARACTER = read("prompt/prompt_character_eng.md")
PROMPT_CHARACTER_V2 = read("prompt/prompt_character_v2_eng.md")

def memory_to_text(m, char_id=None):
    text = ""    
    if char_id is not None and "bid" in m:
        m["aid"] = "you" if m["aid"] == char_id else m["aid"]
        m["bid"] = "you" if m["bid"] == char_id else m["bid"]

    if m["x"] == "-give":
        text = "{} give {} {}。".format(m["aid"], m["bid"], m["cid"])
    elif m["x"] == "-speak" and "bid" in m:
        text = "{} speak: {}".format(m["aid"], m["content"])
    elif m["x"] == "-speak":
        text = "{} speak to {}: {}".format(m["aid"], m["bid"], m["content"])
    elif m["x"] == "-leave":
        text = "{} leave the conversation。".format(m["aid"])
    elif m["x"] == "-move":
        text = "{} go to {}。".format(m["aid"], m["bid"])
    elif m["x"] == "-scream":
        text = "{} scream: {}".format(m["aid"], m["content"])

    return text

def observation_to_text(o, char_id=None):
    o["interact_with"] = "you" if o["interact_with"] == char_id else o["interact_with"]
    if o["status"] == "/idle/" and o["interact_with"] is None:
        text = "{} is idle, at {}.".format(o["id"], o["loc"])
    elif o["status"] == "/idle/" and o["interact_with"] is not None:
        text = "{} is interacting with {}, at {}..".format(o["id"], o["interact_with"], o["loc"])
    elif o["status"] == "/faint/":
        text = "{} is faint, at{}.".format(o["id"], o["loc"])

    return text

def dump_script(script, id, detail=False):
    if detail:
        return yaml.safe_dump(script, allow_unicode=True, indent=2, sort_keys=False)
    tmp_script = deepcopy(script)
    for scene_id, v in tmp_script.items():
        if scene_id == ("scene"+str(id)):
            continue
        # v["stream"] = get_keys(v["stream"]) if "stream" in v else None
        v["characters"] = None
        v["mode"] = None
        v["stream"] = None
    return yaml.safe_dump(tmp_script, allow_unicode=True, indent=2, sort_keys=False)
