from app.infra.repositories import PostRepository
from app.models import Post


class PostService:
    def __init__(self, post_repo: PostRepository):
        self.post_repo = post_repo

    def list_posts(self, owner_id: int) -> list[Post]:
        return self.post_repo.list_by_owner(owner_id)

    def create_post(self, owner_id: int, title: str, content: str) -> Post:
        return self.post_repo.create(owner_id=owner_id, title=title.strip(), content=content.strip())
