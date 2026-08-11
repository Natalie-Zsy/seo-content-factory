"""本地活动记录（SQLite）。

记录：关键词调研、标题生成、文章生成、WordPress 草稿等事件，
用于「概览」页展示统计和最近动态。

说明：Streamlit Cloud 免费版的文件系统在每次重启/重新部署后可能重置，
因此这里只作轻量统计用途；正式运营数据请以 WordPress 后台为准。
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from seo_factory.timeutil import now_local

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "activity.db"


def _conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            type TEXT NOT NULL,
            summary TEXT NOT NULL,
            detail TEXT
        )
        """
    )
    conn.commit()
    return conn


def _now() -> str:
    return now_local().isoformat(timespec="seconds")


def log_event(event_type: str, summary: str, detail: dict | None = None) -> None:
    """记录一条事件。event_type 建议：keyword / title / article / wp_draft / task。"""
    try:
        conn = _conn()
        conn.execute(
            "INSERT INTO events (ts, type, summary, detail) VALUES (?,?,?,?)",
            (_now(), event_type, summary, json.dumps(detail, ensure_ascii=False) if detail else ""),
        )
        conn.commit()
        conn.close()
    except Exception:
        # 记录失败不影响主流程
        pass


def recent_events(limit: int = 30) -> list[dict]:
    try:
        conn = _conn()
        rows = conn.execute(
            "SELECT ts, type, summary, detail FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        conn.close()
        events = []
        for ts, etype, summary, detail in rows:
            try:
                detail_obj = json.loads(detail) if detail else None
            except Exception:
                detail_obj = None
            events.append({"ts": ts, "type": etype, "summary": summary, "detail": detail_obj})
        return events
    except Exception:
        return []


def stats() -> dict:
    """汇总统计，供概览页使用。"""
    try:
        conn = _conn()
        total_events = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        keyword_count = conn.execute("SELECT COUNT(*) FROM events WHERE type='keyword'").fetchone()[0]
        article_count = conn.execute("SELECT COUNT(*) FROM events WHERE type='article'").fetchone()[0]
        draft_count = conn.execute("SELECT COUNT(*) FROM events WHERE type='wp_draft'").fetchone()[0]
        today = _now()[:10]
        today_count = conn.execute(
            "SELECT COUNT(*) FROM events WHERE ts LIKE ?", (today + "%",)
        ).fetchone()[0]
        conn.close()
        return {
            "total_events": total_events,
            "keyword_count": keyword_count,
            "article_count": article_count,
            "draft_count": draft_count,
            "today_count": today_count,
        }
    except Exception:
        return {
            "total_events": 0,
            "keyword_count": 0,
            "article_count": 0,
            "draft_count": 0,
            "today_count": 0,
        }