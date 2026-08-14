"""设置页：填写三个平台的密钥，并保存到 Streamlit Secrets。"""
from __future__ import annotations

import streamlit as st

from seo_factory import dataforseo, wordpress
from ui import common

LLM_PRESETS = {
    "OpenAI（gpt-4o-mini，适合英文市场）": ("https://api.openai.com/v1", "gpt-4o-mini"),
    "DeepSeek（deepseek-chat，便宜，适合中文/英文）": ("https://api.deepseek.com/v1", "deepseek-chat"),
    "Kimi / Moonshot（moonshot-v1-8k）": ("https://api.moonshot.cn/v1", "moonshot-v1-8k"),
    "通义千问（qwen-plus）": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
    "自定义": ("", ""),
}


def _save(key: str, value: str) -> None:
    st.session_state.setdefault("overrides", {})
    st.session_state["overrides"][key] = value.strip()


def render() -> None:
    st.title("⚙️ 设置")
    st.caption(
        "在这里填写三个平台的密钥。保存后仅对「本次会话」生效；"
        "要让网页每次都自动读取，请把密钥配置到 Streamlit Cloud 的 Secrets 里（见下方说明，或 README 第 5 步）。"
    )

    # ---------- DataForSEO ----------
    st.subheader("1️⃣ DataForSEO（关键词搜索量数据）")
    st.caption("注册：https://app.dataforseo.com/ → 登录后右上角头像 → API Access 查看 API Login / API Password。按次计费，先充少量余额测试。")
    dfs = common.dfs_config()
    dfs_login = st.text_input("API Login（通常是注册邮箱）", value=dfs["login"], key="set_dfs_login")
    dfs_password = st.text_input("API Password（API 密钥）", value=dfs["password"], type="password", key="set_dfs_password")
    c1, c2 = st.columns(2)
    if c1.button("保存到本次会话", key="save_dfs"):
        _save("dfs_login", dfs_login)
        _save("dfs_password", dfs_password)
        st.success("已保存（本次会话有效）。")
    if c2.button("检查账户余额", key="check_dfs"):
        if not (dfs_login and dfs_password):
            st.warning("请先填写并保存 DataForSEO 凭证。")
        else:
            with st.spinner("查询中…"):
                info = dataforseo.check_balance(dfs_login, dfs_password)
            if info:
                st.info(f"账户余额：${info.get('balance', '?')}　·　累计消费：${info.get('total_cost', '?')}")
            else:
                st.error("余额查询失败（可能凭证有误，或账户不支持该接口）。")

    # ---------- LLM ----------
    st.subheader("2️⃣ 大模型 LLM（生成标题 / 正文）")
    st.caption("兼容所有 OpenAI 风格接口：OpenAI / DeepSeek / Kimi / 通义千问 / 本地 Ollama。")
    llm = common.llm_config()
    preset = st.selectbox("快捷选择模型", list(LLM_PRESETS.keys()), index=0, key="set_llm_preset")
    preset_url, preset_model = LLM_PRESETS[preset]
    default_url = llm["base_url"] or preset_url
    default_model = llm["model"] or preset_model
    llm_key = st.text_input("API Key", value=llm["api_key"], type="password", key="set_llm_key")
    llm_url = st.text_input("接口地址 Base URL", value=default_url, key="set_llm_url",
                            placeholder="https://api.openai.com/v1")
    llm_model = st.text_input("模型名称 Model", value=default_model, key="set_llm_model",
                              placeholder="gpt-4o-mini / deepseek-chat / …")
    if st.button("保存到本次会话", key="save_llm"):
        _save("llm_api_key", llm_key)
        _save("llm_base_url", llm_url)
        _save("llm_model", llm_model)
        st.success("已保存（本次会话有效）。")

    # ---------- WordPress ----------
    st.subheader("3️⃣ WordPress（草稿箱）")
    st.caption(
        "站点地址示例：https://你的域名.com（不要带 /wp-admin）\n\n"
        "创建应用程序密码：WP 后台 → 用户 → 个人资料 → 拉到「应用程序密码」→ 起个名字 → 生成 → 复制（只显示一次）。"
    )
    wp = common.wp_config()
    wp_url = st.text_input("站点地址", value=wp["url"], key="set_wp_url", placeholder="https://example.com")
    wp_user = st.text_input("用户名", value=wp["username"], key="set_wp_user")
    wp_app = st.text_input("应用程序密码", value=wp["app_password"], type="password", key="set_wp_app")
    c1, c2 = st.columns(2)
    if c1.button("保存到本次会话", key="save_wp"):
        _save("wp_url", wp_url)
        _save("wp_username", wp_user)
        _save("wp_app_password", wp_app)
        st.success("已保存（本次会话有效）。")
    if c2.button("测试 WordPress 连接", key="test_wp"):
        if not (wp_url and wp_user and wp_app):
            st.warning("请先填写并保存 WordPress 配置。")
        else:
            with st.spinner("连接中…"):
                try:
                    user = wordpress.test_connection(wp_url, wp_user, wp_app)
                    st.success(f"✅ 连接成功（{user}）")
                except wordpress.WordPressError as exc:
                    st.error(f"❌ {exc}")

    st.divider()

    # ---------- 网络诊断 ----------
    st.subheader("🛰️ 网络诊断（排查 WordPress 海外拦截）")
    st.caption("查询当前服务器（云端 Streamlit 或你本机）访问外网时使用的出口 IP，用于在主机防火墙放行。")
    if st.button("查询本服务器出口 IP", key="net_ip"):
        with st.spinner("查询中…"):
            try:
                import requests as _req

                ip = _req.get("https://api.ipify.org", timeout=15).text.strip()
                st.info(f"当前出口 IP：**{ip}**")
                st.caption("把该 IP 加到 WordPress 主机防火墙放行名单即可。注意：Streamlit 应用重启后出口 IP 可能变化，变了需重新查并更新；GitHub Actions 定时任务的 IP 段请用 https://api.github.com/meta 里的 actions 列表。")
            except Exception as exc:  # noqa: BLE001
                st.error(f"查询失败：{exc}")

    st.divider()

    # ---------- 永久保存到 Streamlit Secrets ----------
    st.subheader("🔐 永久保存：配置到 Streamlit Cloud Secrets")
    st.markdown(
        """
在 Streamlit Cloud 部署后：
1. 打开你的应用 → 右上角 **⋮ 菜单 → Settings → Secrets**
2. 在文本框中粘贴下面的内容（把 `xxx` 换成真实值），然后点 **Save**

> 网页里的「保存到本次会话」只是为了快速测试；下次重启应用会丢失。
> 密钥只会保存在 Streamlit/GitHub 的安全区域，**绝不会**写入代码或仓库。
"""
    )
    secrets_toml = f'''# ===== DataForSEO =====
DATAFORSEO_LOGIN = "{dfs_login or "你的 DataForSEO API Login（邮箱）"}"
DATAFORSEO_PASSWORD = "{dfs_password or "你的 DataForSEO API Password"}"

# ===== 大模型 LLM =====
LLM_API_KEY = "{llm_key or "你的 LLM API Key"}"
LLM_BASE_URL = "{llm_url or "https://api.openai.com/v1"}"
LLM_MODEL = "{llm_model or "gpt-4o-mini"}"

# ===== WordPress =====
WP_URL = "{wp_url or "https://你的域名.com"}"
WP_USERNAME = "{wp_user or "你的 WP 用户名"}"
WP_APP_PASSWORD = "{wp_app or "你的 WP 应用程序密码"}"
'''
    st.code(secrets_toml, language="toml")
    st.download_button("⬇️ 下载 secrets.toml 模板", secrets_toml, file_name="secrets.toml", mime="text/plain")

    st.divider()
    st.subheader("🧪 当前配置状态")
    for item in common.config_checklist():
        if item["ok"]:
            st.success(f"✅ {item['name']}")
        else:
            st.warning(f"⚠️ {item['name']}：{item['hint']}")
    st.caption("说明：这里显示的是「已生效」的状态。若你已填入但显示未配置，请先点击对应区块的「保存到本次会话」。")