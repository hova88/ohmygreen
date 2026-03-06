from pathlib import Path

from blog.markdown_engine import MarkdownEngine


def test_markdown_frontmatter_parse(tmp_path: Path):
    post_file = tmp_path / "post.md"
    post_file.write_text(
        "---\ntitle: Sample\ndate: 2026-01-02\nslug: sample\ntags: [one]\n---\n\n# Hello",
        encoding="utf-8",
    )
    post = MarkdownEngine().load_posts(tmp_path)[0]
    assert post.title == "Sample"
    assert "<h1" in post.body_html
