"""竞品外链透视镜页：DataForSEO Backlinks API 反查竞品高质量外链。"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from seo_factory import dataforseo, storage
from ui import common


def render() -> None:
    st.title("🔗 竞品外链透视镜")
    st.caption("输入竞争对手网址，反查其高质量外链来源，挖掘外链建设机会（DataForSEO Backlinks API，按返回条数计费）")

    dfs = common.dfs_config()

    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        target_domain = st.text_input("🎯 竞品域名或页面", placeholder="例如 example.com 或 https://example.com/page")
    with col2:
        only_dofollow = st.checkbox("✅ 仅看 DoFollow 链接", value=True)
    with col3:
        one_per_domain = st.checkbox("🌐 每个域名仅限一条", value=True)

    limit = st.slider("最多返回多少条", 10, 200, 50, step=10)

    if st.button("🚀 开始透视竞品外链", type="primary", disabled=not target_domain.strip()):
        if not dfs["login"] or not dfs["password"]:
            st.error("请先到「设置」页填写 DataForSEO 的 API Login / Password。")
        else:
            with st.spinner("正在调用 DataForSEO Backlinks API，通常需要 10~60 秒…"):
                try:
                    result = dataforseo.backlinks(
                        target=target_domain.strip(),
                        mode="one_per_domain" if one_per_domain else "all",
                        dofollow_only=only_dofollow,
                        limit=limit,
                        login=dfs["login"],
                        password=dfs["password"],
                    )
                    st.session_state["bl_result"] = result
                    st.session_state["bl_target"] = target_domain.strip()
                    storage.log_event(
                        "backlinks",
                        f"竞品外链调查：{target_domain.strip()}",
                        {"total_count": result.get("total_count", 0), "returned": len(result.get("items") or [])},
                    )
                except dataforseo.DataForSEOError as exc:
                    st.error(f"❌ {exc}")

    result = st.session_state.get("bl_result", {})
    items = result.get("items") or []
    if not items:
        st.info("还没有结果。在上方输入竞品域名，点击「开始透视竞品外链」。")
        return

    st.subheader("📊 外链数据概览")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("查询到外链总数", f"{result.get('total_count', 0):,}")
    c2.metric("本次返回条数", f"{len(items):,}")
    high = sum(1 for it in items if (it.get("domain_from_rank") or 0) >= 50)
    c3.metric("高权重来源 (DR≥50)", f"{high}")
    dofollow_count = sum(1 for it in items if it.get("dofollow"))
    c4.metric("DoFollow 占比", f"{dofollow_count / len(items) * 100:.0f}%")

    st.markdown("---")
    st.subheader("🔍 详细外链列表")
    df = pd.DataFrame(items)
    df = df.rename(
        columns={
            "domain_from_rank": "来源域名权重(DR)",
            "url_from": "来源页面",
            "anchor": "锚文本",
            "url_to": "目标页面",
            "dofollow": "属性",
            "first_seen": "首次发现",
            "last_seen": "最近发现",
        }
    )
    df["属性"] = df["属性"].map(lambda v: "DoFollow" if v else "NoFollow")
    st.dataframe(
        df[["来源域名权重(DR)", "来源页面", "锚文本", "目标页面", "属性", "首次发现", "最近发现"]],
        use_container_width=True,
        hide_index=True,
        height=min(480, 35 * len(df) + 40),
        column_config={
            "来源页面": st.column_config.LinkColumn("来源页面", display_text="🔗 打开来源页"),
            "目标页面": st.column_config.LinkColumn("目标页面", display_text="🔗 打开目标页"),
        },
    )
    st.caption("提示：优先联系「高权重、DoFollow、锚文本自然」的来源页面，模仿其外链策略。")

    st.download_button(
        "📥 导出数据为 CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f'{st.session_state.get("bl_target", "backlinks")}_backlinks.csv',
        mime="text/csv",
    )