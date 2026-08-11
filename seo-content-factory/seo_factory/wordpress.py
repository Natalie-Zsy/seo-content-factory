"""WordPress REST API 客户端。

功能：
- 把文章以「草稿」状态写入 WordPress（你审核后再手动发布）
- 列出最近草稿
- 修改文章状态

前置条件（详见 README 第 4 步）：
1. WordPress 已启用 REST API（固定链接不能是纯数字）
2. 已创建「应用程序密码」：WP 后台 → 用户 → 个人资料 → 应用程序密码
"""
from __future__ import annotations

import requests


class WordPressError(Exception):
    """WordPress 接口调用失败。"""


def _api(wp_url: str) -> str:
    return wp_url.strip().rstrip("/") + "/wp-json/wp/v2"


def _check_config(wp_url: str, username: str, app_password: str) -> None:
    if not wp_url or not username or not app_password:
        raise WordPressError("还没有配置 WordPress 的站点地址 / 用户名 / 应用程序密码，请先到「设置」页填写。")


def test_connection(wp_url: str, username: str, app_password: str) -> str:
    """验证 WordPress 连接，返回当前登录用户名。"""
    _check_config(wp_url, username, app_password)
    try:
        resp = requests.get(
            f"{_api(wp_url)}/users/me",
            auth=(username, app_password),
            timeout=30,
        )
    except requests.RequestException as exc:
        raise WordPressError(f"无法连接 WordPress：{exc}") from exc
    if resp.status_code == 401:
        raise WordPressError("WordPress 认证失败（401）：请检查用户名 / 应用程序密码是否正确。")
    if resp.status_code == 404:
        raise WordPressError("WordPress REST API 不可用（404）：请确认固定链接设置不是纯数字，并允许 REST API 访问。")
    if resp.status_code != 200:
        raise WordPressError(f"WordPress 返回异常状态码 {resp.status_code}：{resp.text[:300]}")
    data = resp.json()
    return data.get("name") or data.get("slug") or ""


def create_draft(
    wp_url: str,
    username: str,
    app_password: str,
    title: str,
    content_html: str,
    slug: str = "",
    meta_title: str = "",
    meta_description: str = "",
) -> dict:
    """创建一篇草稿，返回 {id, link, edit_link}。"""
    _check_config(wp_url, username, app_password)
    payload: dict = {
        "title": title,
        "content": content_html,
        "status": "draft",
    }
    if slug:
        payload["slug"] = slug
    meta = {}
    if meta_title:
        meta["_yoast_wpseo_title"] = meta_title
    if meta_description:
        meta["_yoast_wpseo_metadesc"] = meta_description
    if meta:
        payload["meta"] = meta

    try:
        resp = requests.post(
            f"{_api(wp_url)}/posts",
            json=payload,
            auth=(username, app_password),
            timeout=90,
        )
    except requests.RequestException as exc:
        raise WordPressError(f"无法连接 WordPress：{exc}") from exc

    if resp.status_code in (401, 403):
        raise WordPressError(f"WordPress 拒绝写入（{resp.status_code}）：请确认应用程序密码权限，或联系主机商放行 REST API。")
    if resp.status_code != 201 and resp.status_code != 200:
        raise WordPressError(f"创建草稿失败（{resp.status_code}）：{resp.text[:400]}")

    post = resp.json()
    base = wp_url.strip().rstrip("/")
    return {
        "id": post.get("id"),
        "link": post.get("link", ""),
        "edit_link": f"{base}/wp-admin/post.php?post={post.get('id')}&action=edit",
    }


def list_drafts(wp_url: str, username: str, app_password: str, per_page: int = 30) -> list[dict]:
    """按最近修改时间列出草稿。"""
    _check_config(wp_url, username, app_password)
    try:
        resp = requests.get(
            f"{_api(wp_url)}/posts",
            params={
                "status": "draft",
                "per_page": per_page,
                "orderby": "modified",
                "order": "desc",
            },
            auth=(username, app_password),
            timeout=60,
        )
    except requests.RequestException as exc:
        raise WordPressError(f"无法连接 WordPress：{exc}") from exc
    if resp.status_code != 200:
        raise WordPressError(f"获取草稿列表失败（{resp.status_code}）：{resp.text[:400]}")
    posts = resp.json()
    return [
        {
            "id": p.get("id"),
            "title": p.get("title", {}).get("rendered", ""),
            "link": p.get("link", ""),
            "modified": p.get("modified", ""),
            "status": p.get("status", ""),
        }
        for p in posts
    ]


def set_post_status(wp_url: str, username: str, app_password: str, post_id: int, status: str) -> str:
    """把某篇文章改为指定状态（如 publish），返回文章链接。"""
    _check_config(wp_url, username, app_password)
    try:
        resp = requests.post(
            f"{_api(wp_url)}/posts/{post_id}",
            json={"status": status},
            auth=(username, app_password),
            timeout=60,
        )
    except requests.RequestException as exc:
        raise WordPressError(f"无法连接 WordPress：{exc}") from exc
    if resp.status_code != 200:
        raise WordPressError(f"更新文章状态失败（{resp.status_code}）：{resp.text[:400]}")
    return resp.json().get("link", "")