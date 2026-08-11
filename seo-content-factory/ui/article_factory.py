"""文章工厂页：选词 → 生成标题候选 → 锁定标题 → 生成正文 → 发送到 WP 草稿箱。"""
from __future__ import annotations

import streamlit as st

from seo_factory import config as cfg
from seo_factory import llm, storage, wordpress
from ui import common


def render() -> None:
    st.title("✍️ 文章工厂")
    st.caption("第二步：从写作计划选词（或手动输入）→ 生成标题候选 → 锁定标题 → 生成正文 → 发送到 WordPress 草稿箱")

    llm_cfg = common.llm_config()
    wp = common.wp_config()

    # ---------- 1. 选择关键词 ----------
    st.subheader("1️⃣ 选择关键词")
    plan = common.write_plan()
    plan_keys = [p["keyword"] for p in plan]
    source = st.radio("关键词来源", ["从写作计划选择", "手动输入"], horizontal=True, key="fc_source")

    keyword = ""
    if source == "从写作计划选择" and plan_keys:
        keyword = st.selectbox("写作计划里的关键词", plan_keys, key="fc_plan_kw")
    else:
        keyword = st.text_input("手动输入关键词", placeholder="例如 Geschenkideen", key="fc_manual_kw")

    market = st.selectbox("目标市场（影响写作语言）", list(cfg.MARKETS.keys()), index=0, key="fc_market")
    _lang_en = market.split("(")[-1].rstrip(")").strip()
    language_name = cfg.LANGUAGE_NAMES.get(_lang_en, _lang_en)

    # ---------- 2. 全局设置 ----------
    st.subheader("2️⃣ 全局设置")
    c1, c2 = st.columns(2)
    min_words = c1.number_input("期望最少字数", 300, 5000, 900, step=50, key="fc_min")
    max_words = c2.number_input("期望最多字数", 300, 6000, 1100, step=50, key="fc_max")
    if min_words >= max_words:
        st.warning("最少字数应小于最多字数，请调整。")
    custom_instruction = st.text_area(
        "定制指令（可选）",
        placeholder="例如：语气亲切专业；多给具体例子；面向德国普通消费者；避免陈词滥调…",
        height=80,
        key="fc_inst",
    )

    # ---------- 3. 生成标题 ----------
    st.subheader("3️⃣ 生成标题候选")
    if st.button("🎯 生成标题候选（LLM）", type="primary", disabled=not keyword.strip()):
        if not llm_cfg["api_key"]:
            st.error("请先到「设置」页配置 LLM API Key。")
        else:
            with st.spinner("正在生成标题，通常需要 10-60 秒…"):
                try:
                    titles = llm.generate_titles(
                        keyword=keyword.strip(),
                        language_name=language_name,
                        custom_instruction=custom_instruction,
                        **llm_cfg,
                    )
                    st.session_state["fc_titles"] = titles
                    st.session_state["fc_article"] = None
                    storage.log_event("title", f"为「{keyword.strip()}」生成标题候选", {"count": len(titles)})
                except llm.LLMError as exc:
                    st.error(f"❌ {exc}")

    titles = st.session_state.get("fc_titles", [])
    if titles:
        options = [f"📌 {t['title']}　｜　中文备注：{t['zh_note'] or '（无）'}" for t in titles]
        chosen = st.radio("选择要使用的标题（外文标题 + 中文备注）", options, key="fc_title_choice")
        idx = options.index(chosen)
        chosen_title = titles[idx]["title"]
        use_foreign = st.checkbox("选用纯外文标题（推荐，标题不掺中文）", value=True, key="fc_use_foreign")
        if use_foreign:
            final_title = chosen_title
        else:
            final_title = st.text_input("可在此手动修改最终标题", value=chosen_title, key="fc_final_title")
        st.session_state["fc_final_title"] = final_title

        # ---------- 4. 生成正文 ----------
        st.subheader("4️⃣ 生成正文")
        if st.button("📄 锁定标题并生成正文（LLM）", type="primary"):
            with st.spinner("正在撰写文章，通常需要 30 秒 - 2 分钟…"):
                try:
                    article = llm.generate_article(
                        keyword=keyword.strip(),
                        language_name=language_name,
                        min_words=min_words,
                        max_words=max_words,
                        custom_instruction=custom_instruction,
                        **llm_cfg,
                    )
                    st.session_state["fc_article"] = article
                    storage.log_event("article", f"生成文章：{final_title}", {"keyword": keyword.strip(), "words": common.estimate_words(article["content_html"])})
                except llm.LLMError as exc:
                    st.error(f"❌ {exc}")

    article = st.session_state.get("fc_article")
    if article:
        st.divider()
        st.subheader(f"📄 文章预览：{final_title}")
        words = common.estimate_words(article["content_html"])
        st.caption(f"估算字数：约 {words} 词　·　字数设置：{min_words}-{max_words}")
        st.markdown("**SEO 元信息**")
        st.code(
            f"标题(Title)：{article['title']}\n"
            f"别名(Slug)：{article['slug']}\n"
            f"SEO 标题：{article['meta_title']}\n"
            f"SEO 描述：{article['meta_description']}",
            language=None,
        )
        with st.expander("查看 / 复制正文 HTML", expanded=False):
            st.code(article["content_html"], language="html")
        st.markdown("**正文预览**")
        st.markdown(article["content_html"], unsafe_allow_html=True)

        # ---------- 5. 发送到 WordPress ----------
        st.subheader("5️⃣ 发送到 WordPress 草稿箱")
        st.caption("会以「草稿」状态写入，不会公开，你审核后再到 WP 后台发布。")
        if st.button("📤 发送到 WordPress 草稿箱", type="primary"):
            if not (wp["url"] and wp["username"] and wp["app_password"]):
                st.error("请先到「设置」页填写 WordPress 站点地址 / 用户名 / 应用程序密码。")
            else:
                with st.spinner("正在写入 WordPress…"):
                    try:
                        post = wordpress.create_draft(
                            wp_url=wp["url"],
                            username=wp["username"],
                            app_password=wp["app_password"],
                            title=final_title,
                            content_html=article["content_html"],
                            slug=article.get("slug", ""),
                            meta_title=article.get("meta_title", ""),
                            meta_description=article.get("meta_description", ""),
                        )
                        storage.log_event(
                            "wp_draft",
                            f"草稿已创建：{final_title}",
                            {"post_id": post.get("id"), "edit_link": post.get("edit_link", "")},
                        )
                        st.success("✅ 已写入 WordPress 草稿箱！")
                        st.markdown(f"👉 去审核：[在 WordPress 中编辑草稿]({post.get('edit_link', '')})")
                        st.markdown(f"预览链接（未发布，仅你可见）：{post.get('link', '')}")
                    except wordpress.WordPressError as exc:
                        st.error(f"❌ {exc}")