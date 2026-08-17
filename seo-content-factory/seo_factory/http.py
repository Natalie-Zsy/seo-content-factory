"""HTTP 请求工具：对连接类错误自动重试。

背景：部分网络（代理/VPN 不稳定、运营商干扰）会出现间歇性的
SSL 握手失败（SSLEOFError / 连接重置 / 连接超时），重试通常能成功。
"""
from __future__ import annotations

import time

import requests


def request_with_retry(method: str, url: str, attempts: int = 5, delay: float = 3.0, **kwargs):
    """发请求并自动重试连接类错误；认证错误(401)等不会重试。"""
    last_exc: Exception | None = None
    for i in range(attempts):
        try:
            return requests.request(method, url, **kwargs)
        except requests.exceptions.ConnectionError as exc:
            last_exc = exc
            if i < attempts - 1:
                time.sleep(delay * (i + 1))
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("request_with_retry 未执行成功")  # pragma: no cover