"""每日任务页：查看自动化配置、手动立即执行一次。"""
from __future__ import annotations

import json

import streamlit as st
import pandas as pd

from seo_factory import config as cfg
from seo_factory import daily
from ui import common


def render() -> None:
    st.title("⏰ 每日任务")
    st.caption("第四步：每天自动生成一篇新文章到 WordPress 草稿箱，你审核后再发布。")

    with st.expander("📖 自动化的原理（必读）", expanded=True):
        st.markdown(
            """
**这套“每天自动生成”不靠 Streamlit，而是靠 GitHub Actions（GitHub 免费提供的定时任务）。**

流程：
1. 代码仓库里有 `.github/workflows/daily.yml`，里面写了一个定时触发器（默认每天 UTC 02:00 = 北京时间 10:00）
2. 到时间后，GitHub 会在云端运行 `python scripts/daily_article.py`
3. 该脚本读取仓库里的 `config/daily_plan.json`（今天写什么主题、多少字、什么语言）+ GitHub 仓库 Secrets（密钥）
4. 自动执行：选词 → （可选）DataForSEO 调研 → LLM 生成标题 → LLM 生成正文 → 写入 WordPress 草稿箱
5. 你每天早上到 WordPress 后台审核草稿，点「发布」

**需要你手动做的只有三件事（详见 README 第 6 步）：**
1. 把 `config/daily_plan.example.json` 复制为 `config/daily_plan.json` 并改成你的关键词
2. 在 GitHub 仓库 → Settings → Secrets and variables → Actions 里添加密钥（DataForSEO / LLM / WordPress）
3. 在 GitHub 仓库 → Actions → Daily SEO Article → Run workflow 手动触发一次，验证成功

> 关键词每天自动轮换：按“一年中的第几天”依次取列表里的词，不重复需要任何存储。
"""
        )

    # 当前计划展示
    plan = daily.load_plan()
    st.subheader("🗂️ 当前每日计划（config/daily_plan.json）")
    if daily.PLAN_PATH.exists():
        st.success(f"已读取配置文件：{daily.PLAN_PATH}")
    else:
        st.warning("还没有创建 daily_plan.json，当前展示的是内置默认值。请复制 config/daily_plan.example.json 为 config/daily_plan.json 并修改。")

    show = {
        "语言": plan.get("language_name"),
        "关键词列表": "、".join(plan.get("keywords") or []),
        "是否调研扩展": "是（DataForSEO 优选出搜索量高的词）" if plan.get("research_expand") else "否",
        "期望字数": f"{plan.get('min_words')} - {plan.get('max_words')}",
        "标题候选数": plan.get("titles_count"),
        "定制指令": (plan.get("custom_instruction") or "")[:60] + ("…" if len(plan.get("custom_instruction") or "") > 60 else ""),
    }
    st.dataframe(pd.DataFrame([{"项目": k, "配置": v} for k, v in show.items()]), use_container_width=True, hide_index=True)

    st.divider()

    # 立即执行
    st.subheader("⚡ 立即执行一次今日任务")
    st.caption("在网页里手动跑一遍完整的「选词 → 调研 → 生成 → 写草稿」流程，用于测试或补写。密钥使用「设置」页里已配置的。")
    if st.button("▶️ 立即执行今日任务", type="primary"):
        with st.spinner("正在执行：选词 → 调研 → 生成标题 → 生成正文 → 写入 WordPress 草稿…（可能需要 2-5 分钟）"):
            try:
                result = daily.run(plan=plan, verbose=False, settings=common.session_settings())
                st.success("✅ 今日任务执行成功！")
                st.markdown(f"**今日关键词：** {result['keyword']}")
                st.markdown(f"**文章标题：** {result['title']}")
                st.markdown(f"👉 [在 WordPress 中编辑草稿]({result.get('edit_link', '')})")
                st.markdown(f"预览（未发布）：{result.get('public_link', '')}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"❌ 执行失败：{exc}")
                st.info("常见原因：密钥未配置 / DataForSEO 余额不足 / WordPress 应用密码错误。可展开下方「开发人员原始报文」查看细节（脚本把最近一次结果写在 data/last_article.json）。")

    st.divider()
    st.subheader("🔎 配置检查")
    checks = common.config_checklist()
    for item in checks:
        if item["ok"]:
            st.success(f"✅ {item['name']}")
        else:
            st.warning(f"⚠️ {item['name']}：{item['hint']}")

    st.caption("提示：如果只是想要“每天固定写某几个主题”，把关键词写进 daily_plan.json 的 keywords 列表即可，列表越长，每天轮换越多样。")