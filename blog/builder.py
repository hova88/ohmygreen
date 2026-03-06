from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import BlogConfig
from .markdown_engine import MarkdownEngine


class BlogBuilder:
    def __init__(self, config: BlogConfig | None = None) -> None:
        self.config = config or BlogConfig()
        self.markdown = MarkdownEngine()
        self.env = Environment(
            loader=FileSystemLoader(self.config.templates_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    def build(self) -> None:
        posts = self.markdown.load_posts(self.config.posts_dir)
        self._prepare_dist()
        self._render("index.html", self.config.dist_dir / "index.html", posts=posts[:5], page_title="Home")
        self._render("blog-index.html", self.config.dist_dir / "blog" / "index.html", posts=posts, page_title="Blog")
        for post in posts:
            self._render(
                "post.html",
                self.config.dist_dir / post.output_path,
                post=post,
                page_title=post.title,
            )
        self._render("404.html", self.config.dist_dir / "404.html", page_title="Not found")
        self._write_rss(posts)
        self._write_sitemap(posts)

    def _prepare_dist(self) -> None:
        if self.config.dist_dir.exists():
            shutil.rmtree(self.config.dist_dir)
        self.config.dist_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(self.config.static_dir, self.config.dist_dir / "static")

    def _render(self, template_name: str, destination: Path, **context: object) -> None:
        template = self.env.get_template(template_name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            template.render(site=self.config, now=datetime.now(timezone.utc), **context),
            encoding="utf-8",
        )

    def _write_rss(self, posts: list) -> None:
        self._render("rss.xml", self.config.dist_dir / "rss.xml", posts=posts)

    def _write_sitemap(self, posts: list) -> None:
        self._render("sitemap.xml", self.config.dist_dir / "sitemap.xml", posts=posts)
