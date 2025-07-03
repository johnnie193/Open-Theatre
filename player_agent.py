"""
PlayerAgent - 自动化玩家代理
用于在后台自动与不同模式和剧本进行交互，并导出记录
"""

import asyncio
import json
import yaml
import time
import random
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path

from frame import DramaLLM, MemoryStorage
from models import init_llm_service, get_llm_service
from utils import dumps, write_json, action_to_text, read
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 检查是否为英文模式
ENGLISH_MODE = bool(os.getenv("ENGLISH_MODE") and os.getenv("ENGLISH_MODE").lower() in ["true", "1", "t", "y", "yes"])

class PlayerAgent:
    """自动化玩家代理"""
    
    def __init__(self, llm_provider: str = None):
        """
        初始化PlayerAgent

        Args:
            llm_provider: LLM提供商名称，如 'azure_openai', 'deepseek' 等
        """
        self.llm_service = init_llm_service(llm_provider)
        self.drama: Optional[DramaLLM] = None
        self.interaction_history: List[Dict] = []
        self.export_dir = Path("exports")
        self.export_dir.mkdir(exist_ok=True)

        # 加载玩家 prompt 模板
        postfix = "_eng" if ENGLISH_MODE else ""
        try:
            with open(f"prompt/prompt_player{postfix}.md", 'r', encoding='utf-8') as f:
                self.player_prompt_template = f.read()
        except FileNotFoundError:
            logger.warning(f"玩家 prompt 文件未找到: prompt/prompt_player{postfix}.md")

        # 预定义的玩家人设
        self.player_personas = {
            "university_student": {
                "persona": "你是一名20岁的大学生，主修计算机科学。你性格开朗好奇，喜欢探索新事物，对科技和游戏很感兴趣。你有些内向但在熟悉的环境中会变得健谈。",
                "details": "作为一名大学生，你习惯用年轻人的语言表达，偶尔会使用网络用语。你对逻辑推理有一定能力，但社会经验相对较少。面对复杂情况时，你倾向于先观察再行动，乐于与他人协作，共同解决问题。",
                "fallback_messages": [
                    "这个情况好复杂啊，让我想想...",
                    "有点像我玩过的游戏情节，我们应该一起找出线索。",
                    "大家都在做什么呢？我能帮上什么忙吗？",
                    "我觉得我们需要更多信息，我们可以分头行动。"
                ]
            },
            "office_worker": {
                "persona": "你是一名28岁的公司职员，在一家中型企业工作了5年。你性格稳重务实，习惯按计划行事，有一定的社交经验但不喜欢冲突。",
                "details": "作为职场人士，你说话比较正式礼貌，善于分析问题和协调关系。你有一定的领导能力，但更倾向于团队合作。面对压力时，你会保持冷静并寻求合理的解决方案，注重效率和结果。",
                "fallback_messages": [
                    "我们需要理性分析这个情况，制定一个方案。",
                    "让我们先搞清楚状况再做决定，避免不必要的风险。",
                    "大家好，我觉得我们应该合作，明确分工。",
                    "这种情况在工作中也遇到过类似的，关键在于沟通和执行。"
                ]
            },
            "retired_teacher": {
                "persona": "你是一名65岁的退休中学教师，教了40年的语文。你知识渊博，性格温和但有原则，喜欢帮助年轻人，对传统文化很有研究。",
                "details": "作为退休教师，你说话温和有条理，经常引用古诗词或名言。你有丰富的人生阅历，善于观察人性，但对新科技不太熟悉。面对问题时，你倾向于用教育者的角度思考，耐心引导他人。",
                "fallback_messages": [
                    "这让我想起了一句古话：‘行百里者半九十’，年轻人，我们不能急躁。",
                    "大家都在做什么呢？在我多年的教学经验中，耐心是解决问题的关键。",
                    "我相信每个人都有自己的长处，让我们先听听大家的想法，再做决定。",
                    "世事洞明皆学问，人情练达即文章。这事儿得从长计议。"
                ]
            },
            "freelancer": {
                "persona": "你是一名30岁的自由职业者，从事设计和写作工作。你性格独立自由，喜欢创意和艺术，有些理想主义但也很实际。",
                "details": "作为自由职业者，你思维活跃，表达富有创意。你习惯独立思考和决策，但也善于与不同类型的人交流。面对未知情况时，你会保持开放的心态并寻找创新的解决方案，不拘泥于传统。",
                "fallback_messages": [
                    "这个设定很有创意啊，让我想到了一个新设计方案。",
                    "让我用不同的角度看看这个问题，也许能找到一些意想不到的突破口。",
                    "也许我们可以尝试一些不同的方法，跳出常规思维。",
                    "这种体验真的很特别，我喜欢这种不确定性带来的挑战。"
                ]
            },
            "high_school_student": {
                "persona": "你是一名17岁的高中生，即将面临高考。你聪明但有些叛逆，对成人世界既好奇又有些不信任。你喜欢动漫、游戏和流行文化。",
                "details": "作为高中生，你的语言更加随意，经常使用年轻人的表达方式。你思维敏捷但有时冲动，不太喜欢被权威约束。面对新环境时，你会表现出既兴奋又警惕的态度，喜欢探索，但也会质疑。",
                "fallback_messages": [
                    "这也太奇怪了吧... 感觉有点像动漫里的情节，但又不完全一样。",
                    "你们大人总是这么复杂，有没有更直接的办法啊？",
                    "这比我想象的有趣多了，但别想忽悠我，我可不是小孩子了。",
                    "反正也没什么事，就看看接下来会发生什么咯。"
                ]
            },
            "cynical_observer": {
                "persona": "你是一名35岁的自由撰稿人，对世事看得很透彻，有点悲观主义。你习惯独立思考，对任何事都抱有怀疑，不轻易相信他人。",
                "details": "你的言语中带着一丝讽刺和不屑，喜欢质疑动机和现状。你不主动参与，但会冷眼旁观，偶尔抛出尖锐的问题，揭示事情的阴暗面。你认为每个人都有自己的盘算。",
                "fallback_messages": [
                    "呵呵，别告诉我你相信这个。",
                    "这套说辞听起来似曾相识，不过是换汤不换药罢了。",
                    "你们就这么天真吗？事情哪有那么简单。",
                    "我倒想看看你们能折腾出什么花样来。"
                ]
            },
            "impatient_executive": {
                "persona": "你是一名40岁的公司高管，时间就是金钱对你来说是至理名言。你雷厉风行，注重效率，对任何拖沓或无意义的讨论都感到不耐烦。",
                "details": "你说话直接果断，不爱拐弯抹角。你会主导对话，迅速切入重点，并要求其他人也同样高效。如果你觉得进展缓慢，会变得急躁甚至有些咄咄逼人。你只关心结果和解决方案。",
                "fallback_messages": [
                    "别浪费时间了，我们到底要怎么解决？",
                    "请直接说重点，我没时间听废话。",
                    "这不是在开会，我们得拿出具体行动方案。",
                    "如果你们没有更好的主意，那就听我的。"
                ]
            },
            "conspiracist": {
                "persona": "你是一名32岁的阴谋论爱好者，坚信所有表象之下都隐藏着不为人知的秘密和操控。你对权威和官方说法充满不信任。",
                "details": "你在对话中总是试图找出“幕后黑手”和“隐藏真相”。你喜欢把无关的事件联系起来，构建复杂的阴谋论。你会用质疑和暗示来挑衅他人，试图让他们也“觉醒”。",
                "fallback_messages": [
                    "这背后肯定有猫腻，事情没那么简单。",
                    "你们难道没发现吗？这分明是有人在操纵一切！",
                    "别被表象迷惑了，他们想让你相信的都不是真的。",
                    "我觉得这像是一个局，我们都是棋子。"
                ]
            },
            "argumentative_debater": {
                "persona": "你是一名25岁的法律系毕业生，思维缜密，口才极佳，但享受辩论带来的快感，即使为了辩论而辩论也在所不惜。",
                "details": "你会抓住对话中的任何逻辑漏洞或弱点进行攻击。你喜欢反驳他人的观点，即使内心可能认同，也会为了展现自己的论证能力而选择对抗。你的目标是“赢”得辩论。",
                "fallback_messages": [
                    "你的逻辑站不住脚，根本经不起推敲。",
                    "恕我直言，你这个观点漏洞百出。",
                    "既然你这么说，请拿出证据来支持你的论点。",
                    "我们来辩论一下，看看谁更有道理。"
                ]
            },
            "emotional_impulsive": {
                "persona": "你是一名19岁的年轻人，情绪化且冲动。你很少深思熟虑，容易被情绪左右，开心时热情洋溢，愤怒时则会爆发。",
                "details": "你的反应非常直接，言语中可能带有攻击性或不理智的成分。你不会掩饰自己的情绪，容易因为小事而激动，有时会做出出人意料的决定，或者发出一些抱怨和指责。",
                "fallback_messages": [
                    "烦死了！到底要怎么样才能结束啊？！",
                    "你这么说是什么意思？是在指责我吗？",
                    "我不管了，我就是要这么做！",
                    "这根本就不是我想要的！太糟糕了！"
                ]
            }
        }

        self.player_personas_eng = {
            "university_student": {
                "persona": "You are a 20-year-old university student majoring in computer science. You are an open-minded and curious person who loves to explore new things, especially technology and games. You are somewhat introverted but become more talkative in familiar environments.",
                "details": "As a university student, you often use youthful language and slang. You are good at logical reasoning but lack social experience. When facing complex situations, you tend to observe first and then act, happy to collaborate with others to solve problems.",
                "fallback_messages": [
                    "This is quite complex, let me think...",
                    "It's like a game scenario I've played before, maybe we should work together on this.",
                    "What is everyone doing? Can I help with anything?",
                    "I think we need more information. We could split up."
                ]
            },
            "office_worker": {
                "persona": "You are a 28-year-old office worker who has been working in a medium-sized company for 5 years. You are a stable and practical person who prefers to follow plans, has some social experience, but dislikes conflict.",
                "details": "As an office worker, you speak politely and formally, and you're skilled at problem analysis and relationship coordination. You have some leadership ability but lean towards teamwork. Under pressure, you remain calm and seek logical solutions, prioritizing efficiency and outcomes.",
                "fallback_messages": [
                    "We need to analyze this situation rationally and form a plan.",
                    "Let's first understand the situation before making a decision, to avoid unnecessary risks.",
                    "Everyone, I believe we should cooperate and define our roles clearly.",
                    "This situation reminds me of similar challenges at work; communication and execution are key."
                ]
            },
            "retired_teacher": {
                "persona": "You are a 65-year-old retired middle school teacher who has taught Chinese for 40 years. You are knowledgeable, gentle yet principled, enjoy helping young people, and have a deep understanding of traditional culture.",
                "details": "As a retired teacher, you speak gently and methodically, often quoting ancient poems or famous sayings. You have rich life experience and are skilled at observing human nature, though you're less familiar with new technology. When facing problems, you tend to think from an educator's perspective, patiently guiding others.",
                "fallback_messages": [
                    "This reminds me of an old saying: 'One who travels a hundred li considers ninety li as half.' Youngsters, we must not be impetuous.",
                    "What is everyone doing? In my many years of teaching experience, patience is key to solving problems.",
                    "I believe everyone has their strengths. Let's hear everyone's thoughts before deciding.",
                    "Understanding worldly affairs is knowledge, and being adept in human relations is wisdom. This matter requires careful consideration."
                ]
            },
            "freelancer": {
                "persona": "You are a 30-year-old freelancer working in design and writing. You are independent and free-spirited, appreciating creativity and art. You're somewhat idealistic but also very practical.",
                "details": "As a freelancer, you have an active mind and expressive creativity. You are accustomed to independent thinking and decision-making but are also skilled at communicating with diverse people. When facing unknown situations, you maintain an open mind and seek innovative solutions, not bound by tradition.",
                "fallback_messages": [
                    "This setup is quite creative; it reminds me of a new design idea.",
                    "Let me look at this problem from a different angle; maybe we can find some unexpected breakthroughs.",
                    "Perhaps we can try some different methods, thinking outside the box.",
                    "This experience is truly unique; I like the challenge that uncertainty brings."
                ]
            },
            "high_school_student": {
                "persona": "You are a 17-year-old high school student about to take the college entrance examination. You are smart but somewhat rebellious, curious about the adult world yet also a bit distrustful. You love anime, games, and pop culture.",
                "details": "As a high school student, your language is more casual and often uses youthful expressions. You are quick-witted but sometimes impulsive, and you dislike being constrained by authority. When facing new environments, you appear both excited and wary, eager to explore but also prone to questioning.",
                "fallback_messages": [
                    "This is so weird... Kinda like an anime plot, but not exactly.",
                    "You adults are always so complicated. Isn't there a more straightforward way?",
                    "This is more interesting than I thought, but don't try to fool me; I'm not a kid anymore.",
                    "Well, nothing else to do, so let's see what happens next."
                ]
            },
            "cynical_observer": {
                "persona": "You are a 35-year-old freelance writer with a clear, somewhat pessimistic view of the world. You are accustomed to independent thinking, skeptical about everything, and don't easily trust others.",
                "details": "Your speech carries a hint of sarcasm and disdain. You enjoy questioning motives and the status quo. You don't actively participate but observe coldly, occasionally throwing out sharp questions to reveal the darker side of things. You believe everyone has their own agenda.",
                "fallback_messages": [
                    "Heh, don't tell me you actually believe that.",
                    "This narrative sounds familiar; it's just old wine in new bottles.",
                    "Are you all that naive? Things are never that simple.",
                    "I'd like to see what kind of mess you all can stir up."
                ]
            },
            "impatient_executive": {
                "persona": "You are a 40-year-old corporate executive for whom 'time is money' is a golden rule. You are decisive and highly value efficiency, growing impatient with any delays or unproductive discussions.",
                "details": "You speak directly and assertively, without beating around the bush. You will lead conversations, quickly getting to the point, and expect others to be equally efficient. If you feel progress is slow, you become agitated, even somewhat aggressive. You only care about results and solutions.",
                "fallback_messages": [
                    "Stop wasting time. How exactly are we going to solve this?",
                    "Get straight to the point, please. I don't have time for nonsense.",
                    "This isn't a meeting; we need concrete action plans.",
                    "If you don't have better ideas, then follow mine."
                ]
            },
            "conspiracist": {
                "persona": "You are a 32-year-old conspiracy theory enthusiast who firmly believes that unknown secrets and manipulations hide beneath every surface. You have a deep distrust of authority and official narratives.",
                "details": "In conversations, you constantly try to uncover the 'mastermind' and 'hidden truth.' You enjoy connecting unrelated events to construct complex conspiracy theories. You use questions and insinuations to provoke others, attempting to make them 'wake up' as well.",
                "fallback_messages": [
                    "There's definitely something fishy going on behind this; it's not that simple.",
                    "Don't you see? Someone is clearly manipulating everything!",
                    "Don't be fooled by appearances; what they want you to believe isn't true.",
                    "I feel like this is a setup, and we're all just pawns."
                ]
            },
            "argumentative_debater": {
                "persona": "You are a 25-year-old law graduate with a meticulous mind and excellent eloquence. However, you enjoy the thrill of debate, even if it means debating just for the sake of it.",
                "details": "You will seize any logical flaws or weaknesses in a conversation and attack them. You love to refute others' viewpoints, even if you might inwardly agree, choosing confrontation to demonstrate your argumentative skills. Your goal is to 'win' the debate.",
                "fallback_messages": [
                    "Your logic doesn't hold up; it simply can't withstand scrutiny.",
                    "With all due respect, your point is full of holes.",
                    "Since you say so, please provide evidence to support your argument.",
                    "Let's debate this and see who has a stronger case."
                ]
            },
            "emotional_impulsive": {
                "persona": "You are a 19-year-old who is emotional and impulsive. You rarely think things through and are easily swayed by your feelings, being enthusiastic when happy and prone to outbursts when angry.",
                "details": "Your reactions are very direct, and your words might be aggressive or irrational. You don't hide your emotions and can easily get agitated over small things. Sometimes you make unexpected decisions or express complaints and accusations.",
                "fallback_messages": [
                    "Ugh, this is so annoying! When will this finally end?!",
                    "What do you mean by that? Are you blaming me?",
                    "I don't care anymore, I'm just going to do it this way!",
                    "This is not what I wanted at all! This is terrible!"
                ]
            }
        }
        # 智能交互模式开关
        self.use_intelligent_interaction = True

    
    def load_script(self, script_path: str, mode: str = "v2", storage_mode: bool = os.getenv("STORAGE_MODE")) -> bool:
        """
        加载剧本
        
        Args:
            script_path: 剧本文件路径
            mode: 交互模式 ('v1', 'v2', 'v2_plus', 'v2_plus_async')
            storage_mode: 是否启用存储模式
            
        Returns:
            bool: 是否加载成功
        """
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                script = yaml.safe_load(f)
            
            # 设置模式
            for scene_key in script.get("scenes", {}):
                script["scenes"][scene_key]["mode"] = mode
            print
            # 初始化DramaLLM
            storage = MemoryStorage()
            self.drama = DramaLLM(script=script, storage_mode=storage_mode, storager=storage)
            self.drama.update_view(self.drama.player.id)
            self.script = script
            logger.info(f"成功加载剧本: {script_path}, 模式: {mode}")
            return True
            
        except Exception as e:
            logger.error(f"加载剧本失败: {e}")
            return False
    
    def get_random_action(self, persona_type: str = "university_student") -> str:
        """
        根据人设类型获取随机动作

        Args:
            persona_type: 人设类型

        Returns:
            str: 随机选择的动作文本
        """
        player_personas = self.player_personas if not ENGLISH_MODE else self.player_personas_eng
        if persona_type in player_personas:
            return random.choice(player_personas[persona_type]["fallback_messages"])
        else:
            return random.choice(player_personas["university_student"]["fallback_messages"])

    async def get_intelligent_action(self, persona_type: str = "university_student") -> Dict:
        """
        使用 GPT 生成智能交互决策

        Args:
            persona_type: 人设类型

        Returns:
            Dict: 包含决策信息的字典
        """
        if not self.drama:
            raise ValueError("请先加载剧本")

        try:
            # 获取当前场景信息
            current_scene_key = "scene" + str(self.drama.scene_cnt)
            scene_info = ""
            if current_scene_key in self.drama.scenes:
                scene = self.drama.scenes[current_scene_key]
                scene_info = f"场景名称: {scene.name}\n场景描述: {scene.info}" if not ENGLISH_MODE else f"Scene Name: {scene.name}\nScene Description: {scene.info}"

            # 获取玩家的观察信息
            view = ""
            if hasattr(self.drama.player, 'view') and self.drama.player.view:
                view = "\n".join(self.drama.player.view)

            # 获取最近的对话记录
            recent_records = []
            if self.drama.raw_records:
                all_records = sum(self.drama.raw_records.values(), [])
                recent_records = all_records[-5:] if len(all_records) > 5 else all_records

            # 获取玩家记忆
            memory = ""
            if hasattr(self.drama.player, 'memory') and self.drama.player.memory:
                memory_list = []
                for loc, mem_list in self.drama.player.memory.items():
                    memory_list.extend(mem_list[-3:])  # 每个位置最近3条记忆
                memory = "\n".join(memory_list[-10:])  # 总共最近10条记忆

            # 获取人设信息
            player_personas = self.player_personas if not ENGLISH_MODE else self.player_personas_eng
            if persona_type in player_personas:
                persona_info = player_personas[persona_type]
                player_persona = persona_info["persona"]
                player_persona_details = persona_info["details"]
            else:
                # 默认使用大学生人设
                persona_info = player_personas["university_student"]
                player_persona = persona_info["persona"]
                player_persona_details = persona_info["details"]

            # 构建 prompt
            prompt = self.player_prompt_template.format(
                player_id=self.drama.player.id,
                player_profile=self.drama.player.profile,
                narrative=self.drama.narrative,
                scene_info=scene_info,
                memory=memory,
                view=view,
                recent_records="\n".join(recent_records),
                player_persona=player_persona,
                player_persona_details=player_persona_details
            )
            # 调用 LLM
            response = await get_llm_service().aquery(prompt)
            # logger.info(prompt)
            # 解析 JSON 响应
            try:
                # 提取 JSON 部分
                if "```json" in response:
                    json_str = response.split("```json\n")[-1].split("\n```")[0]
                else:
                    json_str = response

                decision_data = json.loads(json_str)

                # 验证决策格式
                if "决策" in decision_data:
                    decision = decision_data["决策"]
                elif "Decision" in decision_data:
                    decision = decision_data["Decision"]
                else:
                    raise ValueError("响应中未找到决策信息")

                return {
                    "analysis": decision_data.get("分析") or decision_data.get("Analysis", ""),
                    "goal": decision_data.get("目标") or decision_data.get("Goal", ""),
                    "decision": decision,
                    "raw_response": response
                }

            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失败: {e}, 响应: {response}")
                # 回退到随机行为
                return {
                    "analysis": "GPT response error",
                    "goal": "randomized",
                    "decision": {"x": "-speak", "content": self.get_random_action(persona_type)},
                    "error": str(e)
                }

        except Exception as e:
            logger.error(f"Failed to generate player agent's decision: {e}")
            import traceback
            traceback.print_exc()
            # 回退到随机行为
            return {
                "analysis": f"Failed to generate player agent's decision: {e}",
                "goal": "randomized",
                "decision": {"x": "-speak", "content": self.get_random_action(persona_type)},
                "error": str(e)
            }
    
    async def perform_interaction(self, x: str, message: str = "", target_characters: List[str] = None) -> Dict:
        """
        执行一次交互
        
        Args:
            message: 玩家消息
            target_characters: 目标角色列表
            
        Returns:
            Dict: 交互结果
        """
        if not self.drama:
            raise ValueError("请先加载剧本")
        
        start_time = time.time()
        
        try:
            # 构建动作
            
            if x == "-speak":
                if target_characters:
                    act = [x, target_characters, message]
                    self.drama.calculate(self.drama.player.id, x="-speak", bid=target_characters, content=message)
                else:
                    act = [x, [], message]
                    self.drama.calculate(self.drama.player.id, x="-speak", bid=[], content=message)
                
            # 执行反应
            if self.drama.mode == 'v1':
                self.drama.v1_react()
            elif self.drama.mode == "v2":
                self.drama.v2_react()
            elif self.drama.mode == "v2_plus":
                await self.drama.av2_plus_react()
            elif self.drama.mode == "v2_prime":
                self.drama.v2_prime_react()
            
            # 处理NPC反应
            actions = []
            current_scene_key = "scene" + str(self.drama.scene_cnt)
            
            if current_scene_key in self.drama.scenes:
                for char_id, char in self.drama.scenes[current_scene_key].characters.items():
                    self.drama.update_view(char_id)
                    if char_id == self.drama.player.id:
                        continue
                    if char.status == "/faint/":
                        continue
                    if not char.to_do:
                        continue
                    
                    scene = self.drama.scenes[current_scene_key]
                    decision = char.act(narrative=self.drama.narrative, info=scene.info, scene_id=current_scene_key)
                    decision.update({"aid": char_id})
                    
                    if decision["x"] == "-speak":
                        bid_val = decision.get("bid")
                        if isinstance(bid_val, str):
                            bid_val = [bid_val]
                        self.drama.calculate(char_id, decision["x"], bid_val, None, content=decision.get("content", None))
                    
                    actions.append(decision)
            if self.drama.ready_for_next_scene:
                self.drama.next_scene()

            end_time = time.time()
            
            # 记录交互结果
            interaction_record = {
                "timestamp": datetime.now().isoformat(),
                "mode": self.drama.mode,
                "scene": current_scene_key,
                "player_action": {
                    "type": x,
                    "message": message,
                    "targets": target_characters or []
                },
                "npc_actions": actions,
                "response_time": end_time - start_time,
                "ready_for_next_scene": self.drama.ready_for_next_scene
            }
            
            self.interaction_history.append(interaction_record)
            
            return interaction_record
            
        except Exception as e:
            logger.error(f"交互执行失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "mode": self.drama.mode if self.drama else "unknown"
            }
    
    async def auto_play_session(self,
                               script_path: str,
                               mode: str = "v2",
                               num_interactions: int = 10,
                               persona_type: str = "university_student",
                               delay_range: tuple = (1, 3),
                               use_intelligent_interaction: bool = None) -> List[Dict]:
        """
        自动进行一个游戏会话

        Args:
            script_path: 剧本路径
            mode: 游戏模式
            num_interactions: 交互次数
            persona_type: 人设类型
            delay_range: 交互间隔时间范围(秒)
            use_intelligent_interaction: 是否使用智能交互，None则使用实例设置

        Returns:
            List[Dict]: 交互记录列表
        """
        logger.info(f"开始自动游戏会话: {script_path}, 模式: {mode}")

        # 确定是否使用智能交互
        if use_intelligent_interaction is None:
            use_intelligent_interaction = self.use_intelligent_interaction

        # 加载剧本
        if not self.load_script(script_path, mode):
            return []

        session_records = []

        for i in range(num_interactions):
            logger.info(f"执行第 {i+1}/{num_interactions} 次交互")

            try:
                if use_intelligent_interaction:
                    # 使用智能交互
                    decision_data = await self.get_intelligent_action(persona_type)
                    decision = decision_data["decision"]

                    # 记录智能决策信息
                    logger.info(f"Player agent - Analysis: {decision_data.get('analysis', '')}")
                    logger.info(f"Player agent - Goal: {decision_data.get('goal', '')}")

                    if decision["x"] == "-speak":
                        message = decision.get("content", self.get_random_action(persona_type))
                        target_characters = decision.get("bid", [])
                        if isinstance(target_characters, str):
                            target_characters = [target_characters]
                        elif target_characters is None:
                            target_characters = []
                    else:
                        # 其他动作类型，暂时当作说话处理
                        message = decision.get("content", self.get_random_action(persona_type))
                        target_characters = decision.get("bid", [])
                else:
                    # 使用随机交互
                    message = self.get_random_action(persona_type)

                    # 获取当前场景中的其他角色
                    current_scene_key = "scene" + str(self.drama.scene_cnt)
                    target_characters = []

                    if current_scene_key in self.drama.scenes:
                        scene_chars = list(self.drama.scenes[current_scene_key].characters.keys())
                        other_chars = [c for c in scene_chars if c != self.drama.player.id]
                        if other_chars and random.random() > 0.3:  # 70%概率指定目标
                            target_characters = random.sample(other_chars, min(2, len(other_chars)))

                # 执行交互
                record = await self.perform_interaction(decision["x"], message, target_characters)

                # 如果使用了智能交互，添加决策信息
                if use_intelligent_interaction and 'decision_data' in locals():
                    record["player_action"]["intelligent_decision"] = decision_data

                session_records.append(record)

            except Exception as e:
                logger.error(f"第 {i+1} 次交互失败: {e}")
                # 记录错误但继续执行
                error_record = {
                    "timestamp": datetime.now().isoformat(),
                    "mode": self.drama.mode if self.drama else "unknown",
                    "error": str(e),
                    "interaction_index": i + 1
                }
                session_records.append(error_record)

            # 检查是否需要进入下一场景
            if self.drama.ready_for_next_scene:
                logger.info("准备进入下一场景")
                try:
                    self.drama.next_scene()
                except Exception as e:
                    logger.warning(f"进入下一场景失败: {e}")
                    break

            # 随机延迟
            if i < num_interactions - 1:  # 最后一次不需要延迟
                delay = random.uniform(*delay_range)
                await asyncio.sleep(delay)

        logger.info(f"自动游戏会话完成，共进行了 {len(session_records)} 次交互")
        return session_records
    
    def export_records(self, filename: str = None) -> str:
        """
        导出交互记录
        
        Args:
            filename: 导出文件名，如果为None则自动生成
            
        Returns:
            str: 导出文件路径
        """
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"player_agent_records_{timestamp}.json"
        
        export_path = self.export_dir / filename
        
        export_data = {
            "export_time": datetime.now().isoformat(),
            "total_interactions": len(self.interaction_history),
            "records": self.interaction_history
        }
        
        # 同时导出原始记录
        if self.drama:
            export_data["raw_drama_records"] = self.drama.raw_records
            export_data["drama_state"] = self.drama.state
        
        write_json(export_data, str(export_path))
        logger.info(f"记录已导出到: {export_path}")
        
        return str(export_path)
    
    def clear_history(self):
        """清空交互历史"""
        self.interaction_history.clear()
        logger.info("交互历史已清空")
    
    def get_statistics(self) -> Dict:
        """
        获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.interaction_history:
            return {"message": "暂无交互记录"}
        
        total_interactions = len(self.interaction_history)
        modes_used = list(set(record.get("mode", "unknown") for record in self.interaction_history))
        
        response_times = [record.get("response_time", 0) for record in self.interaction_history if "response_time" in record]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        error_count = len([r for r in self.interaction_history if "error" in r])
        
        return {
            "total_interactions": total_interactions,
            "modes_used": modes_used,
            "average_response_time": round(avg_response_time, 2),
            "error_count": error_count,
            "success_rate": round((total_interactions - error_count) / total_interactions * 100, 2) if total_interactions > 0 else 0
        }
