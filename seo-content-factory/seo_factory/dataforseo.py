"""DataForSEO API 客户端。

文档：https://docs.dataforseo.com/
本工具主要使用 Keywords Data API 中的
「keywords_for_keywords」接口获取关键词的真实搜索量、竞争度、CPC。

注意：DataForSEO 是付费商业 API（按次计费），不是开源软件。
"""
from __future__ import annotations

import requests

API_BASE = "https://api.dataforseo.com/v3"


class DataForSEOError(Exception):
    """DataForSEO 接口调用失败。"""


def keywords_for_keywords(
    keywords: list[str],
    location_code: int,
    language_code: str,
    login: str = "",
    password: str = "",
    limit: int = 20,
    timeout: int = 90,
) -> list[dict]:
    """获取关键词及其相关词的真实搜索量、竞争度、CPC。

    :param keywords: 种子关键词列表，例如 ["Geschenkideen"]
    :param location_code: DataForSEO 地区代码（如德国 276）
    :param language_code: DataForSEO 语言代码（如 de）
    :param login: DataForSEO API Login（通常是注册邮箱）
    :param password: DataForSEO API Password（API 密钥）
    :param limit: 每个种子词最多返回多少条相关词
    """
    if not login or not password:
        raise DataForSEOError("还没有配置 DataForSEO 的 API Login / Password，请先到「设置」页填写。")

    url = f"{API_BASE}/keywords_data/google_ads/keywords_for_keywords/live"
    payload = {
        "data": [
            {
                "keywords": keywords,
                "location_code": int(location_code),
                "language_code": language_code,
                "limit": int(limit),
                "include_adult_keywords": False,
            }
        ]
    }
    try:
        resp = requests.post(url, json=payload, auth=(login, password), timeout=timeout)
    except requests.RequestException as exc:
        raise DataForSEOError(f"无法连接 DataForSEO：{exc}") from exc

    if resp.status_code == 401:
        raise DataForSEOError("DataForSEO 认证失败（401）：请检查 API Login 和 API Password 是否正确。")
    if resp.status_code == 402:
        raise DataForSEOError("DataForSEO 余额不足（402）：请到 https://app.dataforseo.com/ 充值。")
    if resp.status_code != 200:
        raise DataForSEOError(f"DataForSEO 返回异常状态码 {resp.status_code}：{resp.text[:300]}")

    body = resp.json()
    tasks = body.get("tasks") or []
    if not tasks:
        raise DataForSEOError(f"DataForSEO 返回空结果：{body.get('status_message', '')}")

    first = tasks[0]
    if first.get("status_code") != 20000:
        raise DataForSEOError(f"{first.get('status_code')}: {first.get('status_message')}")

    items: list[dict] = []
    for result in first.get("result") or []:
        for it in result.get("items") or []:
            ki = it.get("keyword_info") or {}
            intent = (it.get("search_intent_info") or {}).get("main_intent", "")
            items.append(
                {
                    "keyword": it.get("keyword", ""),
                    "search_volume": ki.get("search_volume", 0) or 0,
                    "competition_level": ki.get("competition_level", ""),
                    "competition": ki.get("competition", 0) or 0,
                    "cpc": ki.get("cpc", 0) or 0,
                    "intent": intent,
                }
            )
    return items


def check_balance(login: str = "", password: str = "") -> dict:
    """查询账户余额（用于「设置」页显示剩余额度）。"""
    if not login or not password:
        return {}
    try:
        resp = requests.get(
            f"{API_BASE}/account",
            auth=(login, password),
            timeout=30,
        )
        if resp.status_code != 200:
            return {}
        body = resp.json()
        tasks = body.get("tasks") or []
        if not tasks:
            return {}
        result = tasks[0].get("result") or []
        if not result:
            return {}
        r = result[0]
        return {
            "balance": r.get("balance", 0),
            "total_cost": r.get("total_cost", 0),
        }
    except Exception:
        return {}