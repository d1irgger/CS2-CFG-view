# cs2cfgviewernew.py
# CS2 CFG Viewer · PyWebView 版本
# 白色液态玻璃风格 · 保留全部核心功能
# 环境：Python 3.10+ / pywebview

from __future__ import annotations

import json
import re
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

import webview


# ==========================================================
# DPI 感知
# ==========================================================

def _ensure_dpi_aware():
    if not sys.platform.startswith("win"):
        return
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            return
        except Exception:
            pass
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
    except Exception:
        pass


_ensure_dpi_aware()


# ==========================================================
# 应用元信息
# ==========================================================

APP_NAME    = "CS2 CFG Viewer"
APP_VERSION = "3.0.0"
APP_AUTHOR  = "D1r3ctor"

GITHUB_URL   = "https://github.com/d1irgger/CS2-CFG-view"
TELEGRAM_URL = "https://t.me/timharrys"

STEAM_PLACEHOLDER = "选择 Steam 目录，或用 ProSettings 下载解析 autoexec"


# ==========================================================
# 按键名规范化
# ==========================================================

def normalize_key_name(name: str) -> str:
    if not name:
        return ""
    n = name.strip()
    if n.lower().startswith("key_"):
        n = n[4:]
    return n.lower()


# ==========================================================
# 按键名字典（保留全部）
# ==========================================================

KEY_NAME_CN = {
    "mouse1": "鼠标左键", "mouse2": "鼠标右键", "mouse3": "鼠标中键",
    "mouse4": "鼠标侧键1", "mouse5": "鼠标侧键2",
    "mouse6": "鼠标附加键6", "mouse7": "鼠标附加键7", "mouse8": "鼠标附加键8",
    "mwheelup": "滚轮上", "mwheeldown": "滚轮下",
    "mouse_x": "鼠标水平轴（视角）", "mouse_y": "鼠标垂直轴（视角）",
    "mouse_wheel": "鼠标滚轮",
    **{c: c.upper() for c in "abcdefghijklmnopqrstuvwxyz"},
    **{str(n): str(n) for n in range(10)},
    **{f"f{n}": f"F{n}" for n in range(1, 13)},
    "shift": "Shift", "rshift": "右 Shift", "lshift": "左 Shift",
    "ctrl": "Ctrl", "control": "Ctrl", "rctrl": "右 Ctrl", "lctrl": "左 Ctrl",
    "alt": "Alt", "ralt": "右 Alt", "lalt": "左 Alt",
    "capslock": "CapsLock", "numlock": "NumLock", "scrolllock": "ScrollLock",
    "space": "空格", "tab": "Tab", "enter": "回车", "return": "回车",
    "escape": "Esc", "esc": "Esc", "backspace": "退格",
    "del": "Del", "delete": "Del", "ins": "Ins", "insert": "Ins",
    "home": "Home", "end": "End",
    "pgup": "PgUp", "pgdn": "PgDn",
    "pageup": "PgUp", "pagedown": "PgDn",
    "pause": "Pause", "break": "Break",
    "printscreen": "PrtSc", "sysreq": "SysRq",
    "up": "方向键 上", "down": "方向键 下",
    "left": "方向键 左", "right": "方向键 右",
    "uparrow": "方向键 上", "downarrow": "方向键 下",
    "leftarrow": "方向键 左", "rightarrow": "方向键 右",
    **{f"kp_{n}": f"小键盘 {n}" for n in range(10)},
    "kp_ins": "小键盘 Ins", "kp_del": "小键盘 Del", "kp_end": "小键盘 End",
    "kp_down": "小键盘 下", "kp_pgdn": "小键盘 PgDn",
    "kp_left": "小键盘 左", "kp_right": "小键盘 右",
    "kp_home": "小键盘 Home", "kp_up": "小键盘 上", "kp_pgup": "小键盘 PgUp",
    "kp_slash": "小键盘 /", "kp_divide": "小键盘 /",
    "kp_multiply": "小键盘 *",
    "kp_minus": "小键盘 -", "kp_plus": "小键盘 +",
    "kp_enter": "小键盘 回车", "kp_period": "小键盘 .",
    "kp_decimal": "小键盘 .",
    "semicolon": ";", "apostrophe": "'", "comma": ",", "period": ".",
    "slash": "/", "backslash": "反斜杠",
    "lbracket": "[", "rbracket": "]",
    "minus": "-", "equal": "=", "backtick": "`", "grave": "`",
    '"': "引号键",
    "\\": "反斜杠",
}


# ==========================================================
# 命令字典（保留全部）
# ==========================================================

CMD_NAME_CN = {
    "+attack": "开火", "-attack": "松开开火",
    "+attack2": "副开火/右键", "-attack2": "松开副开火",
    "+attack3": "第三开火", "-attack3": "松开第三开火",
    "+forward": "前进", "-forward": "松开前进",
    "+back": "后退", "-back": "松开后退",
    "+moveleft": "左移", "-moveleft": "松开左移",
    "+moveright": "右移", "-moveright": "松开右移",
    "+left": "左转", "-left": "松开左转",
    "+right": "右转", "-right": "松开右转",
    "+up": "上浮/向上", "-up": "松开向上",
    "+down": "下潜/向下", "-down": "松开向下",
    "+jump": "跳跃", "-jump": "松开跳跃",
    "+duck": "蹲下", "-duck": "松开蹲下",
    "+sprint": "冲刺（按住）", "-sprint": "松开冲刺",
    "+speed": "静步/慢走", "-speed": "松开静步",
    "+walk": "静步/慢走", "-walk": "松开静步",
    "+use": "使用/互动", "-use": "松开使用", "use": "使用",
    "+reload": "换弹", "-reload": "松开换弹",
    "drop": "丢弃武器", "+drop": "丢弃武器",
    "+lookup": "视角上抬", "+lookdown": "视角下压",
    "+mlook": "鼠标控制视角", "+klook": "键盘控制视角",
    "+zoom": "开镜", "-zoom": "松开开镜",
    "+lookatweapon": "检视武器", "-lookatweapon": "停止检视",
    "inspect": "检视",
    "yaw": "偏航（水平视角）", "pitch": "俯仰（垂直视角）",
    "+showscores": "显示比分", "-showscores": "关闭比分",
    "+voicerecord": "语音", "-voicerecord": "松开语音",
    "+radialradio": "无线电轮盘",
    "+radialradio2": "无线电轮盘 2", "+radialradio3": "无线电轮盘 3",
    "+spray_menu": "喷漆菜单",
    "+cl_show_team_equipment": "显示队友装备",
    "cl_show_team_equipment": "显示队友装备",
    "cl_showpos": "显示坐标",
    "toggleradarscale": "切换雷达缩放",
    "show_loadout_toggle": "显示/隐藏装备栏",
    "show_loadout_toggle_off": "隐藏装备栏",
    "toggleconsole": "切换控制台",
    "jpeg": "截图", "screenshot": "截图",
    "play": "播放音效", "playvol": "按音量播放音效",
    "teamtoggle": "切换队伍", "teammenu": "队伍菜单",
    "noclip": "穿墙", "impulse": "impulse 命令",
    "bot_place": "放置机器人",
    "mute": "静音",
    "pause": "暂停",
    "quit": "退出游戏",
    "quit prompt": "退出游戏（带确认）",
    "slot1": "主武器", "slot2": "副武器", "slot3": "近战刀",
    "slot4": "手雷", "slot5": "C4",
    "slot6": "道具 6", "slot7": "道具 7", "slot8": "道具 8",
    "slot9": "道具 9", "slot10": "道具 10",
    "slot11": "道具 11", "slot12": "道具 12",
    "invnext": "下一个武器", "invprev": "上一个武器",
    "lastinv": "上一个武器", "switchhands": "换手",
    "say": "全体发言", "say_team": "队伍发言",
    "messagemode": "全体聊天", "messagemode2": "队伍聊天",
    "messagemode3": "聊天模式 3",
    "radio": "无线电", "radio1": "无线电 1",
    "radio2": "无线电 2", "radio3": "无线电 3",
    "player_ping": "玩家标记（Ping）",
    "buy": "购买菜单", "buymenu": "购买菜单",
    "buyammo1": "购买主武器弹药", "buyammo2": "购买副武器弹药",
    "autobuy": "自动购买", "rebuy": "重复上次购买",
    "sellbackall": "退回全部购买", "cancelselect": "取消当前选择",
    "cs_quit_prompt": "退出游戏确认",
    "callvote": "发起投票", "vote": "投票",
    "save": "存档", "load": "读档",
    "save quick": "快速存档", "load quick": "快速读档",
    "quick_save": "快速存档", "quick_load": "快速读档",
    "<unbound>": "未绑定",
    "weapon_ak47": "AK-47", "weapon_m4a1": "M4A4",
    "weapon_m4a1_silencer": "M4A1-S", "weapon_awp": "AWP",
    "weapon_deagle": "沙漠之鹰", "weapon_usp_silencer": "USP-S",
    "weapon_hkp2000": "P2000", "weapon_glock": "Glock-18",
    "weapon_p250": "P250", "weapon_fiveseven": "Five-SeveN",
    "weapon_tec9": "Tec-9", "weapon_elite": "双持贝瑞塔",
    "weapon_galilar": "Galil AR", "weapon_famas": "FAMAS",
    "weapon_sg556": "SG 553", "weapon_aug": "AUG",
    "weapon_ssg08": "SSG 08", "weapon_scar20": "SCAR-20",
    "weapon_g3sg1": "G3SG1", "weapon_nova": "Nova",
    "weapon_xm1014": "XM1014", "weapon_mag7": "MAG-7",
    "weapon_sawedoff": "Sawed-Off", "weapon_m249": "M249",
    "weapon_negev": "Negev", "weapon_mac10": "MAC-10",
    "weapon_mp9": "MP9", "weapon_mp7": "MP7",
    "weapon_mp5sd": "MP5-SD", "weapon_ump45": "UMP-45",
    "weapon_p90": "P90", "weapon_bizon": "PP-Bizon",
    "weapon_hegrenade": "高爆手雷", "weapon_flashbang": "闪光弹",
    "weapon_smokegrenade": "烟雾弹", "weapon_molotov": "燃烧瓶",
    "weapon_incgrenade": "燃烧弹", "weapon_decoy": "诱饵弹",
    "weapon_taser": "电击枪", "weapon_c4": "C4",
    "weapon_knife": "刀", "weapon_knife_t": "T 刀",
    "weapon_knife_karambit": "爪子刀", "weapon_healthshot": "医疗针",
    "vest": "防弹衣", "vesthelm": "防弹衣 + 头盔",
    "defuser": "拆弹器", "taser": "电击枪",
    "item_assaultsuit": "防弹衣 + 头盔",
    "item_kevlar": "防弹衣", "item_defuser": "拆弹器",
    "r_cleardecals": "清除血迹",
}


def _lookup(dic: dict, key: str) -> Optional[str]:
    if not key:
        return None
    v = dic.get(key)
    if v is not None:
        return v
    v = dic.get(key.lower())
    if v is not None:
        return v
    if key[0] in "+-":
        base = key[1:]
        v = dic.get(base)
        if v is not None:
            return v
        v = dic.get(base.lower())
        if v is not None:
            return v
    return None


def translate_key_local(key: str) -> Optional[str]:
    return KEY_NAME_CN.get(normalize_key_name(key))


# ==========================================================
# 设置项字典（精简版 · 保留高频核心项）
# ==========================================================

VIDEO_NAME_CN = {
    # ---- 视频 / 显示 ----
    "Version": "版本", "VendorID": "厂商 ID",
    "DeviceID": "设备 ID", "Autoconfig": "自动配置等级",
    "setting.defaultres": "分辨率宽度",
    "setting.defaultresheight": "分辨率高度",
    "setting.fullscreen": "全屏模式",
    "setting.coop_fullscreen": "合作模式全屏",
    "setting.fullscreen_min_on_focus_loss": "失焦时最小化全屏",
    "setting.nowindowborder": "无边框窗口",
    "setting.high_dpi": "高 DPI 缩放",
    "setting.aspectratiomode": "宽高比模式",
    "setting.aspectranormal": "宽高比模式",
    "setting.refreshrate_numerator": "刷新率（分子）",
    "setting.refreshrate_denominator": "刷新率（分母）",
    "setting.refreshrate_default": "默认刷新率",
    "setting.monitor_index": "显示器索引",
    "setting.knowndevice": "已知设备标记",

    # ---- 图形 ----
    "setting.mat_vsync": "垂直同步",
    "setting.mat_triplebuffered": "三重缓冲",
    "setting.mat_queue_mode": "多线程渲染模式",
    "setting.mat_monitorgamma": "显示器伽马",
    "setting.mat_monitorgamma_tv_enabled": "电视伽马",
    "setting.gpu_level": "GPU 性能等级",
    "setting.gpu_mem_level": "显存等级",
    "setting.cpu_level": "CPU 性能等级",
    "setting.r_low_latency": "低延迟模式",
    "setting.shaderquality": "着色器质量",
    "setting.texturequality": "纹理质量",
    "setting.detailquality": "细节质量",
    "setting.particlequality": "粒子质量",
    "setting.shadowquality": "阴影质量",
    "setting.r_texturefilteringquality": "纹理过滤质量",
    "setting.msaa_samples": "MSAA 采样数",
    "setting.r_csgo_cmaa_enable": "CMAA 抗锯齿",
    "setting.videocfg_shadow_quality": "阴影质量",
    "setting.videocfg_dynamic_shadows": "动态阴影",
    "setting.videocfg_texture_detail": "纹理细节",
    "setting.videocfg_particle_detail": "粒子细节",
    "setting.videocfg_ao_detail": "环境光遮蔽细节",
    "setting.videocfg_hdr_detail": "HDR 细节",
    "setting.videocfg_fsr_detail": "FSR 细节",
    "setting.r_csgo_shadows_quality": "阴影质量",
    "setting.r_csgo_water_effects": "水面效果",
    "setting.r_csgo_water_reflections": "水面反射",
    "setting.r_csgo_particle_quality": "粒子质量",
    "setting.r_csgo_character_quality": "角色质量",
    "setting.r_csgo_boost_player_contrast": "增强玩家对比度",
    "setting.r_csgo_ui_contrast": "UI 对比度",
    "setting.r_csgo_motion_blur": "动态模糊",
    "setting.r_csgo_texture_filtering_mode": "纹理过滤模式",
    "setting.optional_user_active_weapon_bloom": "武器动态模糊",
    "setting.cl_predict": "客户端预测",
    "setting.frame_rate_max": "最大帧率",
    "setting.num_workers": "工作线程数",
    "setting.multicore": "多核渲染",
    "setting.mat_shader_cache": "着色器缓存",

    # ---- 音频 ----
    "volume": "音量",
    "snd_musicvolume": "音乐音量",
    "snd_gamevolume": "游戏音量",
    "snd_voipvolume": "语音音量",
    "snd_menumusic_volume": "菜单音乐音量",
    "snd_mute_losefocus": "失焦时静音",
    "snd_mute_mvp_music_live_players": "屏蔽 MVP 音乐（真人玩家）",
    "snd_autodetect_latency": "自动检测延迟",
    "snd_mixahead": "音频预混时间",
    "snd_headphone_eq": "耳机均衡器",
    "snd_spatialize_lerp": "空间化插值",
    "snd_steamaudio_enable_perspective_correction": "Steam Audio 透视校正",
    "snd_deathcamera_volume": "死亡镜头音量",
    "snd_mapobjective_volume": "地图目标音效音量",
    "snd_mvp_volume": "MVP 音量",
    "snd_roundaction_volume": "回合动作音量",
    "snd_roundend_volume": "回合结束音量",
    "snd_roundstart_volume": "回合开始音量",
    "snd_tensecondwarning_volume": "十秒警告音量",
    "snd_duckerattacktime": "闪避攻击时间",
    "snd_duckerreleasetime": "闪避释放时间",
    "snd_duckerthreshold": "闪避阈值",
    "snd_ducktovolume": "闪避到音量",
    "snd_toolvolume": "工具音量",
    "speaker_config": "扬声器配置",
    "dsp_volume": "DSP 音量",

    # ---- 语音 ----
    "voice_scale": "语音音量",
    "voice_threshold": "语音激活阈值",
    "voice_modenable": "启用语音",
    "voice_always_sample_mic": "始终采样麦克风",
    "voice_vox": "语音激活模式",

    # ---- 网络 ----
    "rate": "网络速率",
    "net_allow_multicast": "允许组播",
    "net_maxroutable": "最大可路由大小",
    "cl_interp": "插值时间",
    "cl_interp_ratio": "插值比率",
    "cl_lagcompensation": "延迟补偿",
    "cl_predictweapons": "客户端预测武器",
    "cl_net_buffer_ticks": "网络缓冲 tick",
    "cl_timeout": "网络超时",
    "sv_voiceenable": "启用服务器语音",
    "sv_skyname": "天空盒名称",
    "tv_nochat": "屏蔽观战聊天",
    "mm_csgo_community_search_players_min": "社区搜索最少玩家数",
    "mm_dedicated_search_maxping": "专用服务器最大 Ping",

    # ---- HUD / 准星 ----
    "hud_scaling": "HUD 缩放",
    "hud_showtargetid": "显示目标 ID",
    "hud_fastswitch": "快速切换武器",
    "cl_crosshaircolor": "准星颜色",
    "cl_crosshaircolor_r": "准星颜色红",
    "cl_crosshaircolor_g": "准星颜色绿",
    "cl_crosshaircolor_b": "准星颜色蓝",
    "cl_crosshairalpha": "准星透明度",
    "cl_crosshairdot": "准星中心点",
    "cl_crosshairsize": "准星大小",
    "cl_crosshairthickness": "准星粗细",
    "cl_crosshairgap": "准星间距",
    "cl_crosshairstyle": "准星样式",
    "cl_crosshair_drawoutline": "准星外描边",
    "cl_crosshair_outlinethickness": "准星描边粗细",
    "cl_crosshair_recoil": "准星跟随后坐力",
    "cl_crosshair_sniper_width": "狙击准星线宽",
    "cl_crosshair_t": "T 形准星",
    "cl_crosshairgap_useweaponvalue": "准星间距使用武器值",
    "cl_crosshairusealpha": "准星使用透明度",
    "cl_crosshair_friendly_warning": "准星友方警告",
    "cl_fixedcrosshairgap": "固定准星间距",
    "cl_ironsight_dot_scale": "机瞄点缩放",
    "cl_ironsight_usecrosshaircolor": "机瞄使用准星颜色",
    "crosshair": "启用准星",

    # ---- 雷达 ----
    "cl_radar_scale": "雷达缩放",
    "cl_radar_always_centered": "雷达始终居中",
    "cl_radar_rotate": "雷达旋转",
    "cl_radar_icon_scale_min": "雷达图标最小缩放",
    "cl_radar_square_with_scoreboard": "比分板时雷达方形",
    "cl_radar_square_always": "雷达始终方形",
    "cl_radar_square_when_spectating": "观察时雷达方形",
    "cl_radar_scale_dynamic": "动态雷达缩放",
    "cl_radar_show_all_players_when_spectating": "观察时显示所有玩家",
    "cl_hud_radar_scale": "HUD 雷达缩放",
    "cl_hud_radar_background_alpha": "雷达背景透明度",
    "cl_hud_radar_blur_background": "雷达背景模糊",
    "cl_hud_radar_map_additive": "雷达地图叠加",

    # ---- 队友标识 ----
    "cl_teamid_overhead_always": "始终显示队友标识",
    "cl_teamid_overhead_mode": "队友标识模式",
    "cl_teamid_overhead_colors_show": "显示队友标识颜色",
    "cl_teamid_overhead_fade_near_crosshair": "队友标识在准星附近淡出",
    "cl_teammate_colors_show": "队友颜色",
    "cl_show_clan_in_death_notice": "死亡提示显示战队",

    # ---- 视角模型 ----
    "viewmodel_fov": "视角模型 FOV",
    "viewmodel_offset_x": "视角模型 X 偏移",
    "viewmodel_offset_y": "视角模型 Y 偏移",
    "viewmodel_offset_z": "视角模型 Z 偏移",
    "viewmodel_presetpos": "视角模型预设位置",
    "viewmodel_recoil": "视角模型后坐力",
    "cl_righthand": "右手持枪",
    "cl_prefer_lefthanded": "偏好左手",
    "cl_bob": "视角摆动",
    "cl_bobcycle": "视角摆动周期",
    "cl_bob_lower_amt": "视角摆动下限",
    "cl_bobamt_lat": "横向摆动幅度",
    "cl_bobamt_vert": "纵向摆动幅度",

    # ---- 鼠标 ----
    "sensitivity": "鼠标灵敏度",
    "zoom_sensitivity_ratio": "开镜灵敏度倍率",
    "zoom_sensitivity_ratio_mouse": "开镜灵敏度倍率（鼠标）",
    "sensitivity_y_scale": "Y 轴灵敏度倍率",
    "m_yaw": "鼠标水平灵敏度",
    "m_pitch": "鼠标垂直灵敏度",
    "m_rawinput": "原始鼠标输入",
    "m_customaccel": "自定义鼠标加速",
    "m_customaccel_exponent": "鼠标加速指数",
    "m_customaccel_max": "鼠标加速上限",
    "m_customaccel_scale": "鼠标加速系数",
    "m_mousespeed": "鼠标速度",
    "mouse_inverty": "鼠标 Y 轴反转",

    # ---- 玩家 / 杂项 ----
    "name": "玩家名称",
    "cl_clanid": "战队 ID",
    "cl_color": "颜色",
    "cl_hud_color": "HUD 颜色",
    "fov_desired": "视野 FOV",
    "fps_max": "最大帧率",
    "fps_max_ui": "UI 最大帧率",
    "con_enable": "启用控制台",
    "con_allownotify": "允许控制台通知",
    "cl_showloadout": "显示装备栏",
    "cl_autowepswitch": "自动切换拾取武器",
    "cl_use_opens_buy_menu": "使用键打开购买菜单",
    "cl_disable_round_end_report": "禁用回合结束报告",
    "cl_allow_animated_avatars": "允许动态头像",
    "cl_autohelp": "自动帮助提示",
    "cl_versus_intro": "对战开场动画",
    "cl_weapon_selection_rarity_color": "武器选择稀有度着色",
    "cl_quickinventory_filename": "快速库存文件名",
    "cl_quickinventory_lastinv": "快速库存使用上次武器",
    "cl_quickinventory_line_update_speed": "快速库存行更新速度",
    "cl_inventory_radial_immediate_select": "库存转盘立即选择",
    "cl_inventory_radial_tap_to_cycle": "库存转盘点击循环",
    "cl_buywheel_donate_key": "购买轮盘捐赠键",
    "cl_buywheel_nomousecentering": "购买轮盘禁用鼠标居中",
    "cl_buywheel_nonumberpurchasing": "购买轮盘禁用数字购买",
    "cl_chatfilters": "聊天过滤",
    "cl_mute_all_but_friends_and_party": "仅队友和好友语音",
    "cl_mute_enemy_team": "屏蔽敌方语音",
    "cl_playerspray_auto_apply": "喷漆自动应用",
    "cl_player_ping_mute": "玩家标记静音",
    "cl_ping_fade_deadzone": "标记淡出死区",
    "cl_ping_fade_distance": "标记淡出距离",
    "cl_sanitize_player_names": "过滤玩家名称",
    "cl_scoreboard_mouse_enable_binding": "比分板启用鼠标绑定",
    "cl_scoreboard_survivors_always_on": "比分板始终显示存活者",
    "cl_show_observer_crosshair": "显示观战准星",
    "cl_thirdperson": "第三人称",
    "cl_auto_cursor_scale": "自动缩放光标",
    "cl_cursor_scale": "光标缩放",
    "cl_debounce_zoom": "开镜防抖",
    "cl_sniper_auto_rezoom": "狙击自动重新开镜",
    "cl_sniper_delay_unscope": "狙击延迟收镜",
    "cl_sniper_show_inaccuracy": "显示狙击不准度",
    "cl_enable_party_voice": "启用组队语音",

    # ---- 视觉 / 血液 ----
    "violence_ablood": "血液效果",
    "violence_agibs": "碎尸效果",
    "violence_hblood": "人类血液效果",
    "violence_hgibs": "人类碎尸效果",
    "r_drawtracers_firstperson": "第一人称曳光弹",
    "r_fullscreen_gamma": "全屏伽马",
    "r_player_visibility_mode": "玩家可见性模式",
    "r_spectator_flashbang_opacity": "观战闪光弹不透明度",

    # ---- 观察 / 回放 ----
    "spec_centerchasecam": "居中追踪镜头",
    "spec_replay_autostart": "回放自动开始",
    "spec_show_xray": "显示 X 光",
    "spec_usenumberkeys_nobinds": "使用数字键切换玩家",

    # ---- 蹲/走方式 ----
    "option_duck_method": "蹲下方式",
    "option_speed_method": "慢走方式",
}


# ==========================================================
# 设置项值字典（精简版）
# ==========================================================

VIDEO_VALUE_CN = {
    # ---- 视频 ----
    "setting.fullscreen": {"0": "窗口化", "1": "全屏", "2": "窗口化（无边框）"},
    "setting.coop_fullscreen": {"0": "关闭", "1": "开启"},
    "setting.nowindowborder": {"0": "否", "1": "是"},
    "setting.fullscreen_min_on_focus_loss": {"0": "关闭", "1": "开启"},
    "setting.high_dpi": {"0": "关闭", "1": "开启"},
    "setting.knowndevice": {"0": "未知", "1": "已知"},
    "setting.mat_vsync": {"0": "关闭", "1": "开启", "2": "双缓冲", "3": "三重缓冲"},
    "setting.mat_triplebuffered": {"0": "关闭", "1": "开启"},
    "setting.r_low_latency": {"0": "关闭", "1": "开启", "2": "超低延迟"},
    "setting.gpu_level": {"0": "低", "1": "中", "2": "高", "3": "极高"},
    "setting.gpu_mem_level": {"0": "低", "1": "中", "2": "高"},
    "setting.cpu_level": {"0": "低", "1": "中", "2": "高"},
    "setting.shaderquality": {"0": "低", "1": "中", "2": "高"},
    "setting.texturequality": {"0": "低", "1": "中", "2": "高"},
    "setting.detailquality": {"0": "低", "1": "中", "2": "高"},
    "setting.particlequality": {"0": "低", "1": "中", "2": "高"},
    "setting.shadowquality": {"0": "低", "1": "中", "2": "高"},
    "setting.r_texturefilteringquality": {
        "0": "双线性", "1": "三线性",
        "2": "各向异性 2x", "3": "各向异性 4x",
        "4": "各向异性 8x", "5": "各向异性 16x",
    },
    "setting.msaa_samples": {
        "0": "关闭", "2": "2x MSAA", "4": "4x MSAA", "8": "8x MSAA",
    },
    "setting.r_csgo_cmaa_enable": {"0": "关闭", "1": "开启"},
    "setting.videocfg_shadow_quality": {"0": "低", "1": "中", "2": "高"},
    "setting.videocfg_texture_detail": {"0": "低", "1": "中", "2": "高"},
    "setting.videocfg_particle_detail": {"0": "低", "1": "中", "2": "高"},
    "setting.videocfg_ao_detail": {"0": "关闭", "1": "低", "2": "高"},
    "setting.videocfg_hdr_detail": {"-1": "自动", "0": "关闭", "1": "开启"},
    "setting.videocfg_fsr_detail": {"0": "关闭", "1": "开启", "2": "高质量"},
    "setting.videocfg_dynamic_shadows": {"0": "关闭", "1": "开启"},
    "setting.aspectratiomode": {"0": "自动", "1": "4:3", "2": "16:9", "3": "16:10"},
    "setting.aspectranormal": {"0": "自动", "1": "4:3", "2": "16:9", "3": "16:10"},
    "setting.monitor_index": {"0": "主显示器", "1": "第二显示器"},
    "Autoconfig": {"0": "未配置", "1": "低配", "2": "中配", "3": "高配"},
    "setting.r_csgo_motion_blur": {"0": "关闭", "1": "开启"},
    "setting.r_csgo_boost_player_contrast": {"0": "关闭", "1": "开启"},
    "setting.r_csgo_shadows_quality": {"0": "低", "1": "中", "2": "高"},
    "setting.r_csgo_particle_quality": {"0": "低", "1": "中", "2": "高"},
    "setting.r_csgo_character_quality": {"0": "低", "1": "中", "2": "高"},
    "setting.r_csgo_water_effects": {"0": "关闭", "1": "开启"},
    "setting.r_csgo_water_reflections": {"0": "关闭", "1": "开启"},
    "setting.r_csgo_texture_filtering_mode": {
        "0": "双线性", "1": "三线性",
        "2": "各向异性 2x", "3": "各向异性 4x",
        "4": "各向异性 8x", "5": "各向异性 16x",
    },
    "setting.optional_user_active_weapon_bloom": {"0": "关闭", "1": "开启"},
    "setting.multicore": {"0": "关闭", "1": "开启"},
    "setting.snd_mute_losefocus": {"0": "关闭", "1": "开启"},
    "setting.mat_monitorgamma_tv_enabled": {"0": "关闭", "1": "开启"},
    "setting.cl_predict": {"0": "关闭", "1": "开启"},
    "setting.mat_shader_cache": {"0": "关闭", "1": "开启"},

    # ---- 常用值 ----
    "m_rawinput": {"0": "关闭", "1": "开启"},
    "m_customaccel": {"0": "关闭", "1": "默认", "2": "经典", "3": "自定义"},
    "cl_righthand": {"0": "左手", "1": "右手"},
    "cl_prefer_lefthanded": {"0": "否", "1": "是"},
    "cl_showloadout": {"0": "关闭", "1": "开启"},
    "cl_autowepswitch": {"0": "关闭", "1": "开启"},
    "cl_use_opens_buy_menu": {"0": "关闭", "1": "开启"},
    "cl_crosshairdot": {"0": "关闭", "1": "开启"},
    "cl_crosshair_t": {"0": "关闭", "1": "开启"},
    "cl_crosshair_drawoutline": {"0": "关闭", "1": "开启"},
    "cl_crosshair_recoil": {"0": "关闭", "1": "开启"},
    "cl_crosshairgap_useweaponvalue": {"0": "关闭", "1": "开启"},
    "cl_crosshairusealpha": {"0": "关闭", "1": "开启"},
    "cl_crosshairstyle": {
        "0": "默认", "1": "默认静态", "2": "经典", "3": "经典动态",
        "4": "经典", "5": "经典动态",
    },
    "cl_crosshaircolor": {
        "0": "红", "1": "绿", "2": "黄", "3": "蓝",
        "4": "青", "5": "自定义",
    },
    "cl_crosshair_sniper_show_normal_inaccuracy": {"0": "关闭", "1": "开启"},
    "cl_crosshair_friendly_warning": {"0": "关闭", "1": "开启"},
    "hud_fastswitch": {"0": "关闭", "1": "开启", "2": "仅数字键"},
    "con_enable": {"0": "关闭", "1": "开启"},
    "con_allownotify": {"0": "关闭", "1": "开启"},
    "crosshair": {"0": "关闭", "1": "开启"},
    "cl_disable_round_end_report": {"0": "关闭", "1": "开启"},
    "cl_allow_animated_avatars": {"0": "关闭", "1": "开启"},
    "cl_autohelp": {"0": "关闭", "1": "开启"},
    "cl_versus_intro": {"0": "关闭", "1": "开启"},
    "cl_weapon_selection_rarity_color": {"0": "关闭", "1": "开启"},
    "cl_teamid_overhead_always": {"0": "关闭", "1": "开启"},
    "cl_teamid_overhead_mode": {"0": "关闭", "1": "仅颜色", "2": "完整"},
    "cl_radar_rotate": {"0": "关闭", "1": "开启"},
    "cl_radar_always_centered": {"0": "关闭", "1": "开启"},
    "cl_radar_scale_dynamic": {"0": "关闭", "1": "开启"},
    "cl_radar_square_always": {"0": "关闭", "1": "开启"},
    "cl_radar_square_when_spectating": {"0": "关闭", "1": "开启"},
    "cl_radar_square_with_scoreboard": {"0": "关闭", "1": "开启"},
    "cl_radar_show_all_players_when_spectating": {"0": "关闭", "1": "开启"},
    "cl_hud_radar_blur_background": {"0": "关闭", "1": "开启"},
    "cl_hud_radar_map_additive": {"0": "关闭", "1": "开启"},
    "cl_quickinventory_lastinv": {"0": "关闭", "1": "开启"},
    "cl_inventory_radial_immediate_select": {"0": "关闭", "1": "开启"},
    "cl_inventory_radial_tap_to_cycle": {"0": "关闭", "1": "开启"},
    "cl_teammate_colors_show": {"0": "关闭", "1": "开启"},
    "cl_teamid_overhead_colors_show": {"0": "关闭", "1": "开启"},
    "cl_sanitize_player_names": {"0": "关闭", "1": "开启"},
    "cl_show_clan_in_death_notice": {"0": "关闭", "1": "开启"},
    "cl_scoreboard_survivors_always_on": {"0": "关闭", "1": "开启"},
    "cl_predictweapons": {"0": "关闭", "1": "开启"},
    "cl_lagcompensation": {"0": "关闭", "1": "开启"},
    "snd_mute_losefocus": {"0": "关闭", "1": "开启"},
    "snd_mute_mvp_music_live_players": {"0": "关闭", "1": "开启"},
    "snd_autodetect_latency": {"0": "关闭", "1": "开启"},
    "snd_steamaudio_enable_perspective_correction": {"0": "关闭", "1": "开启"},
    "voice_modenable": {"0": "关闭", "1": "开启"},
    "voice_always_sample_mic": {"0": "关闭", "1": "开启"},
    "voice_vox": {"0": "按键说话", "1": "语音激活"},
    "violence_ablood": {"0": "关闭", "1": "开启"},
    "violence_agibs": {"0": "关闭", "1": "开启"},
    "violence_hblood": {"0": "关闭", "1": "开启"},
    "violence_hgibs": {"0": "关闭", "1": "开启"},
    "option_duck_method": {"0": "按住", "1": "切换"},
    "option_speed_method": {"0": "按住", "1": "切换"},
    "mouse_inverty": {"0": "关闭", "1": "开启"},
    "cl_debounce_zoom": {"0": "关闭", "1": "开启"},
    "cl_sniper_auto_rezoom": {"0": "关闭", "1": "开启"},
    "cl_sniper_show_inaccuracy": {"0": "关闭", "1": "开启"},
    "cl_sniper_delay_unscope": {"0": "关闭", "1": "开启"},
    "cl_ironsight_usecrosshaircolor": {"0": "关闭", "1": "开启"},
    "r_drawtracers_firstperson": {"0": "关闭", "1": "开启"},
    "r_player_visibility_mode": {"0": "默认", "1": "增强"},
    "spec_centerchasecam": {"0": "关闭", "1": "开启"},
    "spec_replay_autostart": {"0": "关闭", "1": "开启"},
    "spec_usenumberkeys_nobinds": {"0": "关闭", "1": "开启"},
    "snd_toolvolume": {"0": "静音", "1": "正常"},
    "sv_voiceenable": {"0": "关闭", "1": "开启",
                       "false": "关闭", "true": "开启"},
    "tv_nochat": {"0": "关闭", "1": "开启"},
    "net_allow_multicast": {"0": "关闭", "1": "开启"},
    "cl_enable_party_voice": {"0": "关闭", "1": "开启"},
    "cl_auto_cursor_scale": {"0": "关闭", "1": "开启"},
    "cl_player_ping_mute": {"0": "关闭", "1": "开启"},
    "cl_playerspray_auto_apply": {"0": "关闭", "1": "开启"},
    "cl_mute_enemy_team": {"0": "关闭", "1": "开启"},
    "cl_thirdperson": {"0": "关闭", "1": "开启"},
    "closecaption": {"0": "关闭", "1": "开启"},
    "cc_subtitles": {"0": "关闭", "1": "开启"},
    "adsp_debug": {"0": "关闭", "1": "开启"},
    "battery_saver": {"0": "关闭", "1": "开启"},
    "sk_autoaim_mode": {"0": "关闭", "1": "开启"},
    "cam_snapto": {"0": "关闭", "1": "开启"},
    "cam_collision": {"0": "关闭", "1": "开启"},
    "sv_specnoclip": {"0": "关闭", "1": "开启"},
    "sv_log_onefile": {"0": "关闭", "1": "开启"},
    "sv_logbans": {"0": "关闭", "1": "开启"},
    "sv_logecho": {"0": "关闭", "1": "开启"},
    "sv_logfile": {"0": "关闭", "1": "开启"},
    "sv_logflush": {"0": "关闭", "1": "开启"},
    "sv_pause_on_console_open": {"0": "关闭", "1": "开启"},
    "viewmodel_presetpos": {
        "0": "自定义", "1": "桌面", "2": "经典", "3": "专业",
    },
    "speaker_config": {
        "-1": "默认", "0": "立体声", "1": "耳机",
        "2": "2.1", "3": "4.1", "4": "5.1", "5": "7.1",
    },
    "cl_color": {
        "0": "黄", "1": "紫", "2": "绿", "3": "蓝", "4": "橙",
    },
    "cl_hud_color": {
        "0": "默认", "1": "白", "2": "浅蓝", "3": "绿",
        "4": "黄", "5": "橙", "6": "粉", "7": "紫",
        "8": "红", "9": "蓝", "10": "青", "11": "自定义",
    },
}


# ==========================================================
# 翻译函数
# ==========================================================

def translate_video_key_local(key: str) -> Optional[str]:
    if not key:
        return None
    v = VIDEO_NAME_CN.get(key)
    if v is not None:
        return v
    if key.startswith("setting."):
        v = VIDEO_NAME_CN.get(key[8:])
        if v is not None:
            return v
    return VIDEO_NAME_CN.get("setting." + key)


def translate_video_value_local(key: str, value) -> Optional[str]:
    if key is None or value is None:
        return None
    sv = str(value)
    dic = VIDEO_VALUE_CN.get(key)
    if dic is None and key.startswith("setting."):
        dic = VIDEO_VALUE_CN.get(key[8:])
    if dic is None:
        dic = VIDEO_VALUE_CN.get("setting." + key)
    if dic is not None:
        hit = dic.get(sv)
        if hit is not None:
            return hit
    low = sv.lower()
    if low == "true":
        return "开启"
    if low == "false":
        return "关闭"
    return None


_SPLIT_RE = re.compile(r"[;\s]+")


def translate_cmd_local(cmd: str) -> Optional[str]:
    if not cmd:
        return None
    hit = _lookup(CMD_NAME_CN, cmd)
    if hit:
        return hit
    parts = [p for p in _SPLIT_RE.split(cmd.strip()) if p]
    if len(parts) <= 1:
        return None
    translated = []
    for p in parts:
        cn = _lookup(CMD_NAME_CN, p) or translate_video_key_local(p)
        if not cn:
            return None
        translated.append(cn)
    return " + ".join(translated)


def clean_video_key_for_translation(key: str) -> str:
    k = key or ""
    if k.startswith("setting."):
        k = k[8:]
    return k.replace(".", " ").replace("_", " ").strip()


# ==========================================================
# autoexec.cfg 解析
# ==========================================================

def tokenize_cfg_line(line: str) -> list[str]:
    tokens = []
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c in " \t":
            i += 1
        elif c == '"':
            i += 1
            chars = []
            while i < n and line[i] != '"':
                if line[i] == "\\" and i + 1 < n:
                    chars.append(line[i + 1])
                    i += 2
                else:
                    chars.append(line[i])
                    i += 1
            if i < n:
                i += 1
            tokens.append("".join(chars))
        elif c == "/" and i + 1 < n and line[i + 1] == "/":
            break
        elif c == ";":
            break
        else:
            start = i
            while i < n and line[i] not in " \t":
                if line[i] == "/" and i + 1 < n and line[i + 1] == "/":
                    break
                if line[i] == ";":
                    break
                i += 1
            tokens.append(line[start:i])
    return tokens


_SKIP_CMDS = {"echo", "exec", "clear", "host_writeconfig",
              "unbind", "unbindall", "alias"}


def parse_autoexec_cfg(text: str) -> dict:
    binds: list[tuple[str, str]] = []
    settings: list[tuple[str, str]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//"):
            continue
        tokens = tokenize_cfg_line(line)
        if not tokens:
            continue
        cmd = tokens[0]
        cmd_lower = cmd.lower()
        args = tokens[1:]

        if cmd_lower == "bind":
            if len(args) >= 2:
                binds.append((args[0], " ".join(args[1:])))
            continue
        if cmd_lower in _SKIP_CMDS:
            continue
        if args:
            value = " ".join(args) if len(args) > 1 else args[0]
            settings.append((cmd, value))

    return {"binds": binds, "settings": settings}


def dedupe_settings(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    last_val = {}
    for name, value in items:
        last_val[name] = value
    seen = set()
    out = []
    for name, _ in items:
        if name in seen:
            continue
        seen.add(name)
        out.append((name, last_val[name]))
    return out


# ==========================================================
# 文本读取 / VDF 解析
# ==========================================================

_ENCODINGS = ("utf-8-sig", "utf-8", "utf-16", "utf-16-le",
              "utf-16-be", "gbk", "gb18030", "latin-1")


def read_text_with_fallback(path: Path) -> str:
    last_err = None
    for enc in _ENCODINGS:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError as e:
            last_err = e
            continue
        except PermissionError as e:
            raise IOError(f"没有权限读取 {path.name}：{e}")
        except FileNotFoundError:
            raise IOError(f"文件不存在：{path}")
        except OSError as e:
            raise IOError(f"读取失败 {path.name}：{e}")
    try:
        with open(path, "rb") as f:
            data = f.read()
        return data.decode("utf-8", errors="replace")
    except Exception as e:
        raise IOError(
            f"所有编码均失败 {path.name}（最后错误：{last_err}）：{e}")


class VDFParser:
    __slots__ = ("text", "pos", "length")

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.length = len(text)

    def parse(self) -> dict:
        result = {}
        while self.pos < self.length:
            self.skip_ws()
            if self.pos >= self.length:
                break
            if self.peek() == '"':
                key = self.read_string()
                self.skip_ws()
                result[key] = self._read_value()
            else:
                self.pos += 1
        return result

    def parse_block(self) -> dict:
        self.expect("{")
        result = {}
        while True:
            self.skip_ws()
            if self.pos >= self.length:
                break
            if self.peek() == "}":
                self.pos += 1
                break
            if self.peek() == '"':
                key = self.read_string()
                self.skip_ws()
                result[key] = self._read_value()
            else:
                self.pos += 1
        return result

    def _read_value(self):
        c = self.peek()
        if c == "{":
            return self.parse_block()
        if c == '"':
            return self.read_string()
        return self.read_token()

    def skip_ws(self):
        text = self.text
        n = self.length
        while self.pos < n:
            c = text[self.pos]
            if c in " \t\r\n":
                self.pos += 1
            elif c == "/" and self.pos + 1 < n and text[self.pos + 1] == "/":
                nl = text.find("\n", self.pos)
                self.pos = n if nl == -1 else nl
            else:
                break

    def peek(self) -> str:
        return self.text[self.pos] if self.pos < self.length else ""

    def expect(self, ch: str):
        if self.pos < self.length and self.text[self.pos] == ch:
            self.pos += 1
        else:
            raise ValueError(f"Expected '{ch}' at {self.pos}")

    def read_string(self) -> str:
        self.expect('"')
        text = self.text
        n = self.length
        chars = []
        append = chars.append
        while self.pos < n:
            c = text[self.pos]
            if c == "\\":
                self.pos += 1
                if self.pos < n:
                    append(text[self.pos])
                    self.pos += 1
            elif c == '"':
                self.pos += 1
                break
            else:
                append(c)
                self.pos += 1
        return "".join(chars)

    def read_token(self) -> str:
        start = self.pos
        text = self.text
        n = self.length
        while self.pos < n and text[self.pos] not in ' \t\r\n{}"':
            self.pos += 1
        return text[start:self.pos]


def find_section(data, name: str):
    if isinstance(data, dict):
        v = data.get(name)
        if isinstance(v, dict):
            return v
        for v in data.values():
            if isinstance(v, dict):
                res = find_section(v, name)
                if res is not None:
                    return res
    return None


def collect_leaves(data, out: dict, prefix: str = ""):
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict):
                collect_leaves(v, out, prefix + k + ".")
            else:
                out[prefix + k] = v
    else:
        out[prefix] = data


def find_file_fuzzy(directory: Path,
                    keywords: list[str],
                    exts: list[str]) -> Optional[Path]:
    if not directory or not directory.is_dir():
        return None
    try:
        files = [f for f in directory.iterdir() if f.is_file()]
    except (PermissionError, OSError):
        return None

    kw_lower = [k.lower() for k in keywords]
    ext_lower = [e.lower() for e in exts]

    best = None
    best_rank = (len(ext_lower), 1 << 30)
    for f in files:
        name_lower = f.name.lower()
        ext_rank = -1
        for i, ext in enumerate(ext_lower):
            if name_lower.endswith(ext):
                ext_rank = i
                break
        if ext_rank < 0:
            continue
        if not all(kw in name_lower for kw in kw_lower):
            continue
        rank = (ext_rank, len(f.name))
        if rank < best_rank:
            best_rank = rank
            best = f
    return best


# ==========================================================
# Steam 定位
# ==========================================================

def find_steam_path() -> Optional[Path]:
    if sys.platform.startswith("win"):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Valve\Steam")
            val, _ = winreg.QueryValueEx(key, "SteamPath")
            if val and Path(val).is_dir():
                return Path(val)
        except Exception:
            pass
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\WOW6432Node\Valve\Steam")
            val, _ = winreg.QueryValueEx(key, "InstallPath")
            if val and Path(val).is_dir():
                return Path(val)
        except Exception:
            pass
        for p in (r"C:\Program Files (x86)\Steam", r"C:\Program Files\Steam"):
            if Path(p).is_dir():
                return Path(p)
    elif sys.platform.startswith("linux"):
        for p in (Path.home() / ".steam" / "steam",
                  Path.home() / ".local" / "share" / "Steam"):
            if p.is_dir():
                return p
    elif sys.platform == "darwin":
        p = Path.home() / "Library" / "Application Support" / "Steam"
        if p.is_dir():
            return p
    return None


def steamid64_to_account_id(steamid64: str) -> str:
    try:
        return str(int(steamid64) - 76561197960265728)
    except Exception:
        return ""


def scan_steam_users(steam_path: Path) -> list[dict]:
    users: list[dict] = []
    userdata = steam_path / "userdata"
    if not userdata.is_dir():
        return users

    try:
        dirs = sorted(userdata.iterdir(), key=lambda p: p.name)
    except (PermissionError, OSError):
        return users

    for d in dirs:
        if not d.is_dir():
            continue
        game_dir = d / "730"
        if not game_dir.is_dir():
            continue
        cfg_dir = None
        for sub in (game_dir / "local" / "cfg", game_dir / "cfg"):
            if sub.is_dir():
                cfg_dir = sub
                break
        if cfg_dir is None:
            continue
        users.append({
            "account_id": d.name,
            "user_dir": d,
            "cfg_dir": cfg_dir,
            "display": d.name,
        })

    loginusers = steam_path / "config" / "loginusers.vdf"
    if loginusers.is_file():
        try:
            text = read_text_with_fallback(loginusers)
            data = VDFParser(text).parse()
            users_data = find_section(data, "users")
            if isinstance(users_data, dict):
                for steamid64, info in users_data.items():
                    if not isinstance(info, dict):
                        continue
                    account_id = steamid64_to_account_id(steamid64)
                    persona = info.get("PersonaName", "")
                    account = info.get("AccountName", "")
                    for u in users:
                        if u["account_id"] == account_id and (persona or account):
                            u["display"] = f"{persona} ({account}) [{account_id}]"
        except Exception:
            pass
    return users


# ==========================================================
# 配置加载
# ==========================================================

_FILE_SPECS = {
    "machine_convars": (["machine_convars"], [".vcfg", ".txt"]),
    "user_convars":    (["user_convars"],    [".vcfg", ".txt"]),
    "user_keys":       (["user_keys"],       [".vcfg", ".txt"]),
    "video":           (["video"],           [".txt", ".vcfg"]),
}


def load_cs2_configs(cfg_dir: Path) -> dict:
    result = {
        "convar_items": [],
        "key_items": [],
        "video_items": [],
        "raw_texts": {},
        "found_paths": {},
        "errors": [],
        "cfg_dir": str(cfg_dir),
    }

    if not cfg_dir.is_dir():
        result["errors"].append(f"配置目录不存在：{cfg_dir}")
        return result

    for name, (keywords, exts) in _FILE_SPECS.items():
        path = find_file_fuzzy(cfg_dir, keywords, exts)
        if path is None:
            if name != "video":
                result["errors"].append(
                    f"没找到 *{keywords[0]}* 文件（试过 {exts}）")
            continue
        result["found_paths"][name] = str(path)

        try:
            text = read_text_with_fallback(path)
            result["raw_texts"][name] = text
            data = VDFParser(text).parse()

            if name in ("machine_convars", "user_convars"):
                section = None
                for sec in ("convars", "ConVars", "convars_localized"):
                    section = find_section(data, sec)
                    if section:
                        break
                if section is None:
                    tmp: dict = {}
                    collect_leaves(data, tmp)
                    section = {k: v for k, v in tmp.items()
                               if not k.lower().endswith("name")
                               and not k.lower().endswith("version")}
                source = "机器配置" if name == "machine_convars" else "用户配置"
                append = result["convar_items"].append
                for k, v in section.items():
                    if not isinstance(v, dict):
                        append((source, k, v))

            elif name == "user_keys":
                section = None
                for sec in ("bindings", "Bindings", "Keys", "keys"):
                    section = find_section(data, sec)
                    if section:
                        break
                append = result["key_items"].append
                if section:
                    for k, v in section.items():
                        if not isinstance(v, dict):
                            append(("按键", k, v))
                analog = None
                for sec in ("analogbindings", "AnalogBindings"):
                    analog = find_section(data, sec)
                    if analog:
                        break
                if analog:
                    for k, v in analog.items():
                        if not isinstance(v, dict):
                            append(("模拟绑定", k, v))

            elif name == "video":
                inner = data
                for v in data.values():
                    if isinstance(v, dict):
                        inner = v
                        break
                tmp: dict = {}
                collect_leaves(inner, tmp)
                append = result["video_items"].append
                for k, v in tmp.items():
                    if k.lower().endswith("name"):
                        continue
                    if not isinstance(v, dict):
                        append((k, v))

        except IOError as e:
            result["errors"].append(str(e))
        except Exception as e:
            result["errors"].append(f"解析 {path.name} 时出错：{e}")

    return result


# ==========================================================
# 联网翻译
# ==========================================================

class OnlineTranslator:
    API = "https://api.mymemory.translated.net/get"

    def __init__(self):
        self.cache: dict[str, str] = {}
        self.lock = threading.Lock()

    def translate(self, text: str, cancel_event: threading.Event) -> Optional[str]:
        if not text or cancel_event.is_set():
            return None
        with self.lock:
            cached = self.cache.get(text)
        if cached is not None:
            return cached

        query = text.strip().lstrip("+-").strip()
        if not query:
            return None

        try:
            params = urllib.parse.urlencode({"q": query, "langpair": "en|zh-CN"})
            req = urllib.request.Request(
                f"{self.API}?{params}",
                headers={"User-Agent": "CS2CfgViewer/3.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if cancel_event.is_set():
                return None
            result = data.get("responseData", {}).get("translatedText")
            if result and not str(result).startswith("MYMEMORY WARNING"):
                with self.lock:
                    self.cache[text] = result
                return result
        except Exception:
            pass
        return None


# ==========================================================
# 后端 API
# ==========================================================

class Api:
    """所有 public 方法自动暴露给前端 window.pywebview.api.*"""

    def __init__(self):
        self._window: Optional[webview.Window] = None
        self._source: Optional[dict] = None
        self._autoexec_path: Optional[Path] = None
        self._users: list[dict] = []
        self._steam_path: Optional[Path] = None

        self._translator = OnlineTranslator()
        self._cancel = threading.Event()
        self._online_thread: Optional[threading.Thread] = None

    def bind_window(self, w):
        self._window = w

    def _push(self, event: str, data):
        if self._window:
            try:
                payload = json.dumps(data, ensure_ascii=False)
                self._window.evaluate_js(
                    f"window.__push({json.dumps(event)}, {payload})")
            except Exception:
                pass

    # ---------- 基础 ----------

    def get_app_info(self):
        return {
            "name": APP_NAME,
            "version": APP_VERSION,
            "author": APP_AUTHOR,
            "github": GITHUB_URL,
            "telegram": TELEGRAM_URL,
            "placeholder": STEAM_PLACEHOLDER,
        }

    def open_url(self, url: str):
        webbrowser.open(url)
        return {"ok": True}

    # ---------- Steam / 账户 ----------

    def locate_steam(self):
        p = find_steam_path()
        if p:
            self._steam_path = p
            return {"ok": True, "path": str(p)}
        return {"ok": False, "path": None, "reason": "没找到 Steam 目录"}

    def set_steam_path(self, path: str):
        p = Path(path.strip())
        if not p.is_dir():
            return {"ok": False, "reason": f"路径不可用：{path}"}
        if p.name.lower() == "userdata":
            p = p.parent
        self._steam_path = p
        return self._scan()

    def rescan(self):
        return self._scan()

    def _scan(self):
        if not self._steam_path:
            return {"ok": False, "steam_path": None,
                    "options": [], "user_count": 0,
                    "reason": "没找到 Steam 目录"}
        self._users = scan_steam_users(self._steam_path)
        options = [
            {"kind": "vcfg", "value": str(i), "label": u["display"]}
            for i, u in enumerate(self._users)
        ]
        if self._autoexec_path is not None:
            options.append({
                "kind": "autoexec",
                "value": "autoexec",
                "label": f"autoexec ({self._autoexec_path.name})",
            })
        return {
            "ok": True,
            "steam_path": str(self._steam_path),
            "user_count": len(self._users),
            "options": options,
        }

    # ---------- autoexec 虚拟账户 ----------

    def pick_autoexec(self):
        if not self._window:
            return {"ok": False, "reason": "窗口未就绪"}
        result = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=False,
            file_types=("CFG 文件 (*.cfg;*.txt)", "所有文件 (*.*)"),
        )
        if not result:
            return {"ok": False, "reason": "未选择文件"}
        path = Path(result[0])
        self._autoexec_path = path
        return {"ok": True, "path": str(path), "name": path.name}

    # ---------- 加载数据源 ----------

    def load_source(self, value: str):
        if value == "autoexec":
            if self._autoexec_path is None:
                return {"ok": False, "reason": "还没有导入 autoexec"}
            return self._load_autoexec(self._autoexec_path)

        try:
            idx = int(value)
        except (TypeError, ValueError):
            return {"ok": False, "reason": f"无效的账户值：{value}"}

        if idx < 0 or idx >= len(self._users):
            return {"ok": False, "reason": "账户索引超出范围"}

        user = self._users[idx]
        return self._load_vcfg(Path(user["cfg_dir"]),
                               source_desc=f"账户 {user['account_id']}")

    def _load_vcfg(self, cfg_dir: Path, source_desc: str = ""):
        result = load_cs2_configs(cfg_dir)
        self._source = {
            "type": "vcfg",
            "convar": [list(x) for x in result["convar_items"]],
            "key": [list(x) for x in result["key_items"]],
            "video": [list(x) for x in result["video_items"]],
            "raw_texts": dict(result["raw_texts"]),
            "found_paths": dict(result["found_paths"]),
            "errors": list(result["errors"]),
            "cfg_dir": result["cfg_dir"],
            "source_desc": source_desc,
        }
        return self._build_view()

    def _load_autoexec(self, path: Path):
        try:
            text = read_text_with_fallback(path)
        except IOError as e:
            return {"ok": False, "reason": str(e)}

        parsed = parse_autoexec_cfg(text)
        binds = parsed["binds"]
        settings = dedupe_settings(parsed["settings"])

        self._source = {
            "type": "autoexec",
            "key": [["按键", k, v] for k, v in binds],
            "video": [[k, v] for k, v in settings],
            "raw_text": text,
            "filename": path.name,
            "path": str(path),
            "binds_count": len(binds),
            "settings_count": len(settings),
        }
        return self._build_view()

    # ---------- 视图构建 ----------

    def _build_view(self):
        if self._source is None:
            return {
                "ok": True, "convar": [], "keys": [], "video": [],
                "raw": [], "summary": "还没有载入任何配置",
                "source_type": None, "diagnosis": "还没有载入任何配置",
            }

        src = self._source
        if src["type"] == "vcfg":
            convar = [list(x) for x in src["convar"]]
            keys = [self._mk_key(*x) for x in src["key"]]
            video = [self._mk_video(*x) for x in src["video"]]
            raw = [{"name": n, "text": t}
                   for n, t in src["raw_texts"].items()]
            head = f"vcfg {len(src['found_paths'])} 个文件"
        else:
            convar = []
            keys = [self._mk_key(*x) for x in src["key"]]
            video = [self._mk_video(*x) for x in src["video"]]
            raw = [{"name": f"autoexec ({src['filename']})",
                    "text": src["raw_text"]}]
            head = (f"autoexec {src['binds_count']} 按键、"
                    f"{src['settings_count']} 项设置")

        miss_k = sum(1 for it in keys
                     if not it["key_cn"] or not it["value_cn"])
        miss_v = sum(1 for it in video if not it["key_cn"])
        summary = (f"完成 · {head} · {len(convar)} 配置 · "
                   f"{len(keys)} 按键（{miss_k} 未收录）· "
                   f"{len(video)} 设置（{miss_v} 未收录）")

        return {
            "ok": True, "convar": convar, "keys": keys,
            "video": video, "raw": raw, "summary": summary,
            "source_type": src["type"],
            "diagnosis": self._build_diagnosis(),
        }

    @staticmethod
    def _mk_key(source, key, value):
        key_cn = translate_key_local(key) or ""
        value_cn = translate_cmd_local(value) or ""
        trans = "本地" if (key_cn and value_cn) else ""
        return {"source": source, "key": key, "key_cn": key_cn,
                "value": value, "value_cn": value_cn, "trans": trans}

    @staticmethod
    def _mk_video(key, value):
        key_cn = translate_video_key_local(key) or ""
        value_cn = translate_video_value_local(key, value) or ""
        trans = "本地" if key_cn else ""
        return {"key": key, "key_cn": key_cn, "value": str(value),
                "value_cn": value_cn, "trans": trans}

    def _build_diagnosis(self):
        src = self._source
        if not src:
            return "还没有载入任何配置"
        lines = [f"{APP_NAME} v{APP_VERSION}", ""]
        if src["type"] == "vcfg":
            lines.append("vcfg 数据源")
            lines.append(f"  配置目录：{src['cfg_dir']}")
            if src.get("source_desc"):
                lines.append(f"  来源：{src['source_desc']}")
            lines.append("  文件：")
            if src["found_paths"]:
                for n, p in src["found_paths"].items():
                    lines.append(f"    [{n}] {p}")
            else:
                lines.append("    （没有找到文件）")
            if src["errors"]:
                lines.append("  提示：")
                for e in src["errors"]:
                    lines.append(f"    - {e}")
        else:
            lines.append("autoexec 数据源")
            lines.append(f"  文件：{src['path']}")
            lines.append(f"  按键绑定：{src['binds_count']} 条")
            lines.append(f"  设置项：{src['settings_count']} 条（已去重）")
        return "\n".join(lines)

    def get_diagnosis(self):
        return self._build_diagnosis()

    # ---------- 联网翻译 ----------

    def start_online(self):
        if self._source is None:
            return {"ok": False, "reason": "还没有载入任何配置", "total": 0}
        if self._online_thread and self._online_thread.is_alive():
            return {"ok": False, "reason": "已经在运行", "total": 0}

        src = self._source
        pending = []
        for i, (_, k, v) in enumerate(src["key"]):
            if not translate_key_local(k):
                pending.append(("key", i, "key_cn", k))
            if not translate_cmd_local(v):
                pending.append(("key", i, "value_cn", v))
        for i, (k, v) in enumerate(src["video"]):
            if not translate_video_key_local(k):
                pending.append(("video", i, "key_cn",
                                clean_video_key_for_translation(k)))

        if not pending:
            return {"ok": True, "total": 0, "summary": "本地全都收录了"}

        self._cancel.clear()
        total = len(pending)
        self._push("online_start", {"total": total})

        def worker():
            done = 0
            for kind, idx, field, text in pending:
                if self._cancel.is_set():
                    self._push("online_cancel", {})
                    return
                result = self._translator.translate(text, self._cancel)
                if self._cancel.is_set():
                    self._push("online_cancel", {})
                    return
                if result:
                    if kind == "key":
                        item = src["key"][idx]
                        if field == "key_cn":
                            item[2] = result
                        else:
                            item[3] = result
                    else:
                        src["video"][idx][2] = result
                    self._push("online_item",
                               {"kind": kind, "idx": idx,
                                "field": field, "value": result})
                done += 1
                if done % 5 == 0 or done == total:
                    self._push("online_progress",
                               {"done": done, "total": total})
            self._push("online_done", {"total": total})

        self._online_thread = threading.Thread(target=worker, daemon=True)
        self._online_thread.start()
        return {"ok": True, "total": total}

    def stop_online(self):
        self._cancel.set()
        return {"ok": True}


# ==========================================================
# 窗口尺寸与居中（按工作区计算）
# ==========================================================

def _get_work_area() -> tuple[int, int, int, int]:
    """
    获取主屏幕工作区域（排除任务栏）：x, y, width, height。
    失败时回退到整个屏幕。
    """
    if sys.platform.startswith("win"):
        try:
            import ctypes
            from ctypes import wintypes

            SPI_GETWORKAREA = 0x0030
            rect = wintypes.RECT()
            ok = ctypes.windll.user32.SystemParametersInfoW(
                SPI_GETWORKAREA, 0, ctypes.byref(rect), 0)
            if ok and rect.right > rect.left and rect.bottom > rect.top:
                return (rect.left, rect.top,
                        rect.right - rect.left,
                        rect.bottom - rect.top)
        except Exception:
            pass

    # 回退：用整个屏幕尺寸
    if sys.platform.startswith("win"):
        try:
            import ctypes
            user32 = ctypes.windll.user32
            sw = user32.GetSystemMetrics(0)
            sh = user32.GetSystemMetrics(1)
            return (0, 0, sw, sh)
        except Exception:
            pass
    return (0, 0, 1920, 1080)


def _compute_window_geometry():
    """
    按工作区比例算窗口大小与位置：
    - 宽 = 工作区 * 0.78
    - 高 = 工作区 * 0.82
    - 上限 1180×780，下限 720×480
    """
    wx, wy, ww, wh = _get_work_area()

    target_w = int(ww * 0.78)
    target_h = int(wh * 0.82)

    target_w = max(720, min(target_w, 1180))
    target_h = max(480, min(target_h, 780))

    # 不超过工作区
    target_w = min(target_w, max(600, ww - 20))
    target_h = min(target_h, max(400, wh - 20))

    min_w = min(680, target_w)
    min_h = min(440, target_h)

    # 在工作区内居中，略上偏 15px
    x = wx + (ww - target_w) // 2
    y = wy + (wh - target_h) // 2 - 15

    # 兜底
    x = max(wx, min(x, wx + ww - target_w))
    y = max(wy, min(y, wy + wh - target_h))

    return target_w, target_h, min_w, min_h, x, y


# ==========================================================
# 入口
# ==========================================================

def main():
    api = Api()
    web_dir = Path(__file__).parent / "web"
    index = web_dir / "index.html"
    if not index.is_file():
        raise SystemExit(f"找不到前端文件：{index}")

    w, h, mw, mh, x, y = _compute_window_geometry()

    window = webview.create_window(
        title=f"{APP_NAME} v{APP_VERSION}",
        url=str(index),
        js_api=api,
        width=w,
        height=h,
        x=x,
        y=y,
        min_size=(mw, mh),
        background_color="#f5f5f7",
    )
    api.bind_window(window)
    webview.start(debug=False)


if __name__ == "__main__":
    main()
