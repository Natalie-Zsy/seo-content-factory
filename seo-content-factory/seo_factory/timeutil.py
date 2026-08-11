"""时间工具：统一使用北京时间（Asia/Shanghai），并做兜底。"""
from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


def now_local() -> datetime:
    """返回北京时间；如果系统缺少时区数据，则退回系统本地时间。"""
    try:
        return datetime.now(ZoneInfo("Asia/Shanghai"))
    except Exception:  # noqa: BLE001
        return datetime.now()