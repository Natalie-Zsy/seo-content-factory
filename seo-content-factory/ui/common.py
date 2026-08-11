"""页面公共工具。"""
from __future__ import annotations

import re
import streamlit as st

from seo_factory import config as cfg


def effective(key: str, env_key: str) -> str:
    """取配置：会话覆盖 > Streamlit Secrets > 环境变量。"""
    overrides = st.session_state.get("overrides", {})
    if key in overrides and overrides[key]:
        return str(overrides[key]).strip()
    return cfg.get(env_key)


def llm_config() -> dict:
    return {
        "api_key": effective("llm_api_key", "LLM_API_KEY"),
        "base_url": effective("llm_base_url", "LLM_BASE_URL"),
        "model": effective("llm_model", "LLM_MODEL"),
    }


def dfs_config() -> dict:
    return {
        "login": effective("dfs_login", "DATAFORSEO_LOGIN"),
        "password": effective("dfs_password", "DATAFORSEO_PASSWORD"),
    }


def wp_config() -> dict:
    return {
        "url": effective("wp_url", "WP_URL"),
        "username": effective("wp_username", "WP_USERNAME"),
        "app_password": effective("wp_app_password", "WP_APP_PASSWORD"),
    }


def config_checklist() -> list[dict]:
    """返回各项配置的检查结果。"""
    dfs = dfs_config()
    llm = llm_config()
    wp = wp_config()
    return [
        {"name": "DataForSEO（关键词数据）", "ok": bool(dfs["login"] and dfs["password"]), "hint": "设置页填写 API Login / Password"},
        {"name": "大模型 LLM（生成标题/正文）", "ok": bool(llm["api_key"]), "hint": "设置页填写 API Key / 接口地址 / 模型"},
        {"name": "WordPress（草稿箱）", "ok": bool(wp["url"] and wp["username"] and wp["app_password"]), "hint": "设置页填写站点地址 / 用户名 / 应用程序密码"},
    ]


def estimate_words(html_or_text: str) -> int:
    """粗略估算字数：中日韩按字符数，其余按空格分词。"""
    text = re.sub(r"<[^>]+>", "", html_or_text or "")
    cjk = len(re.findall(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", text))
    latin = len(text.split())
    return latin + cjk


def write_plan() -> list[dict]:
    """本次会话的“待写关键词”列表。"""
    return st.session_state.get("write_plan", [])


def add_to_plan(keyword: str, note: str = "", search_volume: int = 0) -> None:
    plan = st.session_state.setdefault("write_plan", [])
    if not any(item.get("keyword") == keyword for item in plan):
        plan.append({"keyword": keyword, "note": note, "search_volume": search_volume})


def remove_from_plan(keyword: str) -> None:
    plan = st.session_state.get("write_plan", [])
    st.session_state["write_plan"] = [item for item in plan if item.get("keyword") != keyword]

# 环境变量名 -> 设置页的会话覆盖键
OVERRIDE_MAP = {
    "DATAFORSEO_LOGIN": "dfs_login",
    "DATAFORSEO_PASSWORD": "dfs_password",
    "LLM_API_KEY": "llm_api_key",
    "LLM_BASE_URL": "llm_base_url",
    "LLM_MODEL": "llm_model",
    "WP_URL": "wp_url",
    "WP_USERNAME": "wp_username",
    "WP_APP_PASSWORD": "wp_app_password",
}


def session_settings() -> dict:
    """把当前生效配置组装成 {环境变量名: 值}，供每日任务模块使用。"""
    return {env_key: effective(session_key, env_key) for env_key, session_key in OVERRIDE_MAP.items()}