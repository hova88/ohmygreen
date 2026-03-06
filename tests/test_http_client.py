from blog.utils import slugify


def test_slugify_basic():
    assert slugify("My First Post") == "my-first-post"
