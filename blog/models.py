from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Post:
    title: str
    slug: str
    date: datetime
    tags: list[str]
    body_markdown: str
    body_html: str
    source_path: Path

    @property
    def output_path(self) -> Path:
        return Path("blog") / self.slug / "index.html"
