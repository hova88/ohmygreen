import "./styles.css";

type Post = {
  id: number;
  title: string;
  body: string;
  created_at: string;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

const form = document.querySelector<HTMLFormElement>("#post-form");
const titleInput = document.querySelector<HTMLInputElement>("#title");
const bodyInput = document.querySelector<HTMLTextAreaElement>("#body");
const publishButton = document.querySelector<HTMLButtonElement>("#publish-btn");
const list = document.querySelector<HTMLUListElement>("#post-list");
const statusText = document.querySelector<HTMLParagraphElement>("#status");
const countText = document.querySelector<HTMLParagraphElement>("#post-count");

const featuredPost = document.querySelector<HTMLElement>("#featured-post");
const featuredTitle = document.querySelector<HTMLHeadingElement>("#featured-title");
const featuredDate = document.querySelector<HTMLParagraphElement>("#featured-date");
const featuredBody = document.querySelector<HTMLDivElement>("#featured-body");

function setStatus(message: string, tone: "info" | "error" = "info"): void {
  if (!statusText) return;
  statusText.textContent = message;
  statusText.dataset.tone = tone;
}

function setSubmitting(isSubmitting: boolean): void {
  if (!publishButton) return;
  publishButton.disabled = isSubmitting;
  publishButton.textContent = isSubmitting ? "Publishing..." : "Publish";
}

function formatDate(value: string): string {
  const date = new Date(value);
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function renderFeatured(post: Post | null): void {
  if (!featuredPost || !featuredTitle || !featuredDate || !featuredBody) return;

  if (!post) {
    featuredPost.classList.add("hidden");
    return;
  }

  featuredTitle.textContent = post.title;
  featuredDate.textContent = formatDate(post.created_at);
  featuredBody.innerHTML = "";

  post.body
    .split("\n")
    .filter((line) => line.trim().length > 0)
    .forEach((line) => {
      const paragraph = document.createElement("p");
      paragraph.textContent = line;
      featuredBody.append(paragraph);
    });

  featuredPost.classList.remove("hidden");
}

async function fetchPosts(): Promise<void> {
  const response = await fetch(`${API_BASE}/posts`);
  if (!response.ok) {
    throw new Error("Unable to load posts.");
  }
  const posts = (await response.json()) as Post[];
  render(posts);
}

function render(posts: Post[]): void {
  if (!list || !countText) return;

  countText.textContent = `${posts.length} total`;
  list.innerHTML = "";

  if (!posts.length) {
    renderFeatured(null);
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.textContent = "No posts yet.";
    list.append(empty);
    return;
  }

  renderFeatured(posts[0]);

  posts.slice(1).forEach((post) => {
    const item = document.createElement("li");
    item.className = "post-item";

    const article = document.createElement("article");
    const heading = document.createElement("h4");
    const time = document.createElement("time");

    heading.textContent = post.title;
    time.dateTime = post.created_at;
    time.textContent = formatDate(post.created_at);

    article.append(heading, time);
    item.append(article);
    list.append(item);
  });

  if (posts.length === 1) {
    const note = document.createElement("li");
    note.className = "empty-state";
    note.textContent = "No older posts yet.";
    list.append(note);
  }
}

form?.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!titleInput || !bodyInput) return;

  setSubmitting(true);
  setStatus("Publishing...");

  try {
    const response = await fetch(`${API_BASE}/posts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: titleInput.value, body: bodyInput.value }),
    });

    if (!response.ok) {
      throw new Error("Unable to publish post.");
    }

    form.reset();
    await fetchPosts();
    setStatus("Published.");
  } catch {
    setStatus("Publish failed. Please retry.", "error");
  } finally {
    setSubmitting(false);
  }
});

void fetchPosts().catch(() => {
  setStatus("Could not load posts.", "error");
});
