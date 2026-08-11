"""关键词调研页：DataForSEO 获取真实搜索量 + AI 中文备注 + 加入写作计划。"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from seo_factory import config as cfg
from seo_factory import dataforseo, llm, storage
from ui import common


def render() -> None:
    st.title("🔍 关键词调研")
    st.caption("第一步：选市场 → 输入种子词 → 获取真实搜索量与竞争数据（DataForSEO，按次计费）")

    dfs = common.dfs_config()
    llm_cfg = common.llm_config()

    col1, col2 = st.columns([1, 1])
    with col1:
        market = st.selectbox("目标市场", list(cfg.MARKETS.keys()), index=0, key="kw_market")
        info = cfg.market_info(market)
        st.caption(f"语言代码 {info['language_code']} · 地区代码 {info['location_code']}")
    with col2:
        seed_input = st.text_area(
            "核心关键词（每行一个）",
            placeholder="例如：\nGeschenkideen\npersonalisierte Geschenke",
            height=90,
        )

    limit = st.slider("每个种子词最多返回多少条相关词", 5, 50, 20, step=5)

    if st.button("🚀 获取真实搜索量（DataForSEO）", type="primary", disabled=not seed_input.strip()):
        seeds = [s.strip() for s in seed_input.splitlines() if s.strip()]
        if not dfs["login"] or not dfs["password"]:
            st.error("请先到「设置」页填写 DataForSEO 的 API Login / Password。")
        else:
            with st.spinner("正在调用 DataForSEO，通常需要几秒到几十秒…"):
                try:
                    items = dataforseo.keywords_for_keywords(
                        seeds,
                        location_code=info["location_code"],
                        language_code=info["language_code"],
                        login=dfs["login"],
                        password=dfs["password"],
                        limit=limit,
                    )
                    st.session_state["kw_results"] = items
                    st.session_state["kw_market_info"] = info
                    storage.log_event(
                        "keyword",
                        f"调研关键词：{', '.join(seeds[:3])}（{market}）",
                        {"count": len(items), "market": market},
                    )
                except dataforseo.DataForSEOError as exc:
                    st.error(f"❌ {exc}")

    items = st.session_state.get("kw_results", [])
    if not items:
        st.info("还没有结果。在上方输入种子词，点击「获取真实搜索量」。")
        return

    st.subheader("📋 调研结果")
    df = pd.DataFrame(items)
    df.columns = ["关键词", "月搜索量", "竞争度", "竞争指数", "CPC(€/$)", "搜索意图"]
    if "中文备注" not in df.columns:
        df["中文备注"] = ""

    # 若已有备注则合并
    notes = st.session_state.get("kw_notes", {})
    df["中文备注"] = df["关键词"].map(lambda k: notes.get(k, ""))

    st.dataframe(
        df[["关键词", "月搜索量", "竞争度", "竞争指数", "CPC(€/$)", "搜索意图", "中文备注"]],
        use_container_width=True,
        hide_index=True,
        height=min(420, 35 * len(df) + 40),
    )
    st.caption("提示：优先选择「月搜索量较高、竞争度适中」的关键词作为写作主题。")

    # AI 中文备注
    if st.button("✨ AI 生成中文备注（需要 LLM 配置）", disabled=not llm_cfg["api_key"]):
        with st.spinner("正在为关键词批量生成中文备注…"):
            try:
                kws = [it["keyword"] for it in items]
                notes = llm.annotate_keywords(kws, **llm_cfg)
                st.session_state["kw_notes"] = notes
                st.success(f"已为 {len(notes)} 个关键词生成中文备注。")
                st.rerun()
            except llm.LLMError as exc:
                st.error(f"❌ {exc}")

    # 加入写作计划
    st.subheader("📝 加入写作计划")
    choices = st.multiselect("勾选想要写作的关键词", [it["keyword"] for it in items])
    if st.button("加入写作计划"):
        for it in items:
            if it["keyword"] in choices:
                common.add_to_plan(
                    it["keyword"],
                    note=notes.get(it["keyword"], ""),
                    search_volume=it.get("search_volume", 0),
                )
        st.success(f"已将 {len(choices)} 个关键词加入写作计划。")
        st.rerun()

    plan = common.write_plan()
    if plan:
        st.divider()
        st.subheader(f"🗂️ 当前写作计划（{len(plan)} 个关键词）")
        plan_df = pd.DataFrame(plan)
        display_cols = [c for c in ["keyword", "search_volume", "note"] if c in plan_df.columns]
        st.dataframe(plan_df[display_cols], use_container_width=True, hide_index=True)
        if st.button("清空写作计划"):
            st.session_state["write_plan"] = []
            st.rerun()
        st.caption("到「文章工厂」页可以从写作计划里直接选词生成文章。")