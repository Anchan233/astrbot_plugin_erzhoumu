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


# ==================== 游戏配置 ====================

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
    {"name": "致幻孢子", "desc": "在丛林中被致幻孢子感染，产生了奇怪的幻觉...", "achievement": "幻觉行者"},
    {"name": "垃圾回收机", "desc": "找到了一台还在运作的垃圾回收机", "achievement": "环保主义者"},
    {"name": "自动贩卖机", "desc": "发现了一台还能使用的自动贩卖机", "achievement": "幸运儿"},
    {"name": "医疗箱", "desc": "在废墟中发现了一个完好的医疗箱", "achievement": "医疗兵"}
]

MAP_TILES = ["⬜", "🏚️", "🛒", "🏥", "🌲", "🛤️", "💧", "🌳", "🏭", "🏫"]


# ==================== 插件主类 ====================

class ErZhouMuPlugin(Star):
    """二周目花月 - 末世生存RPG游戏"""
    
    def __init__(self, context: Context):
        super().__init__(context)
        
        # 数据目录
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # 数据文件
        self.players_file = self.data_dir / "players.json"
        self.achievements_file = self.data_dir / "achievements.json"
        
        # 初始化数据文件
        self._init_data_files()
        
        # 玩家会话缓存
        self.player_sessions: Dict[str, Dict[str, Any]] = {}
        
        logger.info("🌸 二周目花月插件加载成功！")

    def _init_data_files(self):
        """初始化数据文件"""
        if not self.players_file.exists():
            with open(self.players_file, "w", encoding="utf-8") as f:
                json.dump({}, f)
        
        if not self.achievements_file.exists():
            with open(self.achievements_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    def _load_players(self) -> Dict:
        """加载玩家数据"""
        with open(self.players_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_players(self, data: Dict):
        """保存玩家数据"""
        with open(self.players_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_achievements(self) -> Dict:
        """加载成就数据"""
        with open(self.achievements_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_achievements(self, data: Dict):
        """保存成就数据"""
        with open(self.achievements_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _format_map(self, size: int = 8, current_x: int = 0, current_y: int = 0) -> str:
        """格式化地图显示"""
        output = "【探索地图】\n"
        output += "  " + " ".join([f"{i:2d}" for i in range(size)]) + "\n"
        
        for y in range(size):
            row = f"{y:2d} "
            for x in range(size):
                if x == current_x and y == current_y:
                    row += "🧍 "
                elif x == size - 1 and y == size - 1:
                    row += "⭐ "
                elif x == 0 and y == 0:
                    row += "🏠 "
                else:
                    seed = (x * 13 + y * 7) % len(MAP_TILES)
                    row += MAP_TILES[seed] + " "
            output += row + "\n"
        
        output += "\n🧍=你  ⭐=主线  🏠=安全区"
        return output

    # ==================== 主指令组 ====================

    @filter.command_group("花月")
    def erzhoumu_group(self):
        """二周目花月游戏主指令组"""
        pass

    # ==================== 玩家指令 ====================

    @erzhoumu_group.command("注册")
    async def cmd_register(self, event: AstrMessageEvent, faction: str = "流浪者"):
        """注册玩家，可选指定阵营"""
        user_id = event.get_sender_id()
        nickname = event.sender.nickname if hasattr(event.sender, 'nickname') else "无名冒险者"
        
        players = self._load_players()
        
        if user_id in players:
            yield event.plain_result("❌ 你已经注册过了！")
            return
        
        if faction not in FACTIONS:
            yield event.plain_result(f"❌ 无效阵营，可选：{'、'.join(FACTIONS.keys())}")
            return
        
        base_points = 30 + FACTIONS[faction]["bonus_points"]
        
        players[user_id] = {
            "nickname": nickname,
            "faction": faction,
            "level": 1,
            "exp": 0,
            "hp": 100,
            "max_hp": 100,
            "stamina": 100,
            "max_stamina": 100,
            "gold": 0,
            "attributes": {
                "strength": 5, "agility": 5, "constitution": 5,
                "intelligence": 5, "perception": 5, "luck": 5
            },
            "exploration_count": 0,
            "mainline_stage": 1,
            "attribute_points": base_points
        }
        self._save_players(players)
        
        yield event.plain_result(f"""✅ {nickname} 注册成功！

【你的信息】
🎭 阵营：{faction}
📊 可用属性点：{base_points}

💡 使用：/花月 属性 力 敏 体 智 感 运
例：/花月 属性 10 10 5 5 5 5""")

    @erzhoumu_group.command("阵营")
    async def cmd_factions(self, event: AstrMessageEvent):
        """查看所有可选阵营"""
        msg = "【可选阵营】\n\n"
        for name, config in FACTIONS.items():
            msg += f"🎭 {name}\n"
            msg += f"   {config['description']}\n"
            msg += f"   额外点数：+{config['bonus_points']}\n\n"
        msg += "💡 注册时指定：/花月 注册 炊事班供餐部"
        yield event.plain_result(msg)

    @erzhoumu_group.command("属性")
    async def cmd_attributes(
        self, event: AstrMessageEvent,
        strength: int = 5, agility: int = 5, constitution: int = 5,
        intelligence: int = 5, perception: int = 5, luck: int = 5
    ):
        """分配六维属性：力量 敏捷 体质 智力 感知 运气"""
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

    @erzhoumu_group.command("状态")
    async def cmd_status(self, event: AstrMessageEvent):
        """查看你的角色状态"""
        user_id = event.get_sender_id()
        players = self._load_players()
        
        if user_id not in players:
            yield event.plain_result("❌ 请先注册：/花月 注册")
            return
        
        p = players[user_id]
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

【进度】
🗺️ 探索次数：{p['exploration_count']}
📖 主线阶段：{p['mainline_stage']}
""")

    @erzhoumu_group.command("探索")
    async def cmd_explore(self, event: AstrMessageEvent):
        """开始一次探索（消耗10点体力）"""
        user_id = event.get_sender_id()
        players = self._load_players()
        
        if user_id not in players:
            yield event.plain_result("❌ 请先注册：/花月 注册")
            return
        
        if players[user_id]["stamina"] < 10:
            yield event.plain_result("❌ 体力不足！需要 10 点体力")
            return
        
        players[user_id]["stamina"] -= 10
        players[user_id]["exploration_count"] += 1
        self._save_players(players)
        
        self.player_sessions[user_id] = {
            "x": 0,
            "y": 0,
            "sidequests_triggered": 0
        }
        
        yield event.plain_result(f"""✅ 开始探索！

{self._format_map(8, 0, 0)}

💡 指令：
/花月 移动 上/下/左/右 - 移动到相邻格子""")

    @erzhoumu_group.command("移动")
    async def cmd_move(self, event: AstrMessageEvent, direction: str = ""):
        """在地图上移动：上/下/左/右"""
        user_id = event.get_sender_id()
        
        if user_id not in self.player_sessions:
            yield event.plain_result("❌ 你还没有开始探索！\n使用：/花月 探索")
            return
        
        direction_map = {"上": (0, -1), "下": (0, 1), "左": (-1, 0), "右": (1, 0)}
        
        if direction not in direction_map:
            yield event.plain_result("❌ 方向只能是：上、下、左、右")
            return
        
        dx, dy = direction_map[direction]
        session = self.player_sessions[user_id]
        new_x = session["x"] + dx
        new_y = session["y"] + dy
        
        if new_x < 0 or new_x >= 8 or new_y < 0 or new_y >= 8:
            yield event.plain_result("❌ 无法移动到地图外！")
            return
        
        session["x"] = new_x
        session["y"] = new_y
        
        msg = f"📍 移动到 ({new_x}, {new_y})\n\n"
        
        # 随机触发支线
        if session["sidequests_triggered"] < 2 and random.random() < 0.3:
            q = random.choice(SIDEQUESTS)
            msg += f"【支线触发】✨ {q['name']}\n{q['desc']}\n\n"
            session["sidequests_triggered"] += 1
            
            # 记录成就
            achievements = self._load_achievements()
            if user_id not in achievements:
                achievements[user_id] = []
            
            if q["achievement"] not in [a["name"] for a in achievements[user_id]]:
                achievements[user_id].append({
                    "name": q["achievement"],
                    "description": f"完成支线：{q['name']}"
                })
                self._save_achievements(achievements)
                msg += f"🏆 获得成就：{q['achievement']}\n\n"
        
        if new_x == 7 and new_y == 7:
            msg += "⭐ 【主线触发】你抵达了命运的交汇点...\n\n"
        
        msg += self._format_map(8, new_x, new_y)
        yield event.plain_result(msg)

    @erzhoumu_group.command("背包")
    async def cmd_inventory(self, event: AstrMessageEvent):
        """查看背包物品"""
        yield event.plain_result("📦 背包是空的")

    @erzhoumu_group.command("成就")
    async def cmd_achievements(self, event: AstrMessageEvent):
        """查看已获得的成就"""
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

    @erzhoumu_group.command("帮助")
    async def cmd_help(self, event: AstrMessageEvent):
        """显示帮助信息"""
        yield event.plain_result("""【二周目花月 - 指令大全】

🎮 基础指令：
/花月 注册 [阵营] - 注册新玩家
/花月 阵营 - 查看所有可选阵营
/花月 属性 力 敏 体 智 感 运 - 分配属性
/花月 状态 - 查看角色状态
/花月 背包 - 查看背包物品
/花月 成就 - 查看成就

🗺️ 探索指令：
/花月 探索 - 开始一次探索（消耗10体力）
/花月 移动 上/下/左/右 - 在地图上移动

💡 提示：
- 每个探索最多触发2个支线剧情
- 走到右下角⭐位置触发主线推进""")

    # ==================== 生命周期 ====================

    async def terminate(self):
        """插件卸载时清理"""
        self.player_sessions.clear()
        logger.info("🌸 二周目花月插件已卸载")
