"""
二周目花月 - 末世生存文字RPG游戏
标准 AstrBot 插件
"""

import json
import random
from pathlib import Path
from typing import Dict, Any

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star
from astrbot.api import logger


FACTIONS = {
    "流浪者": {"bonus_points": 0, "description": "自由的探索者，无拘无束"},
    "炊事班供餐部": {"bonus_points": 3, "description": "末世中的美食守护者"},
    "警卫局": {"bonus_points": 4, "description": "自治区的武装力量"},
    "自由组队": {"bonus_points": 2, "description": "自发组成的小队"}
}

SIDEQUESTS = [
    {"name": "旧钢琴", "desc": "在废墟中发现了一架破旧的三角琴", "achievement": "钢琴诗人"},
    {"name": "冬叶原传单", "desc": "天空飘来一张破旧的「冬叶原」传单", "achievement": "往事如风"},
    {"name": "深渊之天", "desc": "你望向灰蒙蒙的天空，它仿佛要吞噬一切", "achievement": "存在主义者"},
    {"name": "致幻孢子", "desc": "在丛林中被致幻孢子感染", "achievement": "幻觉行者"},
    {"name": "垃圾回收机", "desc": "找到了一台还在运作的垃圾回收机", "achievement": "环保主义者"},
]

MAP_TILES = ["⬜", "🏚️", "🛒", "🏥", "🌲", "🛤️", "💧", "🌳", "🏭", "🏫"]


class ErZhouMuPlugin(Star):
    """二周目花月 - 末世生存RPG游戏"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.players_file = self.data_dir / "players.json"
        self.achievements_file = self.data_dir / "achievements.json"
        self._init_data_files()
        self.player_sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("🌸 二周目花月插件加载成功！")

    def _init_data_files(self):
        for f in [self.players_file, self.achievements_file]:
            if not f.exists():
                with open(f, "w", encoding="utf-8") as fp:
                    json.dump({}, fp)

    def _load_players(self):
        with open(self.players_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_players(self, data):
        with open(self.players_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_achievements(self):
        with open(self.achievements_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_achievements(self, data):
        with open(self.achievements_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _format_map(self, size=8, x=0, y=0):
        output = "【探索地图】\n  " + " ".join([f"{i:2d}" for i in range(size)]) + "\n"
        for yy in range(size):
            row = f"{yy:2d} "
            for xx in range(size):
                if xx == x and yy == y: row += "🧍 "
                elif xx == size-1 and yy == size-1: row += "⭐ "
                elif xx == 0 and yy == 0: row += "🏠 "
                else: row += MAP_TILES[(xx*13+yy*7)%len(MAP_TILES)] + " "
            output += row + "\n"
        return output + "\n🧍=你 ⭐=主线 🏠=安全区"

    @filter.command_group("花月")
    def group(self): pass

    @group.command("注册")
    async def cmd_register(self, event: AstrMessageEvent, faction="流浪者"):
        user_id = event.get_sender_id()
        players = self._load_players()
        
        if user_id in players:
            yield event.plain_result("❌ 你已经注册过了！")
            return
        if faction not in FACTIONS:
            yield event.plain_result(f"❌ 无效阵营，可选：{'、'.join(FACTIONS.keys())}")
            return
        
        base = 30 + FACTIONS[faction]["bonus_points"]
        players[user_id] = {
            "nickname": f"冒险者{user_id[-4:]}",
            "faction": faction, "level": 1, "exp": 0,
            "hp": 100, "max_hp": 100, "stamina": 100, "max_stamina": 100, "gold": 0,
            "attributes": {"strength":5,"agility":5,"constitution":5,"intelligence":5,"perception":5,"luck":5},
            "exploration_count": 0, "mainline_stage": 1, "attribute_points": base
        }
        self._save_players(players)
        yield event.plain_result(f"""✅ 注册成功！

【你的信息】
🎭 阵营：{faction}
📊 可用属性点：{base}

💡 使用：/花月 属性 力 敏 体 智 感 运
例：/花月 属性 10 10 5 5 5 5""")

    @group.command("阵营")
    async def cmd_factions(self, event: AstrMessageEvent):
        msg = "【可选阵营】\n\n"
        for name, config in FACTIONS.items():
            msg += f"🎭 {name}\n"
            msg += f"   {config['description']}\n"
            msg += f"   额外点数：+{config['bonus_points']}\n\n"
        yield event.plain_result(msg)

    @group.command("属性")
    async def cmd_attributes(
        self, event: AstrMessageEvent,
        strength: int = 5, agility: int = 5, constitution: int = 5,
        intelligence: int = 5, perception: int = 5, luck: int = 5
    ):
        user_id = event.get_sender_id()
        players = self._load_players()
        
        if user_id not in players:
            yield event.plain_result("❌ 请先注册：/花月 注册")
            return
        
        total = strength + agility + constitution + intelligence + perception + luck
        max_points = players[user_id]["attribute_points"]
        
        if total > max_points:
            yield event.plain_result(f"❌ 属性点总和不能超过 {max_points}！")
            return
        
        players[user_id]["attributes"] = {
            "strength": strength, "agility": agility, "constitution": constitution,
            "intelligence": intelligence, "perception": perception, "luck": luck
        }
        self._save_players(players)
        yield event.plain_result("✅ 属性设置成功！")

    @group.command("探索")
    async def cmd_explore(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        players = self._load_players()
        
        if user_id not in players:
            yield event.plain_result("❌ 请先注册：/花月 注册")
            return
        if players[user_id]["stamina"] < 10:
            yield event.plain_result("❌ 体力不足！需要10点体力")
            return
        
        players[user_id]["stamina"] -= 10
        players[user_id]["exploration_count"] += 1
        self._save_players(players)
        self.player_sessions[user_id] = {"x":0, "y":0, "sidequests_triggered":0}
        yield event.plain_result(f"✅ 开始探索！\n\n{self._format_map()}")

    @group.command("移动")
    async def cmd_move(self, event: AstrMessageEvent, direction=""):
        user_id = event.get_sender_id()
        if user_id not in self.player_sessions:
            yield event.plain_result("❌ 请先 /花月 探索")
            return
        
        dir_map = {"上":(0,-1),"下":(0,1),"左":(-1,0),"右":(1,0)}
        if direction not in dir_map:
            yield event.plain_result("❌ 方向只能是：上、下、左、右")
            return
        
        dx, dy = dir_map[direction]
        s = self.player_sessions[user_id]
        new_x, new_y = s["x"]+dx, s["y"]+dy
        
        if new_x<0 or new_x>=8 or new_y<0 or new_y>=8:
            yield event.plain_result("❌ 无法移动到地图外！")
            return
        
        s["x"], s["y"] = new_x, new_y
        msg = f"📍 移动到 ({new_x}, {new_y})\n\n"
        
        if s["sidequests_triggered"]<2 and random.random()<0.3:
            q = random.choice(SIDEQUESTS)
            msg += f"【支线触发】✨ {q['name']}\n{q['desc']}\n\n"
            s["sidequests_triggered"] += 1
            achs = self._load_achievements()
            if user_id not in achs: achs[user_id] = []
            if q["achievement"] not in [a["name"] for a in achs[user_id]]:
                achs[user_id].append({"name":q["achievement"], "description":f"完成支线：{q['name']}"})
                self._save_achievements(achs)
                msg += f"🏆 获得成就：{q['achievement']}\n\n"
        
        if new_x==7 and new_y==7:
            msg += "⭐ 【主线触发】你抵达了命运的交汇点...\n\n"
        
        msg += self._format_map(8, new_x, new_y)
        yield event.plain_result(msg)

    @group.command("状态")
    async def cmd_status(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        p = self._load_players().get(user_id)
        if not p:
            yield event.plain_result("❌ 请先注册：/花月 注册")
            return
        a = p["attributes"]
        yield event.plain_result(f"""【{p['nickname']} 的状态】
Lv.{p['level']} | {p['faction']}

❤️ 生命：{p['hp']}/{p['max_hp']}
⚡ 体力：{p['stamina']}/{p['max_stamina']}
💰 金币：{p['gold']}

【六维属性】
💪 力量：{a['strength']}  🏃 敏捷：{a['agility']}
🛡️ 体质：{a['constitution']}  🧠 智力：{a['intelligence']}
👁️ 感知：{a['perception']}  🍀 运气：{a['luck']}

【进度】探索 {p['exploration_count']} 次""")

    @group.command("成就")
    async def cmd_achievements(self, event: AstrMessageEvent):
        user_id = event.get_sender_id()
        achievements = self._load_achievements()
        
        ach_list = achievements.get(user_id, [])
        if not ach_list:
            yield event.plain_result("🏆 还没有获得任何成就，快去探索吧！")
            return
        
        msg = "【成就列表】\n\n"
        for ach in ach_list:
            msg += f"✨ {ach['name']}\n   {ach['description']}\n\n"
        
        msg += f"已获得 {len(ach_list)} 个成就"
        yield event.plain_result(msg)

    @group.command("帮助")
    async def cmd_help(self, event: AstrMessageEvent):
        yield event.plain_result("""【二周目花月 - 指令大全】

🎮 基础指令：
/花月 注册 [阵营] - 注册新玩家
/花月 阵营 - 查看所有可选阵营
/花月 属性 力 敏 体 智 感 运 - 分配属性
/花月 状态 - 查看角色状态
/花月 成就 - 查看成就

🗺️ 探索指令：
/花月 探索 - 开始一次探索（消耗10体力）
/花月 移动 上/下/左/右 - 在地图上移动

💡 提示：
- 每个探索最多触发2个支线剧情
- 走到右下角⭐位置触发主线推进""")

    async def terminate(self):
        self.player_sessions.clear()
        logger.info("🌸 二周目花月插件已卸载")
