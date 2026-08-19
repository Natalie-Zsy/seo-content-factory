"""DataForSEO API 客户端。

文档：https://docs.dataforseo.com/
本工具主要使用 Keywords Data API 中的
「keywords_for_keywords」接口获取关键词的真实搜索量、竞争度、CPC。

注意：DataForSEO 是付费商业 API（按次计费），不是开源软件。
"""
from __future__ import annotations

import requests

from seo_factory.http import request_with_retry

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
    # 注意：live 接口的请求体是「顶层数组」，不是 {"data": [...]}
    payload = [
        {
            "keywords": keywords,
            "location_code": int(location_code),
            "language_code": language_code,
            "include_adult_keywords": False,
        }
    ]
    try:
        resp = request_with_retry("POST", url, json=payload, auth=(login, password), timeout=timeout)
    except requests.RequestException as exc:
        raise DataForSEOError(f"无法连接 DataForSEO：{exc}") from exc

    if resp.status_code == 401:
        raise DataForSEOError("DataForSEO 认证失败（401）：请检查 API Login 和 API Password 是否正确。")
    if resp.status_code == 402:
        raise DataForSEOError("DataForSEO 余额不足（402）：请到 https://app.dataforseo.com/ 充值。")
    if resp.status_code == 403:
        try:
            body = resp.json()
            msg = body.get("status_message", "") or ""
        except Exception:
            msg = ""
        if "verify" in msg.lower():
            raise DataForSEOError("DataForSEO 账户尚未完成验证：请登录 https://app.dataforseo.com/ 完成账户验证（检查注册邮箱里的验证邮件），完成后重试。")
        raise DataForSEOError(f"DataForSEO 拒绝访问（403）：{resp.text[:300]}")
    if resp.status_code != 200:
        raise DataForSEOError(f"DataForSEO 返回异常状态码 {resp.status_code}：{resp.text[:300]}")

    body = resp.json()
    tasks = body.get("tasks") or []
    if not tasks:
        raise DataForSEOError(f"DataForSEO 返回空结果：{body.get('status_message', '')}")

    first = tasks[0]
    sc = first.get("status_code")
    if sc != 20000:
        msg = first.get("status_message") or ""
        if sc == 40203:
            raise DataForSEOError(
                "DataForSEO 每日花费上限已用完（40203）。请登录 https://app.dataforseo.com/api-settings "
                "把每日花费上限调高（例如 1~2 美元），稍后再试。"
            )
        if sc == 40201:
            raise DataForSEOError(
                "DataForSEO 账户余额不足（40201）。请到 https://app.dataforseo.com 充值后再试。"
            )
        raise DataForSEOError(f"{sc}: {msg}")

    items: list[dict] = []
    for item in first.get("result") or []:
        items.append(
            {
                "keyword": item.get("keyword", ""),
                "search_volume": item.get("search_volume", 0) or 0,
                "competition_level": item.get("competition", ""),
                "competition": item.get("competition_index", 0) or 0,
                "cpc": item.get("cpc", 0) or 0,
                "intent": "",
            }
        )
        if len(items) >= limit:
            break
    return items


def _network_error_hint(exc: Exception) -> str:
    """把连接类异常转成给用户看的提示。"""
    name = type(exc).__name__
    detail = str(exc)
    return (
        f"网络连接失败（{name}）：DataForSEO 服务器在海外，当前网络线路不稳定"
        "（TLS 握手被重置/超时）。这通常与账号无关，请稍后重试；"
        "若持续失败，可换手机热点或其他网络再试。"
        f"\n详细信息：{detail[:200]}"
    )


def check_balance(login: str = "", password: str = "") -> dict:
    """查询账户余额（用于「设置」页显示剩余额度）。

    返回：{"ok": True, "balance": ..., "total_cost": ...}
     或  {"ok": False, "error": "原因说明"}
    """
    if not login or not password:
        return {"ok": False, "error": "还没有配置 DataForSEO 的 API Login / Password。"}
    try:
        resp = request_with_retry("GET", f"{API_BASE}/appendix/user_data", auth=(login, password), timeout=30)
    except requests.exceptions.RequestException as exc:
        return {"ok": False, "error": _network_error_hint(exc)}
    except Exception as exc:  # 兜底
        return {"ok": False, "error": f"查询异常：{exc}"}

    if resp.status_code == 401:
        return {"ok": False, "error": "DataForSEO 认证失败（401）：API Login / Password 不正确。请到 https://app.dataforseo.com 右上角头像 → API Access 核对。"}
    if resp.status_code == 402:
        return {"ok": False, "error": "DataForSEO 余额不足（402）：请到 https://app.dataforseo.com 充值。"}
    if resp.status_code == 403:
        try:
            msg = resp.json().get("status_message", "") or ""
        except Exception:
            msg = ""
        if "verify" in msg.lower():
            return {"ok": False, "error": "DataForSEO 账户尚未完成验证：请登录 https://app.dataforseo.com 检查注册邮箱里的验证邮件，完成后重试。"}
        if "whitelist" in msg.lower() or "access denied" in msg.lower():
            return {"ok": False, "error": f"DataForSEO 拒绝了当前 IP（403）：{msg}。请到 API 设置页把 IP 白名单清空留空。"}
        return {"ok": False, "error": f"DataForSEO 拒绝访问（403）：{resp.text[:200]}"}
    if resp.status_code != 200:
        return {"ok": False, "error": f"DataForSEO 返回异常状态码 {resp.status_code}：{resp.text[:200]}"}

    try:
        body = resp.json()
    except Exception:
        return {"ok": False, "error": "DataForSEO 返回内容无法解析。"}
    tasks = body.get("tasks") or []
    if not tasks:
        return {"ok": False, "error": f"DataForSEO 返回空结果：{body.get('status_message', '')}"}
    result = tasks[0].get("result") or []
    if not result:
        return {"ok": False, "error": "DataForSEO 返回结果为空。"}
    money = (result[0] or {}).get("money") or {}
    return {
        "ok": True,
        "balance": money.get("balance", 0),
        "total_cost": money.get("total", 0),
    }
def backlinks(
    target: str,
    mode: str = "one_per_domain",
    dofollow_only: bool = True,
    limit: int = 50,
    login: str = "",
    password: str = "",
    timeout: int = 120,
) -> dict:
    """查询目标域名的外链（Backlinks API，按返回条数计费）。

    :param target: 竞品域名或页面，例如 "competitor.com" 或 "https://example.com/page"
    :param mode: one_per_domain（每个域名一条）或 all（全部外链）
    :param dofollow_only: 是否只保留 DoFollow 链接
    :param limit: 最多返回多少条
    返回：{"total_count": int, "items": [ {domain_from_rank, url_from, anchor, url_to, dofollow, first_seen, last_seen} ]}
    """
    if not login or not password:
        raise DataForSEOError("还没有配置 DataForSEO 的 API Login / Password，请先到「设置」页填写。")

    url = f"{API_BASE}/backlinks/backlinks/live"
    task: dict = {
        "target": target,
        "mode": mode,
        "limit": int(limit),
    }
    if dofollow_only:
        task["filters"] = [["dofollow", "=", True]]
    payload = [task]
    try:
        resp = request_with_retry("POST", url, json=payload, auth=(login, password), timeout=timeout)
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
    sc = first.get("status_code")
    if sc != 20000:
        msg = first.get("status_message") or ""
        if sc == 40203:
            raise DataForSEOError(
                "DataForSEO 每日花费上限已用完（40203）。请登录 https://app.dataforseo.com/api-settings "
                "把每日花费上限调高（例如 2~5 美元），稍后再试。"
            )
        if sc == 40201:
            raise DataForSEOError("DataForSEO 账户余额不足（40201）。请到 https://app.dataforseo.com 充值后再试。")
        if "backlink" in msg.lower() and any(k in msg.lower() for k in ("not available", "disabled", "enable", "access")):
            raise DataForSEOError(
                f"Backlinks 接口暂不可用：{msg}。请到 https://app.dataforseo.com 确认账户已开通 Backlinks API。"
            )
        raise DataForSEOError(f"{sc}: {msg}")

    results = first.get("result") or []
    if not results:
        return {"total_count": 0, "items": []}
    result0 = results[0]
    items_raw = result0.get("items") or []
    items = []
    for it in items_raw:
        items.append(
            {
                "domain_from_rank": it.get("domain_from_rank", 0) or 0,
                "url_from": it.get("url_from", ""),
                "anchor": (it.get("anchor") or "").strip() or "（无锚文本）",
                "url_to": it.get("url_to", ""),
                "dofollow": bool(it.get("dofollow")),
                "first_seen": it.get("first_seen", ""),
                "last_seen": it.get("last_seen", ""),
            }
        )
    return {
        "total_count": result0.get("total_count", 0) or 0,
        "items": items,
    }

