# -*- coding: utf-8 -*-
"""外观美化：主题切换、看板图标、背景自定义、字号调节，设置自动保存到浏览器地址栏。

用法：
    theme.bootstrap()      # 在 st.set_page_config 之后先调用：恢复保存的外观设置
    theme.apply_theme()    # 注入当前主题 CSS
    theme.render_selector()  # 放在侧边栏，用户可切换主题 / 图标 / 背景 / 字号

设置通过 st.query_params 保存在 URL 里（?scf=...），刷新页面、换设备打开同一链接都能恢复。
"""
from __future__ import annotations

import base64
import inspect
import json

import streamlit as st

DEFAULT_THEME = "清爽浅色"
DEFAULT_ICON = "🚀"
DEFAULT_FONT = "标准"
QP_KEY = "scf"  # 保存在网址里的参数名

# 新版 st.button 支持 width="stretch"，旧版只支持 use_container_width（已废弃）
_BUTTON_WIDTH_OK = "width" in inspect.signature(st.button).parameters

THEMES: dict[str, dict] = {
    "清爽浅色": {
        "desc": "白底黑字，简洁专业",
        "app_bg": "linear-gradient(160deg, #ffffff 0%, #eef3fa 100%)",
        "sidebar_bg": "#ffffff",
        "text": "#1f2430",
        "accent": "#1f6feb",
        "accent_text": "#ffffff",
        "metric_bg": "#ffffff",
        "border": "#e3e9f2",
        "bg_picker": "#ffffff",
    },
    "深色科技": {
        "desc": "深灰黑底，适合夜间使用",
        "app_bg": "linear-gradient(160deg, #0f172a 0%, #1e293b 100%)",
        "sidebar_bg": "#0b1220",
        "text": "#e2e8f0",
        "accent": "#38bdf8",
        "accent_text": "#0b1220",
        "metric_bg": "#1e293b",
        "border": "#334155",
        "bg_picker": "#0f172a",
    },
    "静谧深蓝": {
        "desc": "深蓝商务风",
        "app_bg": "linear-gradient(160deg, #0c2340 0%, #123a5c 100%)",
        "sidebar_bg": "#0a1d35",
        "text": "#eaf2fb",
        "accent": "#4da3ff",
        "accent_text": "#0a1d35",
        "metric_bg": "#123a5c",
        "border": "#2a5275",
        "bg_picker": "#0c2340",
    },
    "清新薄荷": {
        "desc": "浅绿薄荷，清新柔和",
        "app_bg": "linear-gradient(160deg, #f0fdf4 0%, #dcfce7 100%)",
        "sidebar_bg": "#f7fef9",
        "text": "#14532d",
        "accent": "#16a34a",
        "accent_text": "#ffffff",
        "metric_bg": "#ffffff",
        "border": "#bbf7d0",
        "bg_picker": "#f0fdf4",
    },
    "暖阳橙": {
        "desc": "暖橙渐变，活力明亮",
        "app_bg": "linear-gradient(160deg, #fff7ed 0%, #ffedd5 100%)",
        "sidebar_bg": "#fffaf5",
        "text": "#431407",
        "accent": "#ea580c",
        "accent_text": "#ffffff",
        "metric_bg": "#ffffff",
        "border": "#fed7aa",
        "bg_picker": "#fff7ed",
    },
    "渐变星空紫": {
        "desc": "紫蓝渐变，科技感十足",
        "app_bg": "linear-gradient(160deg, #2e1065 0%, #4c1d95 60%, #1e1b4b 100%)",
        "sidebar_bg": "#24104f",
        "text": "#f5f3ff",
        "accent": "#c084fc",
        "accent_text": "#2e1065",
        "metric_bg": "#3b1d7a",
        "border": "#5b3aa0",
        "bg_picker": "#2e1065",
    },
    "樱花粉": {
        "desc": "柔粉渐变，温柔清爽",
        "app_bg": "linear-gradient(160deg, #fdf2f8 0%, #fce7f3 100%)",
        "sidebar_bg": "#fff5fa",
        "text": "#500724",
        "accent": "#db2777",
        "accent_text": "#ffffff",
        "metric_bg": "#ffffff",
        "border": "#fbcfe8",
        "bg_picker": "#fdf2f8",
    },
    "商务墨绿": {
        "desc": "深墨绿渐变，沉稳商务",
        "app_bg": "linear-gradient(160deg, #0f2e24 0%, #14532d 100%)",
        "sidebar_bg": "#0b241c",
        "text": "#ecfdf5",
        "accent": "#34d399",
        "accent_text": "#052e16",
        "metric_bg": "#14532d",
        "border": "#2f6b4f",
        "bg_picker": "#0f2e24",
    },
}

ICONS = ["🚀", "📈", "🔍", "✨", "🎯", "🌐", "🛠️", "⚡", "🧭", "🗂️", "📊", "🔥"]

FONT_SIZES = {"小": "15px", "标准": "16px", "大": "18px"}


def app_icon() -> str:
    """当前看板图标（用于侧边栏标题）。"""
    return st.session_state.get("app_icon", DEFAULT_ICON)


def _theme() -> dict:
    name = st.session_state.get("theme_name", DEFAULT_THEME)
    return THEMES.get(name, THEMES[DEFAULT_THEME])


def _bg_value() -> str:
    """背景优先级：上传的背景图 > 自定义背景色 > 主题默认。"""
    image = st.session_state.get("theme_image")
    if image:
        return f"url({image}) center / cover no-repeat fixed"
    color = st.session_state.get("theme_color")
    if color:
        return color
    return _theme()["app_bg"]


def _css() -> str:
    theme = _theme()
    accent = theme["accent"]
    border = theme["border"]
    text = theme["text"]
    font_size = FONT_SIZES.get(st.session_state.get("font_size", DEFAULT_FONT), "16px")
    image = st.session_state.get("theme_image")
    color = st.session_state.get("theme_color")
    if image:
        # 背景图：独立属性分开展开，更稳
        bg_extra = f"""background-image: url('{image}') !important;
    background-color: {theme["bg_picker"]} !important;
    background-size: cover !important;
    background-position: center !important;
    background-repeat: no-repeat !important;
    background-attachment: fixed !important;"""
    elif color:
        bg_extra = f"background: {color} !important;"
    else:
        bg_extra = f"background: {theme['app_bg']} !important;"
    return f"""
<style>
html, body, .stApp, [data-testid="stAppViewContainer"] {{
    font-size: {font_size} !important;
}}
.stApp, [data-testid="stAppViewContainer"] {{
    {bg_extra}
    color: {text} !important;
}}
/* 让正文内容区透明，背景图/背景色才能铺满整个页面 */
[data-testid="stAppViewContainer"] .block-container,
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
[data-testid="stAppViewContainer"] .main {{
    background: transparent !important;
}}
[data-testid="stHeader"] {{
    background: transparent !important;
}}
[data-testid="stSidebar"] {{
    background: {theme["sidebar_bg"]} !important;
    color: {text} !important;
    border-right: 1px solid {border} !important;
}}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] {{
    color: {text} !important;
}}
h1, h2, h3, h4, h5 {{
    color: {text} !important;
}}
[data-testid="stSidebar"] h1 {{
    font-size: 1.35rem !important;
}}
a {{ color: {accent} !important; }}
a:hover {{ text-decoration: underline; }}
blockquote {{
    border-left: 4px solid {accent} !important;
    background: {accent}14 !important;
    border-radius: 0 10px 10px 0 !important;
    padding: 10px 14px !important;
}}
code {{
    background: {border}88 !important;
    border-radius: 6px !important;
    padding: 2px 6px !important;
}}
hr {{ border-color: {border} !important; }}
[data-testid="stMetric"] {{
    background: {theme["metric_bg"]} !important;
    border: 1px solid {border} !important;
    border-radius: 14px !important;
    padding: 14px 18px !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.06) !important;
}}
[data-testid="stMetricValue"] {{ color: {accent} !important; }}
[data-testid="stMetricLabel"] {{ opacity: 0.8 !important; }}
[data-testid="stBaseButton-primary"] > button {{
    background: {accent} !important;
    border-color: {accent} !important;
    color: {theme["accent_text"]} !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
}}
[data-testid="stBaseButton-primary"] > button:hover {{ filter: brightness(1.08); }}
.stButton > button, .stDownloadButton > button,
[data-testid="stBaseButton-secondary"] > button,
[data-testid="stBaseButton-tertiary"] > button {{
    border-radius: 10px !important;
}}
.stButton > button:hover,
[data-testid="stBaseButton-secondary"] > button:hover,
[data-testid="stBaseButton-tertiary"] > button:hover {{
    border-color: {accent} !important;
    color: {accent} !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{ font-weight: 600; }}
[data-testid="stTabs"] [data-baseweb="tab"][aria-selected="true"] {{ color: {accent} !important; }}
[data-testid="stExpander"] {{
    border: 1px solid {border} !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}}
[data-testid="stExpanderHeader"] {{ font-weight: 600; }}
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {{
    border: 1px solid {border} !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}}
[data-testid="stAlert"] {{
    border-radius: 10px !important;
    border: 1px solid {border} !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label {{
    border-radius: 10px !important;
    padding: 6px 10px !important;
    transition: background 0.15s ease !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: {accent}22 !important;
}}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {{
    background: {accent}26 !important;
    color: {accent} !important;
    font-weight: 600 !important;
}}
[data-testid="stCaptionContainer"] {{ opacity: 0.85; }}
</style>
"""


def _current_settings() -> dict:
    data = {
        "theme_name": st.session_state.get("theme_name", DEFAULT_THEME),
        "app_icon": st.session_state.get("app_icon", DEFAULT_ICON),
        "font_size": st.session_state.get("font_size", DEFAULT_FONT),
    }
    color = st.session_state.get("theme_color")
    if color:
        data["theme_color"] = color
    return data


def _persist() -> None:
    """把当前设置写入网址（?scf=...），仅在设置变化时写一次，避免多余的刷新。"""
    sig = json.dumps(_current_settings(), ensure_ascii=False, sort_keys=True)
    if st.session_state.get("_persisted_sig") == sig:
        return
    st.session_state["_persisted_sig"] = sig
    try:
        st.query_params[QP_KEY] = sig
    except Exception:
        pass  # 某些环境不支持写 query_params 时静默降级


def bootstrap() -> None:
    """从网址参数恢复外观设置（每个会话执行一次）。"""
    if st.session_state.get("_theme_restored"):
        return
    st.session_state["_theme_restored"] = True
    try:
        raw = st.query_params.get(QP_KEY)
        if not raw:
            return
        data = json.loads(raw)
    except (TypeError, ValueError):
        return
    if not isinstance(data, dict):
        return
    if data.get("theme_name") in THEMES:
        st.session_state["theme_name"] = data["theme_name"]
    if data.get("app_icon") in ICONS:
        st.session_state["app_icon"] = data["app_icon"]
    if data.get("font_size") in FONT_SIZES:
        st.session_state["font_size"] = data["font_size"]
    if isinstance(data.get("theme_color"), str) and data["theme_color"].startswith("#"):
        st.session_state["theme_color"] = data["theme_color"]


def apply_theme() -> None:
    """注入当前主题 CSS，在 st.set_page_config 之后调用。"""
    st.markdown(_css(), unsafe_allow_html=True)


def render_selector() -> None:
    """侧边栏外观设置：主题 / 图标 / 背景 / 字号，改动自动保存到网址。"""
    with st.expander("🎨 外观美化（可选）", expanded=False):
        # 1) 主题
        names = list(THEMES.keys())
        cur_theme = st.session_state.get("theme_name", DEFAULT_THEME)
        idx = names.index(cur_theme) if cur_theme in names else 0
        chosen = st.selectbox("界面主题", names, index=idx, key="_theme_select")
        if chosen != cur_theme:
            st.session_state["theme_name"] = chosen
            st.session_state.pop("theme_color", None)  # 换主题后清除自定义背景色
            st.session_state.pop(f"_bg_pick_{cur_theme}", None)  # 同时清掉旧主题的取色器记忆
            st.rerun()
        st.caption(THEMES[chosen]["desc"])

        # 2) 看板图标（宫格点选）
        cur_icon = st.session_state.get("app_icon", DEFAULT_ICON)
        st.markdown("看板图标")
        cols = st.columns(6)
        for i, icon in enumerate(ICONS):
            with cols[i % 6]:
                if _BUTTON_WIDTH_OK:
                    pressed = st.button(icon, key=f"_icon_{icon}", help=f"使用 {icon}", width="stretch")
                else:
                    pressed = st.button(icon, key=f"_icon_{icon}", help=f"使用 {icon}", use_container_width=True)
                if pressed:
                    st.session_state["app_icon"] = icon
                    st.rerun()
        st.caption(f"当前图标：{cur_icon}")

        # 3) 背景：自定义颜色 或 上传图片
        st.markdown("背景")
        use_custom = st.toggle(
            "自定义背景色（覆盖主题默认）",
            value=bool(st.session_state.get("theme_color")),
            key="_bg_toggle",
        )
        if use_custom:
            cur_color = st.session_state.get("theme_color") or THEMES[chosen].get("bg_picker", "#ffffff")
            color = st.color_picker("选择背景色", value=cur_color, key=f"_bg_pick_{chosen}")
            if color != st.session_state.get("theme_color"):
                st.session_state["theme_color"] = color
                st.rerun()
        elif st.session_state.get("theme_color"):
            st.session_state.pop("theme_color", None)
            st.rerun()

        if st.session_state.get("theme_image"):
            st.caption("✅ 已设置自定义背景图（本次会话有效，刷新后需重新上传）")
            if st.button("🗑️ 清除背景图"):
                st.session_state.pop("theme_image", None)
                st.rerun()
        else:
            uploaded = st.file_uploader(
                "上传背景图片（可选，PNG/JPG，建议 6MB 内；仅本次会话有效）",
                type=["png", "jpg", "jpeg", "webp"],
                key="_theme_bg_file",
            )
            if uploaded is not None:
                data = uploaded.getvalue()
                if len(data) > 6 * 1024 * 1024:
                    st.warning("图片超过 6MB，请换一张小一点的图。")
                else:
                    b64 = base64.b64encode(data).decode("utf-8")
                    mime = getattr(uploaded, "type", None) or "image/png"
                    st.session_state["theme_image"] = f"data:{mime};base64,{b64}"
                    st.rerun()

        # 4) 字号
        cur_font = st.session_state.get("font_size", DEFAULT_FONT)
        font = st.select_slider("界面字号", options=list(FONT_SIZES.keys()), value=cur_font, key="_font_select")
        if font != cur_font:
            st.session_state["font_size"] = font
            st.rerun()

        # 5) 恢复默认
        if st.button("↺ 恢复默认外观"):
            for k in (
                "theme_name", "app_icon", "font_size", "theme_color", "theme_image",
                "_theme_restored", "_persisted_sig",
                "_theme_select", "_font_select", "_bg_toggle", "_theme_bg_file",
            ):
                st.session_state.pop(k, None)
            for t in THEMES:
                st.session_state.pop(f"_bg_pick_{t}", None)
            try:
                del st.query_params[QP_KEY]
            except Exception:
                pass
            st.rerun()

        # 把当前设置保存到网址（有变化才写）
        _persist()


