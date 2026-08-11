"""分发管理页：查看 WordPress 草稿、连接测试、本工具写入记录。"""
from __future__ import annotations

import streamlit as st
import pandas as pd

from seo_factory import storage, wordpress
from ui import common


def render() -> None:
    st.title("📤 分发管理")
    st.caption("第三步：管理已经写入 WordPress 草稿箱的文章。正式审核与发布在 WordPress 后台完成。")

    wp = common.wp_config()

    # 连接状态
    if not (wp["url"] and wp["username"] and wp["app_password"]):
        st.warning("尚未配置 WordPress。请先到「设置」页填写 站点地址 / 用户名 / 应用程序密码。")
        return

    col1, col2 = st.columns([3, 1])
    with col1:
        st.info(f"站点：{wp['url']}")
    with col2:
        if st.button("测试连接", key="wp_test"):
            with st.spinner("正在连接…"):
                try:
                    user = wordpress.test_connection(**wp)
                    st.success(f"✅ 连接成功（{user}）")
                except wordpress.WordPressError as exc:
                    st.error(f"❌ {exc}")

    st.divider()
    st.subheader("📥 最近草稿（WordPress）")
    if st.button("🔄 刷新草稿列表"):
        with st.spinner("正在拉取草稿…"):
            try:
                drafts = wordpress.list_drafts(**wp, per_page=30)
                st.session_state["wp_drafts"] = drafts
                st.session_state["wp_drafts_error"] = None
            except wordpress.WordPressError as exc:
                st.session_state["wp_drafts"] = []
                st.session_state["wp_drafts_error"] = str(exc)

    if st.session_state.get("wp_drafts_error"):
        st.error(f"❌ {st.session_state['wp_drafts_error']}")

    drafts = st.session_state.get("wp_drafts")
    if drafts is None:
        st.info("点击「刷新草稿列表」查看 WordPress 中的草稿。")
    elif not drafts:
        st.success("🎉 当前没有草稿。")
    else:
        rows = []
        for d in drafts:
            edit_url = f"{wp['url'].rstrip('/')}/wp-admin/post.php?post={d['id']}&action=edit"
            rows.append({"ID": d["id"], "标题": d["title"], "修改时间": d["modified"], "编辑链接": edit_url})
        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
            column_config={"编辑链接": st.column_config.LinkColumn("编辑链接", display_text="打开编辑页")},
        )

    st.divider()
    st.subheader("📝 本工具写入记录")
    events = [e for e in storage.recent_events(100) if e["type"] in ("wp_draft", "task")]
    if not events:
        st.info("还没有通过本工具创建过草稿。")
    else:
        rows = []
        for e in events:
            link = ""
            detail = e.get("detail") or {}
            if detail.get("edit_link"):
                link = f"[编辑草稿]({detail['edit_link']})"
            rows.append({"时间": e["ts"], "类型": "草稿" if e["type"] == "wp_draft" else "每日任务", "内容": e["summary"], "操作": link})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.info("💡 发布流程：在 WordPress 后台打开草稿 → 检查排版/图片/链接 → 点「发布」。工具永远只写「草稿」状态，不会自动公开。")