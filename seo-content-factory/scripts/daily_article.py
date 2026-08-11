"""每日自动生成一篇文章 → 写入 WordPress 草稿箱。

本地测试：
    pip install -r requirements.txt
    copy .env.example .env    （填入真实密钥）
    python scripts/daily_article.py

GitHub Actions 定时运行（见 .github/workflows/daily.yml）：
    会自动读取仓库 Secrets 作为环境变量，无需 .env。
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from seo_factory import daily, storage


def main() -> None:
    print("=" * 50)
    print("SEO 内容分发工厂 · 每日任务开始")
    print("=" * 50)
    try:
        result = daily.run(verbose=True)
    except Exception as exc:  # noqa: BLE001
        storage.log_event("task", f"每日任务失败：{exc}")
        print(f"\n❌ 每日任务失败：{exc}", file=sys.stderr)
        print("排查建议：检查环境变量 / secrets 是否配置，DataForSEO 余额，WordPress 应用密码等。")
        sys.exit(1)
    print("\n" + "=" * 50)
    print("✅ 每日任务完成")
    print(f"   今日关键词：{result['keyword']}")
    print(f"   文章标题：{result['title']}")
    print(f"   WordPress 草稿编辑链接：{result['edit_link']}")
    print("=" * 50)


if __name__ == "__main__":
    main()