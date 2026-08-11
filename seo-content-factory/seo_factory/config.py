"""配置读取。

读取优先级（从高到低）：
1. 用户在「设置」页填入的本次会话覆盖值（session_state）
2. Streamlit Secrets（部署到 Streamlit Cloud 时在网页上配置）
3. 环境变量（本地运行 / GitHub Actions）
4. 默认值

所有密钥只保存在平台的安全区域，绝不硬编码在代码里。
"""
from __future__ import annotations

import os


def _streamlit_secret(key: str) -> str:
    """尝试从 Streamlit Secrets 中读取，支持扁平键和分组写法。"""
    try:
        import streamlit as st  # type: ignore

        candidates = [key, key.upper(), key.lower()]
        for c in candidates:
            try:
                v = st.secrets[c]
            except Exception:
                continue
            if isinstance(v, str) and v.strip():
                return v.strip()

        # 分组写法示例：[dataforseo] login="..." / [llm] api_key="..."
        for section in ("dataforseo", "llm", "openai", "wordpress", "wp", "seo"):
            try:
                sec = st.secrets[section]
            except Exception:
                continue
            if isinstance(sec, dict):
                for c in candidates:
                    v = sec.get(c)
                    if isinstance(v, str) and v.strip():
                        return v.strip()
    except Exception:
        pass
    return ""


def get(key: str, default: str = "") -> str:
    """读取配置：secrets 优先，其次环境变量。"""
    v = _streamlit_secret(key)
    if v:
        return v
    return os.environ.get(key, default) or default


def get_bool(key: str, default: bool = False) -> bool:
    raw = get(key, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on", "是", "开启")


# 常用市场 -> (DataForSEO 语言代码, 地区代码)
# 完整地区代码表见 DataForSEO 文档：https://docs.dataforseo.com/v3/miscellaneous/available-countries
MARKETS: dict[str, dict] = {
    "德国 (Deutsch)":            {"language_code": "de", "location_code": 276},
    "美国 (English)":            {"language_code": "en", "location_code": 2840},
    "英国 (English)":            {"language_code": "en", "location_code": 2826},
    "加拿大 (English)":          {"language_code": "en", "location_code": 2124},
    "澳大利亚 (English)":        {"language_code": "en", "location_code": 2036},
    "法国 (Français)":           {"language_code": "fr", "location_code": 2250},
    "西班牙 (Español)":          {"language_code": "es", "location_code": 2458},
    "意大利 (Italiano)":         {"language_code": "it", "location_code": 2247},
    "荷兰 (Nederlands)":         {"language_code": "nl", "location_code": 2356},
    "波兰 (Polski)":             {"language_code": "pl", "location_code": 2370},
    "日本 (日本語)":             {"language_code": "ja", "location_code": 2392},
    "巴西 (Português)":          {"language_code": "pt", "location_code": 2076},
    "墨西哥 (Español)":          {"language_code": "es", "location_code": 2153},
    "新加坡 (English)":          {"language_code": "en", "location_code": 2058},
    "中国 (中文)":               {"language_code": "zh", "location_code": 2524},
}


def market_info(market_name: str) -> dict:
    """根据市场名称返回语言代码与地区代码，未知市场给默认值。"""
    return MARKETS.get(market_name, {"language_code": "en", "location_code": 2840})

# 市场英文名 -> 中文语言名（用于 LLM 提示词）
LANGUAGE_NAMES: dict[str, str] = {
    "Deutsch": "德语",
    "English": "英语",
    "Français": "法语",
    "Español": "西班牙语",
    "Italiano": "意大利语",
    "Nederlands": "荷兰语",
    "Polski": "波兰语",
    "日本語": "日语",
    "Português": "葡萄牙语",
    "中文": "中文",
}