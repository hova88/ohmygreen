from blog.builder import BlogBuilder


def test_build_creates_pages(tmp_path):
    posts = tmp_path / "posts"
    templates = tmp_path / "templates"
    static = tmp_path / "static"
    dist = tmp_path / "dist"

    posts.mkdir()
    templates.mkdir(parents=True)
    static.mkdir()

    (posts / "hello.md").write_text(
        "---\ntitle: Hello\ndate: 2026-01-01\nslug: hello\ntags: [x]\n---\n\nHi",
        encoding="utf-8",
    )
    (templates / "index.html").write_text("{{ posts|length }}", encoding="utf-8")
    (templates / "blog-index.html").write_text("blog", encoding="utf-8")
    (templates / "post.html").write_text("{{ post.title }}", encoding="utf-8")
    (templates / "404.html").write_text("404", encoding="utf-8")
    (templates / "rss.xml").write_text("rss", encoding="utf-8")
    (templates / "sitemap.xml").write_text("site", encoding="utf-8")
    (static / "style.css").write_text("body{}", encoding="utf-8")

    from blog.config import BlogConfig

    builder = BlogBuilder(
        BlogConfig(
            posts_dir=posts,
            templates_dir=templates,
            static_dir=static,
            dist_dir=dist,
        )
    )
    builder.build()

    assert (dist / "index.html").exists()
    assert (dist / "blog" / "hello" / "index.html").exists()
    assert (dist / "rss.xml").exists()
