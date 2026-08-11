"""每日自动任务：选词 → 调研 → 生成标题 → 生成正文 → 写入 WP 草稿箱。

这个模块同时被两个地方调用：
1. scripts/daily_article.py（GitHub Actions 定时任务，命令行运行）
2. Streamlit 应用里的「每日任务」页面（点击“立即执行”）
"""
from __future__ import annotations

import json
from pathlib import Path

from seo_factory import config as cfg
from seo_factory import dataforseo, llm, storage, wordpress
from seo_factory.timeutil import now_local

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PLAN_PATH = PROJECT_ROOT / "config" / "daily_plan.json"

DEFAULT_PLAN: dict = {
    "enabled": True,
    "language_name": "德语（德国）",
    "language_code": "de",
    "location_code": 276,
    "keyword_mode": "manual",
    "keywords": ["Geschenkideen"],
    "research_expand": True,
    "research_max_items": 15,
    "min_words": 900,
    "max_words": 1100,
    "custom_instruction": "目标读者是当地普通消费者，语气亲切专业，多给具体可执行的建议和例子。",
    "titles_count": 5,
    "title_language": "foreign",
}

# 环境变量名 -> 会话配置键（Streamlit 设置页里对应的小写键）
ENV_KEYS = (
    "DATAFORSEO_LOGIN",
    "DATAFORSEO_PASSWORD",
    "LLM_API_KEY",
    "LLM_BASE_URL",
    "LLM_MODEL",
    "WP_URL",
    "WP_USERNAME",
    "WP_APP_PASSWORD",
)


def load_plan() -> dict:
    """读取 config/daily_plan.json；文件不存在时返回默认计划。"""
    if PLAN_PATH.exists():
        try:
            plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
            merged = dict(DEFAULT_PLAN)
            merged.update(plan)
            return merged
        except Exception:
            return dict(DEFAULT_PLAN)
    return dict(DEFAULT_PLAN)


def _day_index() -> int:
    """以“一年中的第几天”作为轮换依据，保证每天选词不同且无需存状态。"""
    return now_local().timetuple().tm_yday


def pick_keyword(plan: dict) -> str:
    """确定今天要写的关键词（按天数在关键词列表里轮换）。"""
    keywords = [k.strip() for k in (plan.get("keywords") or []) if k and k.strip()]
    if not keywords:
        raise RuntimeError("daily_plan.json 中没有配置 keywords，请先在配置里填入至少一个关键词。")
    return keywords[_day_index() % len(keywords)]


def _research(keyword: str, plan: dict, settings: dict) -> list[str]:
    """可选的调研扩展：用 DataForSEO 拉取相关词，按搜索量排序后取前 N 个。"""
    login = settings.get("DATAFORSEO_LOGIN", "")
    password = settings.get("DATAFORSEO_PASSWORD", "")
    if not (plan.get("research_expand") and login and password):
        return [keyword]
    try:
        items = dataforseo.keywords_for_keywords(
            [keyword],
            location_code=plan.get("location_code", 276),
            language_code=plan.get("language_code", "de"),
            login=login,
            password=password,
            limit=int(plan.get("research_max_items", 15)),
        )
    except dataforseo.DataForSEOError as exc:
        print(f"[提示] 调研失败，退回使用原关键词：{exc}")
        return [keyword]
    items.sort(key=lambda x: x.get("search_volume", 0), reverse=True)
    candidates = [it["keyword"] for it in items if it.get("keyword")][: int(plan.get("research_max_items", 15))]
    if not candidates:
        return [keyword]
    return candidates


def _settings() -> dict:
    """读取配置（secrets/环境变量）。网页端会传入会话覆盖值。"""
    return {key: cfg.get(key) for key in ENV_KEYS}


def run(plan: dict | None = None, verbose: bool = True, settings: dict | None = None) -> dict:
    """执行一次完整任务，返回结果字典。任何一步失败都会抛出异常。"""
    plan = plan or load_plan()
    settings = settings if settings is not None else _settings()

    keyword = pick_keyword(plan)
    language_name = plan.get("language_name", "德语（德国）")

    if verbose:
        print(f"[1/4] 今日关键词：{keyword}")

    # 1. 关键词调研（可选）
    candidates = _research(keyword, plan, settings)
    target = keyword
    if candidates and candidates[0] != keyword:
        target = candidates[0]
        if verbose:
            print(f"[调研] 根据搜索量优选出：{target}")

    # 2. 生成标题
    titles = llm.generate_titles(
        keyword=target,
        language_name=language_name,
        count=int(plan.get("titles_count", 5)),
        custom_instruction=plan.get("custom_instruction", ""),
        api_key=settings.get("LLM_API_KEY", ""),
        base_url=settings.get("LLM_BASE_URL", ""),
        model=settings.get("LLM_MODEL", ""),
    )
    chosen_title = titles[0]["title"]
    if verbose:
        print(f"[2/4] 选中标题：{chosen_title}")

    # 3. 生成正文
    article = llm.generate_article(
        keyword=target,
        language_name=language_name,
        min_words=int(plan.get("min_words", 900)),
        max_words=int(plan.get("max_words", 1100)),
        custom_instruction=plan.get("custom_instruction", ""),
        api_key=settings.get("LLM_API_KEY", ""),
        base_url=settings.get("LLM_BASE_URL", ""),
        model=settings.get("LLM_MODEL", ""),
    )
    if verbose:
        print(f"[3/4] 文章已生成：{article['title']}")

    # 4. 写入 WordPress 草稿箱
    post = wordpress.create_draft(
        wp_url=settings.get("WP_URL", ""),
        username=settings.get("WP_USERNAME", ""),
        app_password=settings.get("WP_APP_PASSWORD", ""),
        title=article["title"],
        content_html=article["content_html"],
        slug=article.get("slug", ""),
        meta_title=article.get("meta_title", ""),
        meta_description=article.get("meta_description", ""),
    )
    if verbose:
        print(f"[4/4] 已写入 WordPress 草稿：{post['edit_link']}")

    storage.log_event(
        "task",
        f"每日任务完成：{article['title']}",
        {"keyword": target, "post_id": post.get("id"), "link": post.get("edit_link", "")},
    )
    storage.log_event(
        "wp_draft",
        f"草稿已创建：{article['title']}",
        {"post_id": post.get("id"), "link": post.get("edit_link", "")},
    )

    result = {
        "keyword": target,
        "title": article["title"],
        "post_id": post.get("id"),
        "edit_link": post.get("edit_link", ""),
        "public_link": post.get("link", ""),
    }
    # 供本地排查使用：把最近一次结果写到 data/last_article.json
    try:
        out = PROJECT_ROOT / "data" / "last_article.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({**result, "article": article}, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass
    return result