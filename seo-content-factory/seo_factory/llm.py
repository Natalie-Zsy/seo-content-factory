"""大模型（LLM）客户端：用于生成标题、正文、中文备注。

兼容所有 OpenAI 风格的接口：
- OpenAI：https://api.openai.com/v1
- DeepSeek：https://api.deepseek.com/v1
- Moonshot / Kimi：https://api.moonshot.cn/v1
- 通义千问：https://dashscope.aliyuncs.com/compatible-mode/v1
- 本地 Ollama：http://localhost:11434/v1
"""
from __future__ import annotations

import json
import re

import requests


class LLMError(Exception):
    """大模型接口调用失败。"""


def _endpoint(base_url: str) -> str:
    base_url = (base_url or "https://api.openai.com/v1").strip().rstrip("/")
    if base_url.endswith("/chat/completions"):
        return base_url
    return f"{base_url}/chat/completions"


def chat(
    messages: list[dict],
    api_key: str = "",
    base_url: str = "",
    model: str = "",
    temperature: float = 0.7,
    max_tokens: int | None = None,
    timeout: int = 300,
) -> str:
    """调用 chat/completions 接口，返回文本内容。"""
    if not api_key:
        raise LLMError("还没有配置 LLM API Key，请先到「设置」页填写。")

    payload: dict = {
        "model": model or "gpt-4o-mini",
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post(_endpoint(base_url), json=payload, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        raise LLMError(f"无法连接 LLM 接口：{exc}") from exc

    if resp.status_code == 401:
        raise LLMError("LLM 认证失败（401）：请检查 API Key 是否正确。")
    if resp.status_code == 402:
        raise LLMError("LLM 余额不足（402）：请到对应平台充值。")
    if resp.status_code != 200:
        raise LLMError(f"LLM 接口返回 {resp.status_code}：{resp.text[:300]}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        raise LLMError(f"LLM 返回格式异常：{str(data)[:300]}") from exc


def extract_json(text: str):
    """从 LLM 输出中稳健地提取 JSON（兼容带 ```json 代码块的情况）。"""
    if not text:
        raise LLMError("LLM 返回了空内容。")

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # 找到最先出现的 JSON 起始字符（{ 或 [），按外层的括号配对截取
    start = None
    for ch in ("{", "["):
        idx = cleaned.find(ch)
        if idx != -1 and (start is None or idx < start):
            start = idx
    if start is None:
        raise LLMError(f"无法从 LLM 输出中解析 JSON：{text[:200]}")

    opener = cleaned[start]
    closer = "}" if opener == "{" else "]"
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(cleaned)):
        ch = cleaned[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return json.loads(cleaned[start : i + 1])
    raise LLMError(f"无法从 LLM 输出中解析 JSON：{text[:200]}")


def generate_titles(
    keyword: str,
    language_name: str,
    count: int = 5,
    custom_instruction: str = "",
    api_key: str = "",
    base_url: str = "",
    model: str = "",
    temperature: float = 0.8,
) -> list[dict]:
    """生成 N 个目标语言的文章标题候选，每个带中文备注。"""
    prompt = f"""你是资深的多语种 SEO 内容主编。请为关键词「{keyword}」生成 {count} 个面向{language_name}市场的高质量文章标题。

要求：
1. 标题全部用{language_name}撰写，地道自然，符合当地人的搜索习惯，不要有翻译腔
2. 标题中自然包含关键词「{keyword}」或其变体
3. 尽量覆盖不同角度：清单型、指南型、问题型、灵感型等
4. 每个标题同时给出简短的中文备注（用中文解释标题含义与目标读者）"""
    if custom_instruction.strip():
        prompt += f"\n5. 额外定制指令：{custom_instruction.strip()}"
    prompt += """
6. 只输出 JSON 数组，不要输出任何其他内容，格式如下：
[{"title": "外文标题", "zh_note": "中文备注"}]
"""
    content = chat(
        [{"role": "user", "content": prompt}],
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
    )
    data = extract_json(content)
    if not isinstance(data, list):
        raise LLMError("LLM 没有返回标题数组，请重试。")
    titles = []
    for item in data:
        if isinstance(item, dict) and item.get("title"):
            titles.append(
                {
                    "title": str(item.get("title", "")).strip(),
                    "zh_note": str(item.get("zh_note", "")).strip(),
                }
            )
    if not titles:
        raise LLMError("LLM 返回的标题列表为空，请重试。")
    return titles


def generate_article(
    keyword: str,
    language_name: str,
    min_words: int,
    max_words: int,
    custom_instruction: str = "",
    api_key: str = "",
    base_url: str = "",
    model: str = "",
    temperature: float = 0.7,
) -> dict:
    """围绕关键词生成一篇完整文章（HTML 正文 + SEO 元信息）。"""
    prompt = f"""你是资深的多语种 SEO 内容写手。请围绕关键词「{keyword}」写一篇完整的{language_name}文章，用于发布到博客。

要求：
1. 正文用{language_name}撰写，地道自然，避免翻译腔
2. 篇幅约 {min_words}-{max_words} 词（按目标语言的单词/字符数衡量），内容充实、有真实建议，不要空话套话
3. 用 HTML 结构输出：<h2>小标题</h2> 与 <p>段落</p>，适当使用 <h3> 与 <ul><li> 列表
4. 第一段自然地包含关键词「{keyword}」，全文自然分布相关长尾词
5. 不要出现“作为AI”“作为语言模型”等表述"""
    if custom_instruction.strip():
        prompt += f"\n6. 额外定制指令：{custom_instruction.strip()}"
    prompt += """
7. 同时生成用于 SEO 发布的元信息：
   - slug：URL 别名，用目标语言，小写字母+连字符，不含空格和特殊符号
   - meta_title：SEO 标题，长度不超过 60 个字符
   - meta_description：SEO 描述，长度不超过 155 个字符
8. 只输出一个 JSON 对象，不要输出任何其他内容，格式如下：
{"title": "文章标题", "slug": "url-alias", "meta_title": "SEO标题", "meta_description": "SEO描述", "content_html": "<h2>小标题</h2><p>段落内容</p>"}
"""
    content = chat(
        [{"role": "user", "content": prompt}],
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=temperature,
    )
    data = extract_json(content)
    if not isinstance(data, dict):
        raise LLMError("LLM 没有返回文章 JSON 对象，请重试。")
    return {
        "title": str(data.get("title", "")).strip(),
        "slug": str(data.get("slug", "")).strip().lower(),
        "meta_title": str(data.get("meta_title", "")).strip(),
        "meta_description": str(data.get("meta_description", "")).strip(),
        "content_html": str(data.get("content_html", "")).strip(),
    }


def annotate_keywords(
    keywords: list[str],
    api_key: str = "",
    base_url: str = "",
    model: str = "",
) -> dict[str, str]:
    """批量给关键词添加中文备注，返回 {关键词: 中文备注}。"""
    if not keywords:
        return {}
    keyword_list = json.dumps([{"keyword": k} for k in keywords], ensure_ascii=False)
    prompt = (
        "请为以下 SEO 关键词各写一句简短的中文备注（解释词义 + 建议一个内容切入点）。\n"
        f"{keyword_list}\n"
        '只输出 JSON 数组，不要输出其他内容，格式：[{"keyword": "原词", "note": "中文备注"}]'
    )
    content = chat(
        [{"role": "user", "content": prompt}],
        api_key=api_key,
        base_url=base_url,
        model=model,
        temperature=0.3,
    )
    data = extract_json(content)
    notes: dict[str, str] = {}
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("keyword"):
                notes[str(item["keyword"])] = str(item.get("note", "")).strip()
    return notes