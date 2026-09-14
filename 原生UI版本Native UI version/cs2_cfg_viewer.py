# cs2_cfg_viewer.py
# 默认离线，字典优先，未命中才走机翻（需用户主动开启）
# 兼容 .vcfg / .txt / autoexec.cfg
# autoexec 作为独立账户显示，与 vcfg 数据源互斥
# 环境：Python 3.10+ / Tkinter（自带）

from __future__ import annotations

import json
import re
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import Optional


# ==========================================================
# 应用元信息
# ==========================================================

APP_NAME    = "CS2 CFG 配置查看器"
APP_VERSION = "2.1.0"
APP_AUTHOR  = "D1r3ctor"

GITHUB_TEXT   = "Github"
GITHUB_URL    = "https://github.com/d1irgger/CS2-CFG-view"
TELEGRAM_TEXT = "Telegram"
TELEGRAM_URL  = "https://t.me/timharrys"

STEAM_PLACEHOLDER = "选择 Steam 目录，或用 ProSettings 下载解析 autoexec"


# ==========================================================
# UI 辅助函数
# ==========================================================

def make_clickable(parent, text: str, url: str, **pack_kwargs) -> tk.Label:
    """蓝色下划线可点击跳转标签。"""
    label = tk.Label(parent, text=text, fg="#0066CC",
                     cursor="hand2", font=("", 11, "underline"))
    label.pack(**pack_kwargs)
    label.bind("<Button-1>", lambda e: webbrowser.open(url))
    return label


def center_window(win: tk.Toplevel, min_w: int = 0, min_h: int = 0):
    """把 Toplevel 居中到屏幕，附带最小尺寸。"""
    win.update_idletasks()
    w = max(win.winfo_reqwidth(), min_w)
    h = max(win.winfo_reqheight(), min_h)
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 2)
    win.geometry(f"{w}x{h}+{x}+{y}")


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


def _normalize_setting_key(key: str) -> str:
    if key and key.startswith("setting."):
        return key[8:]
    return key or ""


# ==========================================================
# 按键名字典
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
# 命令字典
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
# 设置项字典
# ==========================================================

VIDEO_NAME_CN = {
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
    "setting.r_csgo_portrait_mode": "竖屏模式",
    "setting.r_csgo_fullscreen_gamma": "全屏伽马",
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
    "setting.mat_antialias": "抗锯齿模式",
    "setting.mat_aaquality": "抗锯齿质量",
    "setting.r_csgo_shadows_quality": "阴影质量",
    "setting.r_csgo_water_effects": "水面效果",
    "setting.r_csgo_water_reflections": "水面反射",
    "setting.r_csgo_particle_quality": "粒子质量",
    "setting.r_csgo_character_quality": "角色质量",
    "setting.r_csgo_boost_player_contrast": "增强玩家对比度",
    "setting.r_csgo_ui_contrast": "UI 对比度",
    "setting.r_csgo_motion_blur": "动态模糊",
    "setting.r_csgo_screen_space_ambient_occlusion": "屏幕空间环境光遮蔽",
    "setting.r_csgo_texture_filtering_mode": "纹理过滤模式",
    "setting.r_csgo_texture_filtering_anisotropic": "各向异性过滤",
    "setting.optional_user_active_weapon_bloom": "武器动态模糊",
    "setting.cl_predict": "客户端预测",
    "setting.frame_rate_max": "最大帧率",
    "setting.num_workers": "工作线程数",
    "setting.multicore": "多核渲染",
    "setting.mat_shader_cache": "着色器缓存",
    "setting.r_drawparticles": "绘制粒子",
    "setting.r_eyegloss": "眼睛高光",
    "setting.snd_mute_losefocus": "失焦时静音",
    "setting.snd_steam_surround_enabled": "Steam 环绕声",
    "setting.volume": "音量",
    "setting.snd_music_volume": "音乐音量",
    "setting.snd_menumusic_volume": "菜单音乐音量",
    "setting.player_skin": "玩家模型皮肤",
    "setting.cl_teamid_overhead_always": "始终显示队友标识",
    "setting.cl_teamid_overhead_mode": "队友标识模式",
    "setting.hud_scaling": "HUD 缩放",
    "setting.cl_hud_scaling": "HUD 缩放",
    "setting.cl_hud_scale": "HUD 缩放",
    "setting.hud_health_ammo_number": "显示弹药数字",
    "setting.cl_radar_rotate": "雷达旋转",
    "setting.cl_radar_always_centered": "雷达始终居中",
    "setting.cl_radar_scale": "雷达缩放",
    "setting.cl_hud_radar_scale": "HUD 雷达缩放",
    "setting.enable_debug_name": "启用调试名称",

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
    "m_mouseaccel1": "鼠标加速 1",
    "m_mouseaccel2": "鼠标加速 2",
    "m_mousespeed": "鼠标速度",
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
    "cl_use_opens_buy_menu": "使用键打开购买菜单",
    "cl_autowepswitch": "自动切换拾取武器",
    "cl_showloadout": "显示装备栏",
    "cl_teamid_overhead_always": "始终显示队友标识",
    "cl_teamid_overhead_mode": "队友标识模式",
    "cl_teammate_colors_show": "队友颜色",
    "cl_hud_color": "HUD 颜色",
    "cl_hud_radar_scale": "HUD 雷达缩放",
    "cl_radar_scale": "雷达缩放",
    "cl_radar_always_centered": "雷达始终居中",
    "cl_radar_rotate": "雷达旋转",
    "cl_radar_icon_scale_min": "雷达图标最小缩放",
    "cl_radar_square_with_scoreboard": "比分板时雷达方形",
    "cl_radar_square_always": "雷达始终方形",
    "cl_radar_square_when_spectating": "观察时雷达方形",
    "cl_radar_scale_dynamic": "动态雷达缩放",
    "cl_radar_show_all_players_when_spectating": "观察时显示所有玩家",
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
    "cl_crosshair_dynamic_maxdist_splitratio": "动态准星分裂比",
    "cl_crosshair_dynamic_splitalpha_innermod": "动态准星内透明度",
    "cl_crosshair_dynamic_splitalpha_outermod": "动态准星外透明度",
    "cl_crosshair_dynamic_splitdist": "动态准星分裂距离",
    "cl_crosshair_recoil": "准星跟随后坐力",
    "cl_crosshair_sniper_width": "狙击准星线宽",
    "cl_crosshair_sniper_show_normal_inaccuracy": "狙击显示正常不准度",
    "cl_crosshair_t": "T 形准星",
    "cl_crosshairgap_useweaponvalue": "准星间距使用武器值",
    "cl_crosshairusealpha": "准星使用透明度",
    "cl_crosshair_friendly_warning": "准星友方警告",
    "cl_fixedcrosshairgap": "固定准星间距",
    "cl_ironsight_dot_scale": "机瞄点缩放",
    "cl_ironsight_usecrosshaircolor": "机瞄使用准星颜色",
    "cl_debounce_zoom": "开镜防抖",
    "cl_sniper_auto_rezoom": "狙击自动重新开镜",
    "cl_sniper_delay_unscope": "狙击延迟收镜",
    "cl_sniper_show_inaccuracy": "显示狙击不准度",
    "cl_quickinventory_filename": "快速库存文件名",
    "cl_quickinventory_lastinv": "快速库存使用上次武器",
    "cl_quickinventory_line_update_speed": "快速库存行更新速度",
    "cl_inventory_radial_immediate_select": "库存转盘立即选择",
    "cl_inventory_radial_tap_to_cycle": "库存转盘点击循环",
    "cl_inventory_saved_filter2": "库存保存过滤",
    "cl_inventory_saved_sort2": "库存保存排序",
    "cl_buywheel_donate_key": "购买轮盘捐赠键",
    "cl_buywheel_nomousecentering": "购买轮盘禁用鼠标居中",
    "cl_buywheel_nonumberpurchasing": "购买轮盘禁用数字购买",
    "cl_chatfilters": "聊天过滤",
    "cl_clanid": "战队 ID",
    "cl_color": "颜色",
    "cl_disable_round_end_report": "禁用回合结束报告",
    "cl_dm_buyrandomweapons": "死斗随机购买武器",
    "cl_hide_avatar_images": "隐藏头像图像",
    "cl_invites_only_friends": "仅好友邀请",
    "cl_invites_only_mainmenu": "仅主菜单邀请",
    "cl_itemimages_dynamically_generated": "物品图像动态生成",
    "cl_join_advertise": "加入广播",
    "cl_mouselook": "鼠标控制视角",
    "cl_mute_all_but_friends_and_party": "仅队友和好友语音",
    "cl_mute_enemy_team": "屏蔽敌方语音",
    "cl_obs_interp_enable": "启用观战插值",
    "cl_observed_bot_crosshair": "观察机器人准星",
    "cl_parachute_autodeploy": "降落伞自动展开",
    "cl_ping_fade_deadzone": "标记淡出死区",
    "cl_ping_fade_distance": "标记淡出距离",
    "cl_player_ping_mute": "玩家标记静音",
    "cl_playerspray_auto_apply": "喷漆自动应用",
    "cl_radial_radio_tap_to_ping": "无线电轮盘点击标记",
    "cl_radial_radio_version_reset": "无线电轮盘版本重置",
    "cl_radialmenu_deadzone_size_joystick": "转盘死区大小（摇杆）",
    "cl_sanitize_player_names": "过滤玩家名称",
    "cl_scoreboard_mouse_enable_binding": "比分板启用鼠标绑定",
    "cl_scoreboard_survivors_always_on": "比分板始终显示存活者",
    "cl_show_clan_in_death_notice": "死亡提示显示战队",
    "cl_show_observer_crosshair": "显示观战准星",
    "cl_thirdperson": "第三人称",
    "cl_timeout": "网络超时",
    "cl_versus_intro": "对战开场动画",
    "cl_autohelp": "自动帮助提示",
    "cl_allow_animated_avatars": "允许动态头像",
    "cl_auto_cursor_scale": "自动缩放光标",
    "cl_cursor_scale": "光标缩放",
    "cl_predict": "客户端预测",
    "cl_predictweapons": "客户端预测武器",
    "cl_lagcompensation": "延迟补偿",
    "cl_interp": "插值时间",
    "cl_interp_ratio": "插值比率",
    "cl_net_buffer_ticks": "网络缓冲 tick",
    "cl_enable_party_voice": "启用组队语音",
    "cl_ent_pivot_size": "实体轴点大小",
    "cl_ent_text_flags_active": "实体文本标志激活",
    "cl_force_spec_hud_color_to_team$1": "强制观战 HUD 颜色为队伍",
    "cl_graphics_driver_warning_dont_show_again$2": "不再显示驱动警告",
    "cl_import_csgo_config": "导入 CSGO 配置",
    "cl_latch_report": "latch 报告",
    "cl_low_latency_vsync_recommendation_dont_show_again": "不再显示低延迟 vsync 建议",
    "cl_predict_body_shot_fx": "预测身体命中特效",
    "cl_predict_head_shot_fx": "预测头部命中特效",
    "cl_predict_kill_ragdolls": "预测击杀布娃娃",
    "cl_promoted_settings_acknowledged": "推荐设置已确认",
    "cl_ragdoll_limit": "布娃娃数量上限",
    "cl_redemption_reset_timestamp": "重置时间戳",
    "cl_refresh_rate_recommendation_dont_show_again": "不再显示刷新率建议",
    "cl_vrr_recommendation_dont_show_again": "不再显示 VRR 建议",
    "cl_weapon_selection_rarity_color": "武器选择稀有度着色",
    "cl_teamcounter_playercount_instead_of_avatars": "队伍显示玩家数",
    "cl_show_equipped_character_for_player_avatars": "显示头像装备角色",
    "cl_radial_radio_tab_0_text_1": "无线电轮盘 0 页文本 1",
    "cl_radial_radio_tab_0_text_2": "无线电轮盘 0 页文本 2",
    "cl_radial_radio_tab_0_text_3": "无线电轮盘 0 页文本 3",
    "cl_radial_radio_tab_0_text_4": "无线电轮盘 0 页文本 4",
    "cl_radial_radio_tab_0_text_5": "无线电轮盘 0 页文本 5",
    "cl_radial_radio_tab_0_text_6": "无线电轮盘 0 页文本 6",
    "cl_radial_radio_tab_0_text_7": "无线电轮盘 0 页文本 7",
    "cl_radial_radio_tab_0_text_8": "无线电轮盘 0 页文本 8",
    "cl_radial_radio_tab_1_text_1": "无线电轮盘 1 页文本 1",
    "cl_radial_radio_tab_1_text_2": "无线电轮盘 1 页文本 2",
    "cl_radial_radio_tab_1_text_3": "无线电轮盘 1 页文本 3",
    "cl_radial_radio_tab_1_text_4": "无线电轮盘 1 页文本 4",
    "cl_radial_radio_tab_1_text_5": "无线电轮盘 1 页文本 5",
    "cl_radial_radio_tab_1_text_6": "无线电轮盘 1 页文本 6",
    "cl_radial_radio_tab_1_text_7": "无线电轮盘 1 页文本 7",
    "cl_radial_radio_tab_1_text_8": "无线电轮盘 1 页文本 8",
    "cl_radial_radio_tab_2_text_1": "无线电轮盘 2 页文本 1",
    "cl_radial_radio_tab_2_text_2": "无线电轮盘 2 页文本 2",
    "cl_radial_radio_tab_2_text_3": "无线电轮盘 2 页文本 3",
    "cl_radial_radio_tab_2_text_4": "无线电轮盘 2 页文本 4",
    "cl_radial_radio_tab_2_text_5": "无线电轮盘 2 页文本 5",
    "cl_radial_radio_tab_2_text_6": "无线电轮盘 2 页文本 6",
    "cl_radial_radio_tab_2_text_7": "无线电轮盘 2 页文本 7",
    "cl_radial_radio_tab_2_text_8": "无线电轮盘 2 页文本 8",
    "cl_embedded_stream_audio_volume": "内嵌直播音量",
    "cl_embedded_stream_audio_volume_xmaster": "内嵌直播走主音量",
    "cl_hud_telemetry_frametime_poor": "帧时间差阈值",
    "cl_hud_telemetry_frametime_show": "显示帧时间",
    "cl_hud_telemetry_net_detailed": "详细网络遥测",
    "cl_hud_telemetry_net_misdelivery_poor": "网络错误投递阈值",
    "cl_hud_telemetry_net_misdelivery_show": "显示网络错误投递",
    "cl_hud_telemetry_net_quality_graph_show": "显示网络质量图",
    "cl_hud_telemetry_ping_poor": "Ping 差阈值",
    "cl_hud_telemetry_ping_show": "显示 Ping",
    "cl_hud_telemetry_serverrecvmargin_graph_show": "显示服务器接收裕度图",
    "cl_hud_radar_background_alpha": "雷达背景透明度",
    "cl_hud_radar_blur_background": "雷达背景模糊",
    "cl_hud_radar_map_additive": "雷达地图叠加",
    "cl_teamid_overhead_fade_near_crosshair": "队友标识在准星附近淡出",
    "cl_teamid_overhead_colors_show": "显示队友标识颜色",
    "cl_joystick_enabled": "启用摇杆",
    "cl_deathcampanel_position_dynamic": "死亡镜头面板位置动态",

    "volume": "音量",
    "snd_mute_losefocus": "失焦时静音",
    "snd_musicvolume": "音乐音量",
    "snd_menumusic_volume": "菜单音乐音量",
    "snd_gamevolume": "游戏音量",
    "snd_voipvolume": "语音音量",
    "snd_headphone_eq": "耳机均衡器",
    "snd_spatialize_lerp": "空间化插值",
    "snd_steamaudio_enable_perspective_correction": "Steam Audio 透视校正",
    "snd_steamaudio_source_pathing_debug": "Steam Audio 源路径调试",
    "snd_autodetect_latency": "自动检测延迟",
    "snd_mixahead": "音频预混时间",
    "snd_gain": "音频增益",
    "snd_deathcamera_volume": "死亡镜头音量",
    "snd_mapobjective_volume": "地图目标音效音量",
    "snd_menumap_volume": "菜单地图音量",
    "snd_mvp_volume": "MVP 音量",
    "snd_roundaction_volume": "回合动作音量",
    "snd_roundend_volume": "回合结束音量",
    "snd_roundstart_volume": "回合开始音量",
    "snd_tensecondwarning_volume": "十秒警告音量",
    "snd_duckerattacktime": "闪避攻击时间",
    "snd_duckerreleasetime": "闪避释放时间",
    "snd_duckerthreshold": "闪避阈值",
    "snd_ducktovolume": "闪避到音量",
    "snd_surf_volume_inair": "滑翔空中音量",
    "snd_surf_volume_map": "滑翔地图音量",
    "snd_surf_volume_slide": "滑翔滑行音量",
    "snd_toolvolume": "工具音量",
    "snd_mute_mvp_music_live_players": "屏蔽 MVP 音乐（真人玩家）",
    "snd_deathcamera_volume$4": "死亡镜头音量",
    "snd_mapobjective_volume$4": "地图目标音效音量",
    "snd_menumap_volume$4": "菜单地图音量",
    "snd_menumusic_volume$4": "菜单音乐音量",
    "snd_musicvolume$2": "音乐音量",
    "snd_mvp_volume$4": "MVP 音量",
    "snd_roundaction_volume$4": "回合动作音量",
    "snd_roundend_volume$4": "回合结束音量",
    "snd_roundstart_volume$4": "回合开始音量",
    "snd_tensecondwarning_volume$4": "十秒警告音量",
    "speaker_config": "扬声器配置",
    "dsp_volume": "DSP 音量",

    "voice_scale": "语音音量",
    "voice_threshold": "语音激活阈值",
    "voice_modenable": "启用语音",
    "voice_always_sample_mic": "始终采样麦克风",
    "voice_vox": "语音激活模式",
    "voice_always_sample_mic$2": "始终采样麦克风",
    "voice_threshold$2": "语音激活阈值",

    "rate": "网络速率",
    "net_allow_multicast": "允许组播",
    "net_maxroutable": "最大可路由大小",
    "sv_voiceenable": "启用服务器语音",
    "sv_skyname": "天空盒名称",
    "sv_log_onefile": "日志单一文件",
    "sv_logbans": "记录封禁",
    "sv_logecho": "日志回显",
    "sv_logfile": "记录日志",
    "sv_logflush": "日志立即写入",
    "sv_logsdir": "日志目录",
    "sv_noclipaccelerate": "穿墙加速度",
    "sv_noclipspeed": "穿墙速度",
    "sv_noclipspeedscaleonshift": "Shift 时穿墙速度倍率",
    "sv_pause_on_console_open": "打开控制台暂停",
    "sv_specaccelerate": "观察加速度",
    "sv_specnoclip": "观察穿墙",
    "sv_specspeed": "观察速度",
    "sv_specspeed$2": "观察速度",
    "sv_unlockedchapters": "解锁章节",
    "sv_unpause_on_console_close": "关闭控制台恢复",
    "sv_usercmd_execute_warning_ms": "用户命令执行警告毫秒",
    "tv_nochat": "屏蔽观战聊天",
    "mm_csgo_community_search_players_min": "社区搜索最少玩家数",
    "mm_dedicated_search_maxping": "专用服务器最大 Ping",
    "mm_server_search_lan_ports": "局域网服务器搜索端口",

    "hud_scaling": "HUD 缩放",
    "hud_showtargetid": "显示目标 ID",
    "hud_fastswitch": "快速切换武器",
    "hud_scaling$3": "HUD 缩放",

    "fov_desired": "视野 FOV",
    "fps_max": "最大帧率",
    "fps_max_ui": "UI 最大帧率",
    "fps_max_ui$2": "UI 最大帧率",
    "fps_max_tools": "工具最大帧率",

    "name": "玩家名称",
    "password": "服务器密码",
    "con_enable": "启用控制台",
    "con_allownotify": "允许控制台通知",
    "crosshair": "启用准星",
    "closecaption": "关闭字幕",
    "cc_subtitles": "隐藏式字幕",
    "cc_linger_time": "字幕停留时间",
    "cc_delay_time": "字幕延迟",
    "cc_lang": "字幕语言",
    "option_duck_method": "蹲下方式",
    "option_speed_method": "慢走方式",
    "player_nevershow_communityservermessage": "不显示社区服务器消息",
    "player_teamplayedlast": "上次游玩阵营",
    "player_botdifflast_s": "上次机器人难度",
    "player_survival_list_10_0_303": "生存模式地图列表",
    "player_competitive_maplist_8_10_0_A062AC6A": "竞技地图列表",
    "player_competitive_maplist_8_10_0_C9C8D674": "竞技地图列表",
    "player_competitive_maplist_2v2_10_0_E8C782EC": "2v2 竞技地图列表",
    "player_wargames_list2_10_0_E04": "战争游戏列表",
    "mouse_inverty": "鼠标 Y 轴反转",
    "key_bind_version": "按键绑定版本",
    "trusted_launch": "受信任启动",
    "trusted_launch_once": "单次受信任启动",
    "splitscreen_mode": "分屏模式",
    "violence_ablood": "血液效果",
    "violence_agibs": "碎尸效果",
    "violence_hblood": "人类血液效果",
    "violence_hgibs": "人类碎尸效果",
    "r_drawtracers_firstperson": "第一人称曳光弹",
    "r_fullscreen_gamma": "全屏伽马",
    "r_icon_image_cache_to_disk": "图标图像缓存到磁盘",
    "r_player_visibility_mode": "玩家可见性模式",
    "r_show_build_info": "显示构建信息",
    "r_spectator_flashbang_opacity": "观战闪光弹不透明度",
    "spec_centerchasecam": "居中追踪镜头",
    "spec_replay_autostart": "回放自动开始",
    "spec_show_xray": "显示 X 光",
    "spec_usenumberkeys_nobinds": "使用数字键切换玩家",
    "sk_autoaim_mode": "自动瞄准模式",
    "safezonex": "安全区域 X",
    "safezoney": "安全区域 Y",
    "mapoverview_icon_scale": "地图概览图标缩放",
    "engine_no_focus_sleep": "失焦引擎休眠",
    "func_break_max_pieces": "破碎最大碎块数",
    "imgui_default_font_size": "ImGui 默认字体大小",
    "joy_advanced": "摇杆高级设置",
    "joy_advaxisr": "摇杆高级轴 R",
    "joy_advaxisu": "摇杆高级轴 U",
    "joy_advaxisv": "摇杆高级轴 V",
    "joy_advaxisx": "摇杆高级轴 X",
    "joy_advaxisy": "摇杆高级轴 Y",
    "joy_advaxisz": "摇杆高级轴 Z",
    "joy_axisbutton_threshold": "摇杆轴按钮阈值",
    "joy_display_input": "显示摇杆输入",
    "joy_movement_stick": "摇杆移动模式",
    "joy_name": "摇杆名称",
    "joy_pitchsensitivity": "摇杆俯仰灵敏度",
    "joy_response_look": "摇杆视角响应曲线",
    "joy_response_move": "摇杆移动响应曲线",
    "joy_sidesensitivity": "摇杆侧向灵敏度",
    "joy_wingmanwarrior_centerhack": "僚机战士中心 hack",
    "joy_wingmanwarrior_turnhack": "僚机战士转向 hack",
    "joy_yawsensitivity": "摇杆偏航灵敏度",
    "joystick": "启用摇杆",
    "lockMoveControllerRet": "锁定移动控制器返回",
    "input_filter_relative_analog_inputs": "过滤相对模拟输入",
    "player0_using_joystick": "玩家 0 使用摇杆",
    "panorama_console_position_and_size": "控制台位置和大小",
    "panorama_debug_overlay_opacity": "调试叠加不透明度",
    "panorama_debugger_theme": "调试器主题",
    "panorama_focus_world_panels": "聚焦世界面板",
    "panorama_joystick_enabled": "摇杆启用",
    "panorama_toggledebugger_mode": "切换调试器模式",
    "demo_flush": "demo 刷新",
    "demo_index": "demo 索引",
    "demo_index_max_other": "demo 索引最大其他",
    "demo_mouse_enable_binding": "demo 鼠标启用绑定",
    "enable_boneflex": "启用骨骼柔化",
    "mat_enable_uber_shaders": "启用 Uber 着色器",
    "gameinstructor_enable": "启用游戏教练",
    "steaminput_firsttimepopup": "Steam Input 首次弹窗",
    "steaminput_glyph_display_mode": "Steam Input 图标显示模式",
    "steaminput_glyph_neutral": "Steam Input 图标中性",
    "steaminput_glyph_solid": "Steam Input 图标实心",
    "steaminput_glyph_style": "Steam Input 图标样式",
    "tr_best_course_time": "训练最佳时间",
    "tr_completed_training": "完成训练",
    "weapon_accuracy_logging": "武器精度日志",
    "lobby_default_privacy_bits2": "大厅默认隐私",
    "adsp_debug": "音频 DSP 调试",
    "battery_saver": "省电模式",

    "cam_collision": "摄像机碰撞",
    "cam_idealdelta": "摄像机理想延迟",
    "cam_idealdist": "摄像机理想距离",
    "cam_ideallag": "摄像机理想滞后",
    "cam_idealpitch": "摄像机理想俯仰",
    "cam_idealyaw": "摄像机理想偏航",
    "cam_snapto": "摄像机瞬移",
    "c_maxdistance": "第三人称最大距离",
    "c_maxpitch": "第三人称最大俯仰",
    "c_maxyaw": "第三人称最大偏航",
    "c_mindistance": "第三人称最小距离",
    "c_minpitch": "第三人称最小俯仰",
    "c_minyaw": "第三人称最小偏航",
    "c_orthoheight": "正交高度",
    "c_orthowidth": "正交宽度",
    "c_thirdpersonshoulder": "第三人称越肩视角",
    "c_thirdpersonshoulderaimdist": "越肩瞄准距离",
    "c_thirdpersonshoulderdist": "越肩距离",
    "c_thirdpersonshoulderheight": "越肩高度",
    "c_thirdpersonshoulderoffset": "越肩偏移",
    "cl_obs_interp_speed": "观战插值速度",

    "cachedvalue_count_partybrowser": "组队浏览器缓存计数",
    "cachedvalue_count_teammates": "队友缓存计数",

    "ui_deepstats_radio_heat_figurine": "深度统计电台热度",
    "ui_deepstats_radio_heat_tab": "深度统计电台标签",
    "ui_deepstats_radio_heat_team": "深度统计电台队伍",
    "ui_deepstats_toplevel_mode": "深度统计顶层模式",
    "ui_inventorysettings_recently_acknowledged": "库存设置已确认",
    "ui_mainmenu_bkgnd_movie_CC4ECB9": "主菜单背景影片",
    "ui_mainmenu_bkgnd_movie_C2AEBB5E$13": "主菜单背景影片",
    "ui_nearbylobbies_filter3": "附近大厅过滤",
    "ui_news_last_read_link": "新闻最后阅读链接",
    "ui_playsettings_custom_preset": "自定义游戏预设",
    "ui_playsettings_directchallengekey": "直接挑战键",
    "ui_playsettings_flags_listen_casual": "监听-休闲标志",
    "ui_playsettings_flags_listen_competitive": "监听-竞技标志",
    "ui_playsettings_flags_listen_cooperative": "监听-合作标志",
    "ui_playsettings_flags_listen_deathmatch": "监听-死斗标志",
    "ui_playsettings_flags_listen_scrimcomp2v2": "监听-2v2 竞技标志",
    "ui_playsettings_flags_listen_skirmish": "监听-遭遇战标志",
    "ui_playsettings_flags_listen_survival": "监听-生存标志",
    "ui_playsettings_flags_official_casual": "官方-休闲标志",
    "ui_playsettings_flags_official_competitive": "官方-竞技标志",
    "ui_playsettings_flags_official_cooperative": "官方-合作标志",
    "ui_playsettings_flags_official_deathmatch": "官方-死斗标志",
    "ui_playsettings_flags_official_scrimcomp2v2": "官方-2v2 竞技标志",
    "ui_playsettings_flags_official_skirmish": "官方-遭遇战标志",
    "ui_playsettings_flags_official_survival": "官方-生存标志",
    "ui_playsettings_maps_listen_casual": "监听-休闲地图",
    "ui_playsettings_maps_listen_competitive": "监听-竞技地图",
    "ui_playsettings_maps_listen_deathmatch": "监听-死斗地图",
    "ui_playsettings_maps_listen_scrimcomp2v2": "监听-2v2 竞技地图",
    "ui_playsettings_maps_listen_skirmish": "监听-遭遇战地图",
    "ui_playsettings_maps_official_casual": "官方-休闲地图",
    "ui_playsettings_maps_official_deathmatch": "官方-死斗地图",
    "ui_playsettings_maps_workshop": "创意工坊地图",
    "ui_playsettings_mode_listen": "监听模式",
    "ui_playsettings_mode_official_v20": "官方模式 v20",
    "ui_playsettings_prime": "Prime 优先",
    "ui_playsettings_survival_solo": "生存模式单人",
    "ui_playsettings_warmup_map_name": "热身地图名",
    "ui_popup_weaponupdate_version": "武器更新弹窗版本",
    "ui_setting_advertiseforhire_auto": "自动发布求职",
    "ui_setting_advertiseforhire_auto_last": "上次自动发布求职",
    "ui_show_subscription_alert": "显示订阅提示",
    "ui_show_unlock_competitive_alert": "显示解锁竞技提示",
    "ui_steam_overlay_notification_position": "Steam 覆盖通知位置",
    "ui_steam_overlay_notification_position_horz": "覆盖通知水平位置",
    "ui_steam_overlay_notification_position_vert": "覆盖通知垂直位置",
    "ui_vanitysetting_loadoutslot_ct": "CT 装备槽",
    "ui_vanitysetting_loadoutslot_t": "T 装备槽",
    "ui_vanitysetting_team": "偏好阵营",
    "ui_inspect_bkgnd_map_C2AEBB5E": "检视背景地图",

    "aim_flickstick_circular_deadzone_max": "甩枪圆形死区最大值",
    "aim_flickstick_circular_deadzone_min": "甩枪圆形死区最小值",
    "aim_flickstick_crank_sensitivity": "甩枪曲柄灵敏度",
    "aim_flickstick_crank_tightness": "甩枪曲柄紧密度",
    "aim_flickstick_enabled": "启用甩枪",
    "aim_flickstick_flick_snap_mode": "甩枪瞬移模式",
    "aim_flickstick_flick_tightness": "甩枪瞬移紧密度",
    "aim_flickstick_forward_deadzone": "甩枪向前死区",
    "aim_flickstick_release_dampen_speed": "甩枪释放阻尼速度",
    "aim_gyro_acceleration": "陀螺仪加速度",
    "aim_gyro_base_sensitivity": "陀螺仪基础灵敏度",
    "aim_gyro_circular_deadzone": "陀螺仪圆形死区",
    "aim_gyro_conversion_mode": "陀螺仪转换模式",
    "aim_gyro_enable_mode": "陀螺仪启用模式",
    "aim_gyro_high_sense_multiplier": "陀螺仪高灵敏度倍率",
    "aim_gyro_high_sense_speed": "陀螺仪高灵敏度速度",
    "aim_gyro_invert_pitch": "陀螺仪垂直反转",
    "aim_gyro_invert_yaw": "陀螺仪水平反转",
    "aim_gyro_low_sense_speed": "陀螺仪低灵敏度速度",
    "aim_gyro_pitchyaw_ratio": "陀螺仪俯仰/偏航比",
    "aim_gyro_precision_speed": "陀螺仪精确速度",
    "aim_gyro_raw": "陀螺仪原始模式",
    "aim_gyro_ray_angle": "陀螺仪射线角度",
    "aim_gyro_siapi_convert_pixels_to_angles": "陀螺仪 Steam Input 像素转角度",
    "aim_gyro_siapi_sensitivity_setting": "陀螺仪 Steam Input 灵敏度",
    "aim_gyro_siapi_vertical_scale_setting": "陀螺仪 Steam Input 垂直缩放",
    "aim_gyro_square_deadzone_pitch": "陀螺仪方形死区俯仰",
    "aim_gyro_square_deadzone_yaw": "陀螺仪方形死区偏航",
    "aim_gyro_zoom_dampening_level1": "陀螺仪开镜阻尼等级 1",
    "aim_gyro_zoom_dampening_level2": "陀螺仪开镜阻尼等级 2",
    "aim_stick_circular_deadzone_max": "摇杆圆形死区最大值",
    "aim_stick_circular_deadzone_min": "摇杆圆形死区最小值",
    "aim_stick_extra_turning_delay": "摇杆额外转向延迟",
    "aim_stick_extra_turning_ramp_up_time": "摇杆额外转向加速时间",
    "aim_stick_extra_yaw": "摇杆额外偏航",
    "aim_stick_invert_pitch": "摇杆垂直反转",
    "aim_stick_invert_yaw": "摇杆水平反转",
    "aim_stick_rate_pitch": "摇杆俯仰速率",
    "aim_stick_rate_yaw": "摇杆偏航速率",
    "aim_stick_response_curve": "摇杆响应曲线",
    "aim_stick_square_deadzone_pitch": "摇杆方形死区俯仰",
    "aim_stick_square_deadzone_yaw": "摇杆方形死区偏航",
    "aim_stick_zoom_dampening_level1": "摇杆开镜阻尼等级 1",
    "aim_stick_zoom_dampening_level2": "摇杆开镜阻尼等级 2",
    "aim_touchpad_circular_deadzone_min": "触摸板圆形死区最小值",
    "aim_touchpad_invert_pitch": "触摸板垂直反转",
    "aim_touchpad_invert_yaw": "触摸板水平反转",
    "aim_touchpad_sensitivity_pitch": "触摸板俯仰灵敏度",
    "aim_touchpad_sensitivity_yaw": "触摸板偏航灵敏度",
    "aim_touchpad_square_deadzone_pitch": "触摸板方形死区俯仰",
    "aim_touchpad_square_deadzone_yaw": "触摸板方形死区偏航",
    "aim_touchpad_zoom_dampening_level1": "触摸板开镜阻尼等级 1",
    "aim_touchpad_zoom_dampening_level2": "触摸板开镜阻尼等级 2",
    "move_stick_aggression_strength": "摇杆激进强度",
    "move_stick_aggressive": "摇杆激进模式",
    "move_stick_circular_deadzone_max": "摇杆移动圆形死区最大值",
    "move_stick_circular_deadzone_min": "摇杆移动圆形死区最小值",
    "move_stick_response_curve": "摇杆移动响应曲线",
    "move_stick_square_deadzone_forward": "摇杆移动方形死区前进",
    "move_stick_square_deadzone_strafe": "摇杆移动方形死区横移",
    "move_stick_walk_zone": "摇杆行走区域",
    "move_touchpad_circular_deadzone_min": "触摸板移动圆形死区最小值",
    "move_touchpad_sensitivity_forward": "触摸板移动前进灵敏度",
    "move_touchpad_sensitivity_strafe": "触摸板移动横移灵敏度",
    "move_touchpad_square_deadzone_forward": "触摸板移动方形死区前进",
    "move_touchpad_square_deadzone_strafe": "触摸板移动方形死区横移",
}


# ==========================================================
# 设置项值字典
# ==========================================================

VIDEO_VALUE_CN = {
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
    "setting.r_csgo_screen_space_ambient_occlusion": {"0": "关闭", "1": "开启"},
    "setting.r_csgo_texture_filtering_mode": {
        "0": "双线性", "1": "三线性",
        "2": "各向异性 2x", "3": "各向异性 4x",
        "4": "各向异性 8x", "5": "各向异性 16x",
    },
    "setting.optional_user_active_weapon_bloom": {"0": "关闭", "1": "开启"},
    "setting.multicore": {"0": "关闭", "1": "开启"},
    "setting.snd_mute_losefocus": {"0": "关闭", "1": "开启"},
    "setting.snd_steam_surround_enabled": {"0": "关闭", "1": "开启"},
    "setting.cl_teamid_overhead_always": {"0": "关闭", "1": "开启"},
    "setting.cl_radar_rotate": {"0": "关闭", "1": "开启"},
    "setting.cl_radar_always_centered": {"0": "关闭", "1": "开启"},
    "setting.hud_health_ammo_number": {"0": "关闭", "1": "开启"},
    "setting.enable_debug_name": {"0": "关闭", "1": "开启"},
    "setting.mat_monitorgamma_tv_enabled": {"0": "关闭", "1": "开启"},
    "setting.cl_predict": {"0": "关闭", "1": "开启"},
    "setting.mat_shader_cache": {"0": "关闭", "1": "开启"},

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
    "cl_hud_radar_blur_background": {"0": "关闭", "1": "开启"},
    "cl_hud_radar_map_additive": {"0": "关闭", "1": "开启"},
    "cl_quickinventory_lastinv": {"0": "关闭", "1": "开启"},
    "cl_inventory_radial_immediate_select": {"0": "关闭", "1": "开启"},
    "cl_inventory_radial_tap_to_cycle": {"0": "关闭", "1": "开启"},
    "cl_radial_radio_tap_to_ping": {"0": "关闭", "1": "开启"},
    "cl_teammate_colors_show": {"0": "关闭", "1": "开启"},
    "cl_teamid_overhead_colors_show": {"0": "关闭", "1": "开启"},
    "cl_show_equipped_character_for_player_avatars": {"0": "关闭", "1": "开启"},
    "cl_sanitize_player_names": {"0": "关闭", "1": "开启"},
    "cl_show_clan_in_death_notice": {"0": "关闭", "1": "开启"},
    "cl_teamcounter_playercount_instead_of_avatars": {"0": "关闭", "1": "开启"},
    "cl_scoreboard_survivors_always_on": {"0": "关闭", "1": "开启"},
    "cl_predict": {"0": "关闭", "1": "开启"},
    "cl_predictweapons": {"0": "关闭", "1": "开启"},
    "cl_lagcompensation": {"0": "关闭", "1": "开启"},
    "snd_mute_losefocus": {"0": "关闭", "1": "开启"},
    "snd_mute_mvp_music_live_players": {"0": "关闭", "1": "开启"},
    "voice_modenable": {"0": "关闭", "1": "开启"},
    "voice_always_sample_mic": {"0": "关闭", "1": "开启"},
    "voice_always_sample_mic$2": {"0": "关闭", "1": "开启"},
    "voice_vox": {"0": "按键说话", "1": "语音激活"},
    "violence_ablood": {"0": "关闭", "1": "开启"},
    "violence_agibs": {"0": "关闭", "1": "开启"},
    "violence_hblood": {"0": "关闭", "1": "开启"},
    "violence_hgibs": {"0": "关闭", "1": "开启"},
    "player_nevershow_communityservermessage": {"0": "关闭", "1": "开启"},
    "option_duck_method": {"0": "按住", "1": "切换"},
    "option_speed_method": {"0": "按住", "1": "切换"},
    "mouse_inverty": {"0": "关闭", "1": "开启"},
    "joystick": {"0": "关闭", "1": "开启"},
    "joy_advanced": {"0": "关闭", "1": "开启"},
    "cl_joystick_enabled": {"0": "关闭", "1": "开启"},
    "snd_autodetect_latency": {"0": "关闭", "1": "开启"},
    "cl_debounce_zoom": {"0": "关闭", "1": "开启"},
    "cl_sniper_auto_rezoom": {"0": "关闭", "1": "开启"},
    "cl_sniper_show_inaccuracy": {"0": "关闭", "1": "开启"},
    "cl_sniper_delay_unscope": {"0": "关闭", "1": "开启"},
    "cl_ironsight_usecrosshaircolor": {"0": "关闭", "1": "开启"},
    "r_drawtracers_firstperson": {"0": "关闭", "1": "开启"},
    "r_icon_image_cache_to_disk": {"0": "关闭", "1": "开启"},
    "r_show_build_info": {"0": "关闭", "1": "开启"},
    "spec_centerchasecam": {"0": "关闭", "1": "开启"},
    "spec_replay_autostart": {"0": "关闭", "1": "开启"},
    "spec_usenumberkeys_nobinds": {"0": "关闭", "1": "开启"},
    "splitscreen_mode": {"0": "关闭", "1": "开启"},
    "ui_show_subscription_alert": {"0": "关闭", "1": "开启"},
    "ui_show_unlock_competitive_alert": {"0": "关闭", "1": "开启"},
    "snd_steamaudio_enable_perspective_correction": {"0": "关闭", "1": "开启"},
    "snd_steamaudio_source_pathing_debug": {"0": "关闭", "1": "开启"},
    "enable_boneflex": {"0": "关闭", "1": "开启"},
    "mat_enable_uber_shaders": {"0": "关闭", "1": "开启"},
    "gameinstructor_enable": {"0": "关闭", "1": "开启"},
    "panorama_joystick_enabled": {"0": "关闭", "1": "开启"},
    "input_filter_relative_analog_inputs": {"0": "关闭", "1": "开启"},
    "player0_using_joystick": {"0": "关闭", "1": "开启"},
    "ui_deepstats_radio_heat_figurine": {"0": "关闭", "1": "开启"},
    "ui_deepstats_radio_heat_tab": {"0": "关闭", "1": "开启"},
    "ui_deepstats_radio_heat_team": {"0": "关闭", "1": "开启"},
    "ui_deepstats_toplevel_mode": {"0": "关闭", "1": "开启"},
    "cl_auto_cursor_scale": {"0": "关闭", "1": "开启"},
    "cl_enable_party_voice": {"0": "关闭", "1": "开启"},
    "cl_force_spec_hud_color_to_team$1": {"0": "关闭", "1": "开启"},
    "cl_graphics_driver_warning_dont_show_again$2": {"0": "关闭", "1": "开启"},
    "cl_import_csgo_config": {"0": "关闭", "1": "开启"},
    "cl_interpolate_report": {"0": "关闭", "1": "开启"},
    "cl_latch_report": {"0": "关闭", "1": "开启"},
    "cl_low_latency_vsync_recommendation_dont_show_again": {"0": "关闭", "1": "开启"},
    "cl_obs_interp_enable": {"0": "关闭", "1": "开启"},
    "cl_predict_body_shot_fx": {"0": "关闭", "1": "开启"},
    "cl_predict_head_shot_fx": {"0": "关闭", "1": "开启"},
    "cl_predict_kill_ragdolls": {"0": "关闭", "1": "开启"},
    "cl_refresh_rate_recommendation_dont_show_again": {"0": "关闭", "1": "开启"},
    "cl_vrr_recommendation_dont_show_again": {"0": "关闭", "1": "开启"},
    "cl_parachute_autodeploy": {"0": "关闭", "1": "开启"},
    "cl_mouselook": {"0": "关闭", "1": "开启"},
    "cl_playerspray_auto_apply": {"0": "关闭", "1": "开启"},
    "cl_player_ping_mute": {"0": "关闭", "1": "开启"},
    "cl_invites_only_friends": {"0": "关闭", "1": "开启"},
    "cl_invites_only_mainmenu": {"0": "关闭", "1": "开启"},
    "cl_mute_enemy_team": {"0": "关闭", "1": "开启"},
    "cl_dm_buyrandomweapons": {"0": "关闭", "1": "开启"},
    "cl_hide_avatar_images": {"0": "关闭", "1": "开启"},
    "cl_thirdperson": {"0": "关闭", "1": "开启"},
    "cl_radar_show_all_players_when_spectating": {"0": "关闭", "1": "开启"},
    "closecaption": {"0": "关闭", "1": "开启"},
    "cc_subtitles": {"0": "关闭", "1": "开启"},
    "demo_flush": {"0": "关闭", "1": "开启"},
    "adsp_debug": {"0": "关闭", "1": "开启"},
    "battery_saver": {"0": "关闭", "1": "开启"},
    "trusted_launch": {"0": "关闭", "1": "开启"},
    "trusted_launch_once": {"0": "关闭", "1": "开启"},
    "sk_autoaim_mode": {"0": "关闭", "1": "开启"},
    "c_thirdpersonshoulder": {"false": "关闭", "true": "开启",
                              "0": "关闭", "1": "开启"},
    "cam_snapto": {"0": "关闭", "1": "开启"},
    "cam_collision": {"0": "关闭", "1": "开启"},
    "sv_specnoclip": {"0": "关闭", "1": "开启"},
    "sv_log_onefile": {"0": "关闭", "1": "开启"},
    "sv_logbans": {"0": "关闭", "1": "开启"},
    "sv_logecho": {"0": "关闭", "1": "开启"},
    "sv_logfile": {"0": "关闭", "1": "开启"},
    "sv_logflush": {"0": "关闭", "1": "开启"},
    "sv_pause_on_console_open": {"0": "关闭", "1": "开启"},
    "sv_voiceenable": {"0": "关闭", "1": "开启",
                       "false": "关闭", "true": "开启"},
    "tv_nochat": {"0": "关闭", "1": "开启"},
    "demo_index": {"0": "关闭", "1": "开启"},
    "r_player_visibility_mode": {"0": "默认", "1": "增强"},
    "net_allow_multicast": {"0": "关闭", "1": "开启"},
    "lockMoveControllerRet": {"0": "关闭", "1": "开启"},
    "viewmodel_presetpos": {
        "0": "自定义", "1": "桌面", "2": "经典", "3": "专业",
    },
    "speaker_config": {
        "-1": "默认", "0": "立体声", "1": "耳机",
        "2": "2.1", "3": "4.1", "4": "5.1", "5": "7.1",
    },
    "ui_steam_overlay_notification_position": {
        "bottomright": "右下", "bottomleft": "左下",
        "topright": "右上", "topleft": "左上",
    },
    "player_botdifflast_s": {
        "0": "简单", "1": "普通", "2": "困难", "3": "专家",
    },
    "ui_playsettings_mode_official_v20": {
        "casual": "休闲", "competitive": "竞技",
        "deathmatch": "死斗", "scrimcomp2v2": "2v2 竞技",
        "cooperative": "合作", "skirmish": "遭遇战",
    },
    "ui_playsettings_mode_listen": {
        "casual": "休闲", "competitive": "竞技",
        "deathmatch": "死斗", "scrimcomp2v2": "2v2 竞技",
    },
    "ui_nearbylobbies_filter3": {
        "competitive": "竞技", "casual": "休闲",
        "deathmatch": "死斗", "survival": "生存",
        "scrimcomp2v2": "2v2 竞技",
    },
    "ui_playsettings_prime": {"0": "关闭", "1": "开启"},
    "joy_response_look": {
        "0": "线性", "1": "指数", "2": "平方", "3": "自定义",
    },
    "joy_response_move": {
        "0": "线性", "1": "指数", "2": "平方", "3": "自定义",
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
                headers={"User-Agent": "CS2CfgViewer/2.1"},
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
# 文本读取
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


# ==========================================================
# VDF 解析器
# ==========================================================

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


# ==========================================================
# 文件名模糊匹配
# ==========================================================

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
# 配置加载（vcfg）
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
# GUI
# ==========================================================

class CS2CfgViewerApp(tk.Tk):
    SEARCH_DEBOUNCE_MS = 150

    def __init__(self):
        super().__init__()
        self.title(APP_NAME)

        self.steam_path: Optional[Path] = None
        self.users: list[dict] = []
        self.convar_items: list[tuple] = []
        self.key_items: list[dict] = []
        self.video_items: list[dict] = []
        self.raw_texts: dict[str, str] = {}
        self.last_diagnosis: str = ""

        # 单一数据源（vcfg 或 autoexec，两者互斥）
        self._source_raw: Optional[dict] = None
        # 已导入的 autoexec 文件路径（作为虚拟账户选项）
        self._autoexec_path: Optional[Path] = None

        self._steam_placeholder_active = False

        self.translator = OnlineTranslator()
        self._online_thread: Optional[threading.Thread] = None
        self._cancel_event = threading.Event()
        self._search_after_id: Optional[str] = None

        self.steam_path_var = tk.StringVar()
        self.user_var = tk.StringVar()
        self.search_var = tk.StringVar()
        self.status_var = tk.StringVar(value="准备就绪")
        self.mode_var = tk.StringVar(value="离线")
        self.online_var = tk.BooleanVar(value=False)

        self._setup_window_size()
        self._setup_styles()
        self._build_ui()
        self._auto_locate()

    # ---------- 窗口尺寸自适应 ----------
    def _setup_window_size(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        usable_w = sw - 40
        usable_h = sh - 100

        target_w = min(1360, max(800, int(usable_w * 0.85)))
        target_h = min(860,  max(500, int(usable_h * 0.85)))
        target_w = min(target_w, usable_w)
        target_h = min(target_h, usable_h)

        min_w = min(860, target_w)
        min_h = min(520, target_h)

        x = max(0, (sw - target_w) // 2)
        y = max(0, (sh - target_h) // 2 - 20)

        self.geometry(f"{target_w}x{target_h}+{x}+{y}")
        self.minsize(min_w, min_h)

    # ---------- 全局样式 ----------
    def _setup_styles(self):
        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=(18, 1))
        style.map("TNotebook.Tab",
                  padding=[("selected", (19, 2))])

    # ---------- UI ----------
    def _build_ui(self):
        PAD = 12
        GAP = 6

        status_bar = ttk.Frame(self, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        ttk.Label(status_bar, textvariable=self.status_var,
                  anchor=tk.W, padding=(PAD, 4)).pack(
            side=tk.LEFT, fill=tk.X, expand=True)

        info = ttk.Label(
            status_bar,
            text=f"v{APP_VERSION}    Made by {APP_AUTHOR}",
            anchor=tk.E, padding=(PAD, 4),
            foreground="#666666",
            cursor="hand2")
        info.pack(side=tk.RIGHT)
        info.bind("<Button-1>", lambda e: self._show_about())

        root = ttk.Frame(self, padding=(PAD, PAD, PAD, PAD))
        root.pack(fill=tk.BOTH, expand=True)

        form = ttk.Frame(root)
        form.pack(fill=tk.X)
        form.columnconfigure(1, weight=1)

        # 行 0：Steam 位置
        ttk.Label(form, text="Steam 位置:",
                  anchor=tk.E, width=12).grid(
            row=0, column=0, sticky=tk.EW, padx=(0, GAP), pady=(0, GAP))

        self.steam_entry = ttk.Entry(form, textvariable=self.steam_path_var)
        self.steam_entry.grid(row=0, column=1, sticky=tk.EW, pady=(0, GAP))
        self.steam_entry.bind("<FocusIn>", self._on_steam_focus_in)
        self.steam_entry.bind("<FocusOut>", self._on_steam_focus_out)
        self.steam_entry.bind("<Key>", self._on_steam_key)

        self.steam_path_var.set(STEAM_PLACEHOLDER)
        self._steam_placeholder_active = True
        try:
            self.steam_entry.configure(foreground="#999999")
        except Exception:
            pass

        r0 = ttk.Frame(form)
        r0.grid(row=0, column=2, sticky=tk.W, padx=(GAP, 0), pady=(0, GAP))
        ttk.Button(r0, text="选择文件夹",
                   command=self.choose_steam_dir).pack(side=tk.LEFT)
        ttk.Button(r0, text="导入 autoexec",
                   command=self.import_autoexec).pack(side=tk.LEFT, padx=(GAP, 0))
        ttk.Button(r0, text="刷新",
                   command=self.refresh_users).pack(side=tk.LEFT, padx=(GAP, 0))
        ttk.Button(r0, text="诊断",
                   command=self.show_diagnosis).pack(side=tk.LEFT, padx=(GAP, 0))

        # 行 1：账户
        ttk.Label(form, text="账户:",
                  anchor=tk.E, width=12).grid(
            row=1, column=0, sticky=tk.EW, padx=(0, GAP), pady=(0, GAP))
        self.user_combo = ttk.Combobox(form, textvariable=self.user_var,
                                       state="readonly")
        self.user_combo.grid(row=1, column=1, sticky=tk.EW, pady=(0, GAP))
        r1 = ttk.Frame(form)
        r1.grid(row=1, column=2, sticky=tk.W, padx=(GAP, 0), pady=(0, GAP))
        ttk.Button(r1, text="载入配置",
                   command=self.load_selected_user).pack(side=tk.LEFT)
        self.online_check = ttk.Checkbutton(
            r1, text="联网翻译",
            variable=self.online_var, command=self.on_online_toggle)
        self.online_check.pack(side=tk.LEFT, padx=(GAP * 2, 0))

        # 行 2：搜索 + 模式
        ttk.Label(form, text="搜索:",
                  anchor=tk.E, width=12).grid(
            row=2, column=0, sticky=tk.EW, padx=(0, GAP))

        search_sub = ttk.Frame(form)
        search_sub.grid(row=2, column=1, sticky=tk.W)
        e = ttk.Entry(search_sub, textvariable=self.search_var, width=32)
        e.pack(side=tk.LEFT)
        e.bind("<KeyRelease>", self._on_search_changed)
        ttk.Button(search_sub, text="清除",
                   command=self._clear_search).pack(
            side=tk.LEFT, padx=(GAP, 0))

        mode_box = ttk.Frame(form)
        mode_box.grid(row=2, column=2, sticky=tk.E, padx=(GAP, 0))
        self.mode_label = ttk.Label(
            mode_box, textvariable=self.mode_var,
            foreground="#006600", font=("", 9, "bold"))
        self.mode_label.pack(side=tk.LEFT)
        ttk.Label(
            mode_box, text="  不会联网，一切在本机完成",
            foreground="#666666").pack(side=tk.LEFT)

        # Notebook
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(GAP, 0))

        cf = ttk.Frame(self.notebook)
        self.notebook.add(cf, text="ConVars 配置")
        self.convar_tree = self._create_tree(
            cf,
            columns=("source", "key", "value"),
            headings=("来源", "键", "值"),
            widths=(90, 260, 380))

        kf = ttk.Frame(self.notebook)
        self.notebook.add(kf, text="按键绑定")
        self.keys_tree = self._create_tree(
            kf,
            columns=("value", "value_cn", "key", "key_cn", "trans"),
            headings=("值", "值说明", "设置项", "中文说明", "翻译来源"),
            widths=(140, 160, 140, 160, 90))

        vf = ttk.Frame(self.notebook)
        self.notebook.add(vf, text="视频设置")
        self.video_tree = self._create_tree(
            vf,
            columns=("key", "key_cn", "value", "value_cn", "trans"),
            headings=("设置项", "中文说明", "值", "值说明", "翻译来源"),
            widths=(240, 200, 100, 180, 90))

        rf = ttk.Frame(self.notebook)
        self.notebook.add(rf, text="原始文件预览")
        self.raw_text = tk.Text(rf, wrap=tk.NONE, font=("Consolas", 10))
        ysb = ttk.Scrollbar(rf, orient=tk.VERTICAL,
                            command=self.raw_text.yview)
        xsb = ttk.Scrollbar(rf, orient=tk.HORIZONTAL,
                            command=self.raw_text.xview)
        self.raw_text.configure(yscrollcommand=ysb.set,
                                xscrollcommand=xsb.set)
        self.raw_text.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        rf.rowconfigure(0, weight=1)
        rf.columnconfigure(0, weight=1)

    def _create_tree(self, parent, columns, headings, widths):
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        for col, head, w in zip(columns, headings, widths):
            tree.heading(col, text=head)
            tree.column(col, width=w, anchor=tk.W, stretch=True)
        vsb = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=tree.yview)
        hsb = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        return tree

    # ---------- Steam 输入框占位逻辑 ----------
    def _set_placeholder(self):
        self._steam_placeholder_active = True
        self.steam_path_var.set(STEAM_PLACEHOLDER)
        try:
            self.steam_entry.configure(foreground="#999999")
        except Exception:
            pass

    def _clear_placeholder(self):
        self._steam_placeholder_active = False
        try:
            self.steam_entry.configure(foreground="#000000")
        except Exception:
            pass

    def _on_steam_focus_in(self, event=None):
        if self._steam_placeholder_active:
            self.steam_path_var.set("")
            self._clear_placeholder()

    def _on_steam_focus_out(self, event=None):
        if not self.steam_path_var.get().strip():
            self._set_placeholder()

    def _on_steam_key(self, event=None):
        if self._steam_placeholder_active:
            self.steam_path_var.set("")
            self._clear_placeholder()

    # ---------- 关于窗口 ----------
    def _show_about(self):
        win = tk.Toplevel(self)
        win.title("关于")
        win.transient(self)
        win.resizable(False, False)

        frame = ttk.Frame(win, padding=(40, 32))
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=APP_NAME,
                  font=("", 14, "bold")).pack(anchor=tk.W)

        meta = ttk.Frame(frame)
        meta.pack(anchor=tk.W, pady=(8, 0))
        ttk.Label(meta, text=f"版本 v{APP_VERSION}").pack(side=tk.LEFT)
        ttk.Label(meta, text=f"    Made by {APP_AUTHOR}").pack(side=tk.LEFT)

        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(
            fill=tk.X, pady=18)

        ttk.Label(frame, text="找到我").pack(anchor=tk.W)

        links = ttk.Frame(frame)
        links.pack(anchor=tk.W, pady=(12, 0))
        make_clickable(links, GITHUB_TEXT, GITHUB_URL, side=tk.LEFT)
        make_clickable(links, TELEGRAM_TEXT, TELEGRAM_URL,
                       side=tk.LEFT, padx=(36, 0))

        center_window(win, min_w=420, min_h=240)
        win.grab_set()
        win.focus_set()

    # ---------- 下拉框选项构建 ----------
    def _refresh_user_combo(self, select_autoexec: bool = False):
        """重建下拉框选项：vcfg 账户 + 可选的 autoexec 条目。"""
        displays = [u["display"] for u in self.users]
        if self._autoexec_path is not None:
            displays.append(f"autoexec ({self._autoexec_path.name})")

        self.user_combo["values"] = displays
        if not displays:
            self.user_var.set("")
            return

        if select_autoexec and self._autoexec_path is not None:
            self.user_combo.current(len(self.users))
        else:
            self.user_combo.current(0)

    def _is_autoexec_selected(self) -> bool:
        if self._autoexec_path is None:
            return False
        return self.user_combo.current() == len(self.users)

    # ---------- Steam / 用户 ----------
    def _auto_locate(self):
        sp = find_steam_path()
        if sp:
            self._clear_placeholder()
            self.steam_path_var.set(str(sp))
            self.steam_path = sp
            self.refresh_users()
        else:
            self.status_var.set("没找到 Steam 目录，选一下吧")

    def choose_steam_dir(self):
        d = filedialog.askdirectory(title="选择 Steam 文件夹")
        if d:
            self._clear_placeholder()
            self.steam_path_var.set(d)
            self.refresh_users()

    def import_autoexec(self):
        path = filedialog.askopenfilename(
            title="选择 autoexec.cfg 文件",
            filetypes=[("CFG 配置文件", "*.cfg"),
                       ("文本文件", "*.txt"),
                       ("所有文件", "*.*")])
        if not path:
            return
        self._autoexec_path = Path(path)

        # 刷新下拉框，把 autoexec 追加到末尾并自动选中
        self._refresh_user_combo(select_autoexec=True)

        # 立即加载 autoexec（覆盖任何现有视图）
        self._source_raw = None
        self._load_autoexec_file(self._autoexec_path)

    def refresh_users(self):
        ps = self.steam_path_var.get().strip()
        if ps == STEAM_PLACEHOLDER or not ps:
            messagebox.showwarning("提示", "先选一个 Steam 文件夹吧")
            return
        path = Path(ps)
        if not path.is_dir():
            messagebox.showwarning("提示", f"这个路径不可用：{ps}")
            return

        if path.name.lower() == "userdata":
            path = path.parent

        self.steam_path = path
        self.steam_path_var.set(str(path))

        self.users = scan_steam_users(path)
        if not self.users and self._autoexec_path is None:
            self.user_combo["values"] = []
            self.user_var.set("")
            self.status_var.set("没找到 CS2 的配置目录，检查一下路径？")
            return

        self._refresh_user_combo()
        if self.users:
            self.status_var.set(f"发现 {len(self.users)} 个账户")
        else:
            self.status_var.set("没找到 Steam 账户，但已导入 autoexec")

    def load_selected_user(self):
        idx = self.user_combo.current()
        if idx < 0:
            messagebox.showwarning("提示", "先选一个账户吧")
            return

        # 判断是不是 autoexec 条目（排在 vcfg 账户之后）
        if self._autoexec_path is not None and idx == len(self.users):
            self._source_raw = None
            self._load_autoexec_file(self._autoexec_path)
            return

        # 普通 vcfg 账户
        if idx >= len(self.users):
            return
        user = self.users[idx]
        self._load_cfg_dir(user["cfg_dir"],
                           source_desc=f"账户 {user['account_id']}")

    # ---------- 加载 vcfg（仅 vcfg 数据源） ----------
    def _load_cfg_dir(self, cfg_dir: Path, source_desc: str = ""):
        self.status_var.set(f"正在载入 {cfg_dir}")
        self.update_idletasks()

        result = load_cs2_configs(cfg_dir)
        self._source_raw = {
            "type": "vcfg",
            "convar": list(result["convar_items"]),
            "key": list(result["key_items"]),
            "video": list(result["video_items"]),
            "raw_texts": dict(result["raw_texts"]),
            "found_paths": dict(result["found_paths"]),
            "errors": list(result["errors"]),
            "cfg_dir": result["cfg_dir"],
            "source_desc": source_desc,
        }
        self._recompute_view()

    # ---------- 加载 autoexec.cfg（仅 autoexec 数据源） ----------
    def _load_autoexec_file(self, path: Path):
        self.status_var.set(f"正在载入 autoexec：{path}")
        self.update_idletasks()

        try:
            text = read_text_with_fallback(path)
        except IOError as e:
            messagebox.showerror("读取失败", str(e))
            return

        parsed = parse_autoexec_cfg(text)
        binds = parsed["binds"]
        settings = dedupe_settings(parsed["settings"])

        self._source_raw = {
            "type": "autoexec",
            "key": [("按键", k, v) for k, v in binds],
            "video": [(k, v) for k, v in settings],
            "raw_text": text,
            "filename": path.name,
            "path": str(path),
            "binds_count": len(binds),
            "settings_count": len(settings),
        }
        self._recompute_view()

    # ---------- 从单一数据源构建视图 ----------
    def _recompute_view(self):
        src = self._source_raw
        if src is None:
            self.convar_items = []
            self.key_items = []
            self.video_items = []
            self.raw_texts = {}
            self._build_diagnosis_empty()
            self.apply_filter()
            self._render_raw_texts()
            self.status_var.set("还没有载入任何配置")
            return

        if src["type"] == "vcfg":
            self.convar_items = list(src["convar"])
            self._build_key_items(src["key"])
            self._build_video_items(src["video"])
            self.raw_texts = dict(src["raw_texts"])
            self._build_diagnosis_vcfg()
        else:  # autoexec
            self.convar_items = []
            self._build_key_items(src["key"])
            self._build_video_items(src["video"])
            self.raw_texts = {
                f"autoexec ({src['filename']})": src["raw_text"]
            }
            self._build_diagnosis_autoexec()

        self.apply_filter()
        self._render_raw_texts()

        # 状态栏摘要
        miss_key = sum(1 for it in self.key_items
                       if not it["key_cn"] or not it["value_cn"])
        miss_video = sum(1 for it in self.video_items if not it["key_cn"])
        if src["type"] == "vcfg":
            head = f"vcfg {len(src['found_paths'])} 个文件"
        else:
            head = (f"autoexec {src['binds_count']} 按键、"
                    f"{src['settings_count']} 项设置")
        self.status_var.set(
            f"完成 · {head} · "
            f"{len(self.convar_items)} 配置 · "
            f"{len(self.key_items)} 按键（{miss_key} 未收录）· "
            f"{len(self.video_items)} 设置（{miss_video} 未收录）")

        if self.online_var.get():
            self.start_online_translate()

    # ---------- 诊断信息 ----------
    def _build_diagnosis_empty(self):
        self.last_diagnosis = (
            f"{APP_NAME} v{APP_VERSION}\n\n还没有载入任何配置")

    def _build_diagnosis_vcfg(self):
        src = self._source_raw
        lines = [f"{APP_NAME} v{APP_VERSION}", "", "vcfg 数据源",
                 f"  配置目录：{src['cfg_dir']}"]
        if src.get("source_desc"):
            lines.append(f"  来源：{src['source_desc']}")
        lines.append("  文件：")
        if src["found_paths"]:
            for name, p in src["found_paths"].items():
                lines.append(f"    [{name}] {p}")
        else:
            lines.append("    （没有找到文件）")
        if src["errors"]:
            lines.append("  提示：")
            for e in src["errors"]:
                lines.append(f"    - {e}")
        self.last_diagnosis = "\n".join(lines)

    def _build_diagnosis_autoexec(self):
        src = self._source_raw
        lines = [
            f"{APP_NAME} v{APP_VERSION}",
            "",
            "autoexec 数据源",
            f"  文件：{src['path']}",
            f"  按键绑定：{src['binds_count']} 条",
            f"  设置项：{src['settings_count']} 条（已去重）",
        ]
        self.last_diagnosis = "\n".join(lines)

    def _build_key_items(self, raw_items):
        items = []
        append = items.append
        for source, key, value in raw_items:
            key_cn = translate_key_local(key) or ""
            value_cn = translate_cmd_local(value) or ""
            trans = "本地" if (key_cn and value_cn) else ""
            append({
                "source": source, "key": key, "key_cn": key_cn,
                "value": value, "value_cn": value_cn, "trans": trans,
            })
        self.key_items = items

    def _build_video_items(self, raw_items):
        items = []
        append = items.append
        for key, value in raw_items:
            key_cn = translate_video_key_local(key) or ""
            value_cn = translate_video_value_local(key, value) or ""
            trans = "本地" if key_cn else ""
            append({
                "key": key, "key_cn": key_cn,
                "value": value, "value_cn": value_cn, "trans": trans,
            })
        self.video_items = items

    def _render_raw_texts(self):
        self.raw_text.delete("1.0", tk.END)
        insert = self.raw_text.insert
        for name, text in self.raw_texts.items():
            insert(tk.END, f"===== {name} =====\n")
            insert(tk.END, text)
            insert(tk.END, "\n\n")

    def show_diagnosis(self):
        text = self.last_diagnosis or "还没有载入任何配置"
        win = tk.Toplevel(self)
        win.title("诊断")
        win.geometry("760x480")
        win.transient(self)
        t = tk.Text(win, wrap=tk.NONE, font=("Consolas", 10))
        t.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        t.insert("1.0", text)
        t.configure(state="disabled")

    # ---------- 搜索防抖 ----------
    def _on_search_changed(self, event=None):
        if self._search_after_id is not None:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
        self._search_after_id = self.after(
            self.SEARCH_DEBOUNCE_MS, self._do_search)

    def _do_search(self):
        self._search_after_id = None
        self.apply_filter()

    def _clear_search(self):
        if self._search_after_id is not None:
            try:
                self.after_cancel(self._search_after_id)
            except Exception:
                pass
            self._search_after_id = None
        self.search_var.set("")
        self.apply_filter()

    # ---------- 过滤 / 渲染 ----------
    def apply_filter(self):
        kw = self.search_var.get().strip().lower()
        self._populate_convar(kw)
        self._populate_keys(kw)
        self._populate_video(kw)

    def _populate_convar(self, kw: str):
        tree = self.convar_tree
        tree.delete(*tree.get_children())
        insert = tree.insert
        if kw:
            for item in self.convar_items:
                src, key, value = item
                if (kw not in str(key).lower()
                        and kw not in str(value).lower()
                        and kw not in src.lower()):
                    continue
                insert("", tk.END, values=item)
        else:
            for item in self.convar_items:
                insert("", tk.END, values=item)

    def _populate_keys(self, kw: str):
        tree = self.keys_tree
        tree.delete(*tree.get_children())
        insert = tree.insert
        if kw:
            for it in self.key_items:
                hay = " ".join((it["key"], it["key_cn"],
                                str(it["value"]), it["value_cn"],
                                it["trans"])).lower()
                if kw not in hay:
                    continue
                insert("", tk.END, values=(
                    it["value"], it["value_cn"],
                    it["key"], it["key_cn"], it["trans"]))
        else:
            for it in self.key_items:
                insert("", tk.END, values=(
                    it["value"], it["value_cn"],
                    it["key"], it["key_cn"], it["trans"]))

    def _populate_video(self, kw: str):
        tree = self.video_tree
        tree.delete(*tree.get_children())
        insert = tree.insert
        if kw:
            for it in self.video_items:
                hay = " ".join((it["key"], it["key_cn"],
                                str(it["value"]), it["value_cn"],
                                it["trans"])).lower()
                if kw not in hay:
                    continue
                insert("", tk.END, values=(
                    it["key"], it["key_cn"], it["value"],
                    it["value_cn"], it["trans"]))
        else:
            for it in self.video_items:
                insert("", tk.END, values=(
                    it["key"], it["key_cn"], it["value"],
                    it["value_cn"], it["trans"]))

    # ---------- 联网开关 ----------
    def on_online_toggle(self):
        if self.online_var.get():
            ok = messagebox.askyesno(
                "联网翻译",
                "要开启联网翻译吗？\n\n"
                "• 只有本地没收录的项目才会联网\n"
                "• 请求会发送到 MyMemory\n"
                "• 相同内容只查一次，结果留在内存\n"
                "• 随时可以关掉\n\n"
                "开启")
            if not ok:
                self.online_var.set(False)
                return
            self.mode_var.set("联网")
            self.mode_label.configure(foreground="#CC6600")
            self._cancel_event.clear()
            if self.key_items or self.video_items:
                self.start_online_translate()
            else:
                self.status_var.set("已开启联网翻译")
        else:
            self._cancel_event.set()
            self.mode_var.set("离线")
            self.mode_label.configure(foreground="#006600")
            self.status_var.set("已回到离线")

    def start_online_translate(self):
        pending = []
        append = pending.append
        for it in self.key_items:
            if not it["key_cn"]:
                append((it, "key_cn", it["key"], "key"))
            if not it["value_cn"]:
                append((it, "value_cn", it["value"], "cmd"))
        for it in self.video_items:
            if not it["key_cn"]:
                append((it, "key_cn",
                        clean_video_key_for_translation(it["key"]),
                        "video"))

        if not pending:
            self.status_var.set("本地全都收录了")
            return
        if self._online_thread and self._online_thread.is_alive():
            return

        self._cancel_event.clear()
        self.status_var.set(f"有 {len(pending)} 项本地没收录，正在联网查询")

        translator = self.translator
        cancel_event = self._cancel_event
        total = len(pending)
        after = self.after

        def worker():
            done = 0
            refresh_every = 5
            for item, field, text, kind in pending:
                if cancel_event.is_set():
                    after(0, lambda: self.status_var.set("已取消"))
                    return
                result = translator.translate(text, cancel_event)
                if cancel_event.is_set():
                    after(0, lambda: self.status_var.set("已取消"))
                    return
                if result:
                    item[field] = result
                    if kind == "video":
                        item["trans"] = "联网"
                    else:
                        both_ok = bool(item["key_cn"]) and bool(item["value_cn"])
                        item["trans"] = ("本地 + 联网"
                                          if both_ok and item["trans"] == "本地"
                                          else "联网")
                done += 1
                if done % refresh_every == 0:
                    after(0, self.apply_filter)
                    after(0, lambda d=done, t=total:
                          self.status_var.set(f"联网补充中 {d}/{t}"))
            if not cancel_event.is_set():
                after(0, self.apply_filter)
                after(0, lambda: self.status_var.set(
                    f"联网补充完成，共 {total} 项"))

        self._online_thread = threading.Thread(target=worker, daemon=True)
        self._online_thread.start()


def main():
    app = CS2CfgViewerApp()
    app.mainloop()


if __name__ == "__main__":
    main()
