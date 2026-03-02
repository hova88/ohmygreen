# ohmygreen

极简、私有、CLI-first 的 AI 博客系统：**AI + BearBlog 风格 + Terminal Agent Loop**。

## 设计目标
1. **BearBlog 风格**：简洁页面、快速发布、阅读优先。
2. **私有账户**：每个用户只能查看自己的内容。
3. **CLI 优先**：像 codex / claude code 一样，通过终端进入代理循环写作。
4. **多模型 AI**：支持 `openai` 与 `qwen` 两种 provider。

---

## 功能概览
- Web：登录/注册（同入口）、发布文章、仅显示本人时间线。
- API：
  - `POST /api/auth/login` 获取 token
  - `GET /api/posts` 获取本人文章
  - `POST /api/posts` 直接发布文章（Bearer token）
- CLI：`ohmygreen` 进入 agent loop：
  - `plan -> draft -> refine -> save/publish`

---

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
uvicorn app.main:app --reload
```

访问：`http://127.0.0.1:8000`

---

## CLI 使用（核心体验）

```bash
ohmygreen
```

进入交互后会引导：
- Topic / Audience / Tone
- 选择 AI provider（`openai` 或 `qwen`）
- 自动执行 agent loop 并输出草稿
- 可在终端中反复 regenerate / save / publish

### 环境变量

```bash
# OpenAI
export OPENAI_API_KEY=...
export OPENAI_MODEL=gpt-4.1-mini

# Qwen (DashScope compatible endpoint)
export QWEN_API_KEY=...
export QWEN_MODEL=qwen-plus

# optional
export OHMYGREEN_BASE_URL=http://127.0.0.1:8000
```

> 若未配置 AI key，CLI 会自动回退到本地高质量模板草稿。

---

## 架构
- `app/main.py`: FastAPI 路由（Web + API）
- `app/models.py`: `User/Post` ORM 模型
- `app/security.py`: 密码哈希与 token 生成
- `cli/blog_agent.py`: 终端 agent loop 与 API 发布
- `templates/` + `static/`: 极简界面

---

## 下一步优化建议
- 将 session secret 改为环境变量并增强安全配置。
- 为 markdown 增加安全渲染与目录导航。
- 为 agent loop 增加“提纲确认 -> 分段写作 -> 最终审校”。
- 增加端到端测试（CLI publish + Web timeline 验证）。
