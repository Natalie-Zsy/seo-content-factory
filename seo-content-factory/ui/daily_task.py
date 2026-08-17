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
**这套“每天自动生成”有两种方式：**

**方式 A（推荐 ✅）：本机定时运行**
在你自己电脑上双击 `install_task.bat`，一键创建 Windows 计划任务（默认每天 10:00）。中国网络直连你的 WordPress，不受海外拦截影响。详见 README 第 6 步。

**方式 B（备选）：GitHub Actions**
代码仓库里的 `.github/workflows/daily.yml` 每天定时在 GitHub 云端运行。如果你的 WordPress 主机屏蔽海外访问（测试连接超时），这种方式会连不上你的网站，请改用方式 A。

**无论哪种方式，每天自动执行的流程都一样：**
选词 →（可选）DataForSEO 调研 → LLM 生成标题 → LLM 生成正文 → 写入 WordPress 草稿箱

> 关键词每天自动轮换：按“一年中的第几天”依次取列表里的词，不需要任何存储。
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
        "语言": " + ".join(l.get("language_name", "") for l in daily.plan_languages(plan)),
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
                posts = result.get("posts") or []
                if posts:
                    for p in posts:
                        st.markdown(
                            f"**{p.get('language', '')}草稿：** {p.get('title', '')}　👉 "
                            f"[在 WordPress 中编辑]({p.get('edit_link', '')})"
                        )
                else:
                    st.markdown(f"**文章标题：** {result['title']}")
                    st.markdown(f"👉 [在 WordPress 中编辑草稿]({result.get('edit_link', '')})")
                if result.get("public_link"):
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