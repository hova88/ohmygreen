from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BlogConfig:
    site_name: str = "ohmygreen"
    site_url: str = "https://example.com"
    author: str = "Engineering"
    description: str = "Minimal technical writing about systems and software."
    posts_dir: Path = Path("posts")
    templates_dir: Path = Path("frontend/templates")
    static_dir: Path = Path("frontend/static")
    dist_dir: Path = Path("dist")
