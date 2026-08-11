"""概览页：数据看板 + 配置检查 + 使用引导。"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from seo_factory import storage
from ui import common

TYPE_LABELS = {
    "keyword": "关键词调研",
    "title": "标题生成",
    "article": "文章生成",
    "wp_draft": "WP 草稿",
    "task": "每日任务",
}


def render() -> None:
    st.title("📊 概览")
    st.caption("SEO 内容分发工厂 · 全局看板（本工具的活动统计；正式数据以 WordPress 后台为准）")

    # 配置检查
    st.subheader("🔧 配置检查")
    checklist = common.config_checklist()
    cols = st.columns(len(checklist))
    for col, item in zip(cols, checklist):
        with col:
            if item["ok"]:
                st.success(f"✅ {item['name']}")
            else:
                st.warning(f"⚠️ {item['name']}")
            st.caption(item["hint"])

    # 统计卡片
    st.subheader("📈 本工具统计")
    s = storage.stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("累计调研关键词", s["keyword_count"])
    c2.metric("累计生成文章", s["article_count"])
    c3.metric("累计写入草稿", s["draft_count"])
    c4.metric("今日事件数", s["today_count"])

    # 最近动态
    st.subheader("🕘 最近动态")
    events = storage.recent_events(30)
    if not events:
        st.info("还没有活动记录。去「关键词调研」或「文章工厂」试试吧。")
    else:
        rows = [
            {
                "时间": e["ts"][11:19] + " " + e["ts"][:10],
                "类型": TYPE_LABELS.get(e["type"], e["type"]),
                "内容": e["summary"],
            }
            for e in events
        ]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # 工作流说明
    st.subheader("🚀 推荐工作流")
    st.markdown(
        """
1. **关键词调研**：选目标市场 → 输入种子词 → 获取真实搜索量（DataForSEO）→ 把想写的词加入“写作计划”
2. **文章工厂**：从写作计划选词 → 设置字数与定制指令 → 生成标题候选 → 锁定标题 → 生成正文
3. **分发管理**：把文章发送到 WordPress **草稿箱**（审核前不会公开）
4. **每日任务**：配置好 `daily_plan.json` + GitHub Secrets 后，每天自动生成一篇草稿
5. 每天到 WordPress 后台审核草稿，确认没问题再点“发布”

> 💡 需要先到「设置」页把三个平台的密钥配好，本页的配置检查才会全部变绿。
"""
    )