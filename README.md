# ohmygreen

一个极简的 AI Power 私人博客 Demo（风格接近 BearBlog），重点是 **CLI + AI 写作体验**。

## 当前能力（MVP Demo）
- 极简网页：登录（用户名即私有空间）+ 发帖 + 时间线
- 数据隔离：每个用户名只看到自己的帖子
- CLI Agent Loop：`生成草稿 -> 简单自我修订 -> 输出 markdown`
- 可逐步优化为 Codex/Claude Code 风格的写作闭环

## 快速开始
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

打开 `http://127.0.0.1:8000`。

## CLI + AI 写作
```bash
python -m cli.blog_agent run "今天如何用AI提升写作效率"
```
输出文件默认在 `drafts/latest.md`，复制到网页中发布。

> 若设置 `OPENAI_API_KEY`，CLI 会调用 OpenAI Responses API；否则使用本地 fallback 模板草稿。

## 发布建议（本 repo 内）
1. 先以 SQLite + 单实例部署（Render/Fly.io/Railway 均可）
2. 增加真实鉴权（session/cookie + password）
3. 增加“CLI 直发 API”（从终端直接发布）
4. 增加 agent loop（多轮计划、编辑、回看）
5. 增加全文检索、标签、版本历史

## 下一轮优化方向
- 将 `user` query 参数迁移到安全 session
- 增加 Markdown 渲染与 XSS 过滤
- 增加 `/api/posts` 供 CLI 直接调用
- 增加提示词模板库（标题、摘要、SEO、周报）
