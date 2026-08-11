# 🚀 SEO 内容分发工厂

一套给 SEO 从业者用的**多语种智能内容自动化系统**：

- 🔍 关键词调研：接入 [DataForSEO](https://app.dataforseo.com/) 获取**真实搜索量 / 竞争度 / CPC**
- ✍️ 文章工厂：大模型（LLM）按目标语言自动生成**标题候选 + 正文 + SEO 元信息**
- 📤 自动分发：一键把文章写入 **WordPress 草稿箱**（不会自动公开，你审核后再发布）
- ⏰ 每日任务：GitHub Actions 定时，**每天自动生成一篇草稿**到 WordPress，你早上审核、点发布即可

---

## 目录

1. [整体架构](#整体架构)
2. [费用说明](#费用说明)
3. [你需要准备的材料](#你需要准备的材料)
4. [第 1 步：注册账号、拿到密钥](#第-1-步注册账号拿到密钥)
5. [第 2 步：把代码传到 GitHub](#第-2-步把代码传到-github)
6. [第 3 步：部署到 Streamlit Cloud](#第-3-步部署到-streamlit-cloud)
7. [第 4 步：在 Streamlit 里配置密钥（Secrets）](#第-4-步在-streamlit-里配置密钥secrets)
8. [第 5 步：网页里怎么用（6 个页面）](#第-5-步网页里怎么用6-个页面)
9. [第 6 步：配置每日自动任务](#第-6-步配置每日自动任务)
10. [第 7 步：每天的工作流](#第-7-步每天的工作流)
11. [本地运行（可选，用于测试）](#本地运行可选用于测试)
12. [常见问题 FAQ](#常见问题-faq)
13. [安全提醒](#安全提醒)
14. [后续扩展方向](#后续扩展方向)

---

## 整体架构

```
┌─────────────┐    ┌──────────────────────┐    ┌──────────────────┐
│  你（浏览器） │───▶│  Streamlit Cloud     │───▶│  WordPress       │
│  访问网页工具 │    │  （6 个页面）         │    │  （草稿箱）       │
└─────────────┘    └──────────┬───────────┘    └──────────────────┘
                              │
                 ┌────────────┼────────────┐
                 ▼            ▼            ▼
           DataForSEO    LLM 大模型     GitHub Actions
           （搜索量）    （写标题正文）  （每天定时自动跑）
```

**数据流（写一篇文章）：**
`选词 → DataForSEO 查搜索量 → LLM 生成标题候选 → 你锁定标题 → LLM 生成正文 → 写入 WP 草稿箱 → 你审核 → 发布`

**每日自动任务（无需打开网页）：**
`GitHub Actions 定时触发 → 读取 config/daily_plan.json 和仓库 Secrets → 同样的流程 → 生成一篇草稿 → 你早上在 WP 后台审核发布`

---

## 费用说明

| 项目 | 费用 | 说明 |
|---|---|---|
| GitHub | 免费 | 代码仓库 + 定时任务（Actions 免费额度足够每天跑一次） |
| Streamlit Cloud | 免费 | 应用托管，免费版足够个人使用 |
| DataForSEO | 按次计费（美元） | 每次关键词调研只花几美分，先充 $10–20 测试 |
| LLM（大模型） | 按 token 计费 | 用 DeepSeek / Kimi 等国产接口很便宜，一篇 1000 词文章约几毛钱人民币 |
| WordPress | 你已有 | 需要开启 REST API 和「应用程序密码」 |

> ⚠️ DataForSEO 是**付费商业 API**，不是开源软件。充值入口在它的控制台，按量扣费，建议先小额测试。

---

## 你需要准备的材料

| # | 材料 | 去哪弄 |
|---|---|---|
| 1 | GitHub 账号 | https://github.com 免费注册 |
| 2 | Streamlit 账号 | https://streamlit.io 用 GitHub 账号登录 |
| 3 | DataForSEO 账号 + API 凭证 | https://app.dataforseo.com/ |
| 4 | LLM API Key | OpenAI / DeepSeek / Kimi 任选一个 |
| 5 | WordPress 站点 + 应用程序密码 | 你的 WP 后台 |

---

## 第 1 步：注册账号、拿到密钥

### 1.1 GitHub（用来存代码）
1. 打开 https://github.com → Sign up → 用邮箱注册（免费）
2. 记住你的用户名和邮箱

### 1.2 DataForSEO（关键词搜索量数据）
1. 打开 https://app.dataforseo.com/ → Sign up 注册
2. 登录后，点击右上角头像 → **API Access**（或 My Account）
3. 页面会显示两个值：
   - **API Login**（通常是你的注册邮箱）
   - **API Password**（一串密钥，类似 `xxxx-xxxx-xxxx`）
4. 充值少量余额（$10–20），用于测试关键词调研接口
   - 注意：新账号有时会给试用积分，以官网实际为准

### 1.3 LLM 大模型（生成标题和正文）
任选一个（都兼容本工具），推荐先试 **DeepSeek**（便宜、国内直连）：

- **DeepSeek**：https://platform.deepseek.com → API Keys → 创建 Key
  - 接口地址（Base URL）：`https://api.deepseek.com/v1`
  - 模型名：`deepseek-chat`
- **OpenAI**：https://platform.openai.com → API keys → 创建 Key
  - Base URL：`https://api.openai.com/v1`
  - 模型名：`gpt-4o-mini`
- **Kimi（Moonshot）**：https://platform.moonshot.cn → API Keys
  - Base URL：`https://api.moonshot.cn/v1`，模型名：`moonshot-v1-8k`
- **通义千问**：https://dashscope.aliyun.com → API-KEY 管理
  - Base URL：`https://dashscope.aliyuncs.com/compatible-mode/v1`，模型名：`qwen-plus`

### 1.4 WordPress（你的草稿箱）
1. 登录 WordPress 后台
2. 确认固定链接设置不是纯数字：**设置 → 固定链接** → 选「文章名」或其他含字母的格式（REST API 必需）
3. 创建「应用程序密码」：
   - **用户 → 个人资料** → 拉到最底部 **应用程序密码**
   - 起个名字（如 `seo-tool`）→ 点「添加新应用程序密码」
   - 复制生成的一串密码（**只显示一次**，格式类似 `xxxx xxxx xxxx xxxx xxxx xxxx`）
4. 记下：站点地址（如 `https://你的域名.com`）、你的用户名、上面的应用程序密码

> 💡 如果创建草稿时报 401/404，多半是：用户名/密码不对、固定链接是纯数字、或主机商禁用了 REST API。

---

## 第 2 步：把代码传到 GitHub

### 方式 A：网页上传（新手最推荐，不用装软件）
1. 登录 GitHub → 点右上角 **+** → **New repository**
2. Repository name 填：`seo-content-factory`，选 **Public**（私有也可以，免费版 Actions 配额少一些）→ 点 **Create repository**
3. 在新页面点 **uploading an existing file**
4. 把整个项目文件夹（`seo-content-factory` 里面的所有文件和文件夹）**拖进去**
   - 注意：要把 **里面的内容** 全部传上去，包括 `app.py`、`seo_factory` 文件夹、`.github` 文件夹等
5. 点 **Commit changes** 完成上传

> ⚠️ 上传时**不要**传 `.streamlit/secrets.toml`（本仓库没有这个文件，因为密钥不能进仓库）。`.gitignore` 已自动忽略 `.env` 和 `data/`。

### 方式 B：Git 命令（进阶，可选）
```bash
git clone https://github.com/你的用户名/seo-content-factory.git
# 把项目文件复制进去后：
git add .
git commit -m "初始化 SEO 内容分发工厂"
git push
```

---

## 第 3 步：部署到 Streamlit Cloud

1. 打开 https://streamlit.io → 点 **Sign in** → 用 **GitHub** 登录
2. 登录后点 **Create app**（或 New app）
3. 按提示选择：
   - **Repository**：`你的用户名/seo-content-factory`
   - **Branch**：`main`
   - **Main file path**：`app.py`
4. 点 **Deploy**，等 1-3 分钟
5. 部署成功后你会得到一个网址，如 `https://seo-content-factory-xxxx.streamlit.app`

> 💡 免费版应用闲置一会儿会“休眠”，下次打开会等十几秒启动，属正常现象。

---

## 第 4 步：在 Streamlit 里配置密钥（Secrets）

1. 打开你的应用网址
2. 点页面右上角 **⋮（三点菜单）→ Settings → Secrets**
3. 粘贴以下内容（把 `xxx` 换成你的真实值），点 **Save**：

```toml
# ===== DataForSEO =====
DATAFORSEO_LOGIN = "你的 DataForSEO API Login（邮箱）"
DATAFORSEO_PASSWORD = "你的 DataForSEO API Password"

# ===== 大模型 LLM =====
LLM_API_KEY = "你的 LLM API Key"
LLM_BASE_URL = "https://api.deepseek.com/v1"
LLM_MODEL = "deepseek-chat"

# ===== WordPress =====
WP_URL = "https://你的域名.com"
WP_USERNAME = "你的 WP 用户名"
WP_APP_PASSWORD = "你的 WP 应用程序密码"
```

4. 保存后，回到应用 → **⚙️ 设置** 页，三个区块应该都显示 ✅
5. 也可以点「测试 WordPress 连接」和「检查账户余额」验证

> 应用里的「保存到本次会话」只是临时测试用，重启会失效；**真正永久生效的是这里的 Secrets**。

---

## 第 5 步：网页里怎么用（6 个页面）

### 📊 概览
- 看配置是否齐全、本工具的累计统计、最近动态

### 🔍 关键词调研
1. 选择目标市场（如「德国 (Deutsch)」）
2. 输入种子关键词（每行一个，如 `Geschenkideen`）
3. 点「🚀 获取真实搜索量」→ 看到搜索量 / 竞争度 / CPC / 搜索意图
4. 点「✨ AI 生成中文备注」→ 每个词多一行中文解释
5. 勾选想写的词 → 「加入写作计划」

### ✍️ 文章工厂
1. 选词（从写作计划，或手动输入）
2. 设定字数（如 900-1100 词）+ 定制指令（语气、角度等）
3. 点「生成标题候选」→ 看到 5 个外文标题 + 中文备注 → 选中一个（勾选“选用纯外文标题”）
4. 点「锁定标题并生成正文」→ 预览文章和 SEO 元信息（标题/别名/描述）
5. 满意后点「发送到 WordPress 草稿箱」→ 得到编辑链接

### 📤 分发管理
- 刷新查看 WordPress 里的草稿列表，点链接去后台编辑
- 查看本工具写入过的记录

### ⏰ 每日任务
- 查看自动化的原理和当前计划
- 「立即执行今日任务」= 在网页里手动跑一遍完整流程（用于测试）

### ⚙️ 设置
- 填写/检查三个平台的密钥（DataForSEO / LLM / WordPress）
- 下载 `secrets.toml` 模板

---

## 第 6 步：配置每日自动任务

**原理**：Streamlit 免费版不能定时运行，所以“每天自动生成”由 **GitHub Actions** 完成——每天到点后在 GitHub 云端运行一次脚本，把草稿写进你的 WordPress。

### 6.1 准备每日计划文件
1. 在 GitHub 仓库网页上打开 `config/daily_plan.example.json` → 点铅笔 ✏️ 编辑
2. 把 `keywords` 改成你的主题词（列表越长，每天轮换越多样），语言、字数、定制指令也可以改
3. 点 **Commit changes** 保存（文件名改成 `daily_plan.json`）
   - 也可以直接在本地改好后推上去

### 6.2 添加 GitHub 仓库 Secrets（密钥）
1. 打开你的 GitHub 仓库 → **Settings → Secrets and variables → Actions**
2. 点 **New repository secret**，逐个添加下面 8 个（名字要一模一样）：

| Secret 名字 | 填什么 |
|---|---|
| `DATAFORSEO_LOGIN` | DataForSEO API Login |
| `DATAFORSEO_PASSWORD` | DataForSEO API Password |
| `LLM_API_KEY` | LLM API Key |
| `LLM_BASE_URL` | 如 `https://api.deepseek.com/v1` |
| `LLM_MODEL` | 如 `deepseek-chat` |
| `WP_URL` | WordPress 站点地址 |
| `WP_USERNAME` | WordPress 用户名 |
| `WP_APP_PASSWORD` | WordPress 应用程序密码 |

> 密钥会加密保存在 GitHub，别人看不到，也不会出现在代码里。

### 6.3 测试一次
1. 打开仓库 → **Actions** 标签页 → 左侧 **Daily SEO Article**
2. 点 **Run workflow** → 绿色 **Run workflow** 按钮
3. 等 1-3 分钟，看到 ✅ 绿色对勾 = 成功
4. 去 WordPress 后台 → 文章 → 草稿，就能看到新文章

### 6.4 调整时间（可选）
默认每天 **UTC 02:00 ≈ 北京时间 10:00** 执行。
想改时间：编辑 `.github/workflows/daily.yml` 里的 `cron`，例如
- `0 1 * * *` = 北京时间 09:00
- `0 22 * * *` = 北京时间 06:00（第二天）

> 北京时间 = UTC + 8（夏令时部分国家有差异）。

---

## 第 7 步：每天的工作流

1. 早上打开 WordPress 后台 → **文章 → 草稿**
2. 逐篇检查：标题、内容质量、排版、图片、链接
3. 确认没问题 → 点 **发布**
4. 不满意就修改后发布，或删除草稿
5. （可选）每周在工具里看「概览」统计，或用 DataForSEO 复查排名

> 工具永远只写「草稿」状态，**不会自动公开**，主动权始终在你手里。

---

## 本地运行（可选，用于测试）

想在自己电脑上先试试（不需要，但有助于理解）：

1. 安装 Python 3.10+：https://www.python.org/downloads/ （安装时勾选 Add to PATH）
2. 打开命令行（Windows 按 `Win+R` 输入 `cmd`）：
```bash
cd 项目文件夹路径
pip install -r requirements.txt
copy .env.example .env
```
3. 编辑 `.env`，填入真实密钥
4. 启动网页版：`streamlit run app.py`，浏览器会自动打开 `http://localhost:8501`
5. 测试每日脚本：`python scripts/daily_article.py`

---

## 常见问题 FAQ

**Q1：DataForSEO 报“余额不足 / 402”**
→ 去 https://app.dataforseo.com/ 充值后再试。关键词调研按次计费，很便宜。

**Q2：DataForSEO 报“认证失败 / 401”**
→ API Login / Password 填错了。登录 DataForSEO 控制台 → API Access 重新核对。

**Q3：WordPress 创建草稿失败（401/403/404）**
→ 检查：用户名/应用程序密码是否复制完整（含空格没关系）；固定链接是否为“文章名”格式；主机是否禁用了 REST API（可问主机商）。

**Q4：文章字数总是偏多/偏少**
→ LLM 对“字数”只是近似控制。可以把「期望字数」改成更精确的范围，或在定制指令里强调“正文正文部分不少于 X 词，不含标题和列表”。

**Q5：标题里出现中文/翻译腔**
→ 生成标题时勾选「选用纯外文标题」；生成正文的定制指令里写“禁止出现任何中文”。

**Q6：生成的德语/西语等质量一般**
→ 在定制指令里补充：语气、目标人群、参考品牌、要避免的套话；也可以换更强的大模型（如 gpt-4o）。

**Q7：GitHub Actions 每天只生成固定关键词怎么办**
→ 每天会按日期自动轮换 `keywords` 列表里的词；如果开了 `research_expand`，还会用 DataForSEO 挑搜索量高的相关词。

**Q8：Streamlit 应用打不开/很慢**
→ 免费版闲置会休眠，刷新等 10-30 秒即可。

**Q9：我的站点是小语种（德语等），DataForSEO 支持吗**
→ 支持。DataForSEO 覆盖全球市场，本工具内置了德国、美国、法国、西班牙、日本等 15 个常用市场（可在 `seo_factory/config.py` 的 `MARKETS` 里增删）。

---

## 安全提醒

- **永远不要把 API 密钥写进代码或提交到仓库**。密钥只放 Streamlit Secrets 和 GitHub Secrets
- `.env`、`.streamlit/secrets.toml` 已被 `.gitignore` 忽略，确认它们不会出现在 GitHub 仓库里
- 给 WordPress 的应用程序密码起名时标注用途（如 `seo-tool`），不用时可以在后台一键删除
- 定期检查 DataForSEO 余额和 LLM 消费，防止被盗刷（API Key 不要外传）

---

## 后续扩展方向

对照你截图里的完整看板，这套工具未来可以加：

- **站点明细 / 月度对比**：接入 Google Search Console API 拉真实收录与点击数据
- **AI 来源监控**：接入 Google Analytics / Search Console 统计 AI 搜索引擎带来的流量
- **需求管理**：加一个「写作计划表」，管理关键词池、优先级、任务状态
- **事件记录**：把活动记录升级为带筛选/导出的正式事件日志
- **转化监控**：接入 Shopify / WooCommerce 订单数据，看文章带来的加购与转化
- **多站点分发**：支持一次分发到多个 WordPress 站点

有需要随时在本仓库基础上加功能。

---

*祝发布顺利！有技术问题可以先看 FAQ，或者在部署时报错信息发给我，我帮你排查。*