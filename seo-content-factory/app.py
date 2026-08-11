"""SEO 内容分发工厂 - Streamlit 主程序。

运行方式：
    streamlit run app.py
"""
from __future__ import annotations

import streamlit as st

from ui import article_factory, daily_task, dispatch, keyword_research, overview, settings

st.set_page_config(
    page_title="SEO 内容分发工厂",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "📊 概览": overview.render,
    "🔍 关键词调研": keyword_research.render,
    "✍️ 文章工厂": article_factory.render,
    "📤 分发管理": dispatch.render,
    "⏰ 每日任务": daily_task.render,
    "⚙️ 设置": settings.render,
}

with st.sidebar:
    st.title("🚀 SEO 内容分发工厂")
    st.caption("多语种智能内容自动化系统")
    page = st.radio("导航", list(PAGES.keys()), label_visibility="collapsed")
    st.divider()
    st.caption("流程：调研词库 → 优选标题 → 生成正文 → 自动分发到 WP 草稿箱")

PAGES[page]()