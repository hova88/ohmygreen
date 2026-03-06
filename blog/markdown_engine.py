from __future__ import annotations

from datetime import datetime
from pathlib import Path

import markdown
import yaml

from .models import Post
from .utils import slugify


class MarkdownEngine:
    def __init__(self) -> None:
        self._renderer = markdown.Markdown(
            extensions=["fenced_code", "tables", "codehilite", "toc"],
            output_format="html5",
        )

    def load_posts(self, posts_dir: Path) -> list[Post]:
        posts: list[Post] = []
        for path in sorted(posts_dir.glob("*.md")):
            posts.append(self._parse_post(path))
        return sorted(posts, key=lambda post: post.date, reverse=True)

    def _parse_post(self, path: Path) -> Post:
        text = path.read_text(encoding="utf-8")
        metadata, body = self._split_frontmatter(text)
        title = metadata.get("title") or path.stem.replace("-", " ").title()
        date_raw = metadata.get("date") or datetime.now().strftime("%Y-%m-%d")
        date = datetime.fromisoformat(str(date_raw))
        slug = metadata.get("slug") or slugify(title)
        tags = metadata.get("tags") or []

        self._renderer.reset()
        body_html = self._renderer.convert(body)

        return Post(
            title=title,
            slug=slug,
            date=date,
            tags=[str(tag) for tag in tags],
            body_markdown=body,
            body_html=body_html,
            source_path=path,
        )

    @staticmethod
    def _split_frontmatter(text: str) -> tuple[dict, str]:
        if not text.startswith("---"):
            return {}, text
        _, fm, body = text.split("---", 2)
        metadata = yaml.safe_load(fm.strip()) or {}
        return metadata, body.strip()
