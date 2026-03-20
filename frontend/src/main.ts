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
const clearButton = document.querySelector<HTMLButtonElement>("#clear-btn");
const retryButton = document.querySelector<HTMLButtonElement>("#retry-btn");
const list = document.querySelector<HTMLUListElement>("#post-list");
const statusText = document.querySelector<HTMLParagraphElement>("#status");
const countText = document.querySelector<HTMLParagraphElement>("#post-count");

const featuredPost = document.querySelector<HTMLElement>("#featured-post");
const featuredTitle = document.querySelector<HTMLHeadingElement>("#featured-title");
const featuredDate = document.querySelector<HTMLParagraphElement>("#featured-date");
const featuredBody = document.querySelector<HTMLDivElement>("#featured-body");

function setStatus(message: string, tone: "info" | "success" | "error" = "info"): void {
  if (!statusText) return;
  statusText.textContent = message;
  statusText.dataset.tone = tone;
}

function setSubmitting(isSubmitting: boolean): void {
  if (!publishButton) return;
  publishButton.disabled = isSubmitting;
  publishButton.textContent = isSubmitting ? "Publishing..." : "Publish post";
}

function formatDate(value: string): string {
  const date = new Date(value);
  return new Intl.DateTimeFormat("en", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function excerpt(text: string, limit = 180): string {
  const trimmed = text.replace(/\s+/g, " ").trim();
  if (trimmed.length <= limit) return trimmed;
  return `${trimmed.slice(0, limit).trimEnd()}…`;
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
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, 3)
    .forEach((line) => {
      const paragraph = document.createElement("p");
      paragraph.textContent = line;
      featuredBody.append(paragraph);
    });

  featuredPost.classList.remove("hidden");
}

function render(posts: Post[]): void {
  if (!list || !countText) return;

  countText.textContent = posts.length ? `${posts.length} post${posts.length === 1 ? "" : "s"}` : "No posts yet";
  list.innerHTML = "";

  if (!posts.length) {
    renderFeatured(null);
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.textContent = "Your published posts will appear here.";
    list.append(empty);
    return;
  }

  renderFeatured(posts[0]);

  posts.slice(1).forEach((post) => {
    const item = document.createElement("li");
    item.className = "post-item";

    const heading = document.createElement("h4");
    const summary = document.createElement("p");
    const meta = document.createElement("p");

    heading.textContent = post.title;
    summary.textContent = excerpt(post.body);
    meta.textContent = formatDate(post.created_at);
    meta.className = "post-meta";

    item.append(heading, summary, meta);
    list.append(item);
  });
}

async function fetchPosts(): Promise<void> {
  retryButton?.classList.add("hidden");
  const response = await fetch(`${API_BASE}/posts`);
  if (!response.ok) {
    throw new Error("Unable to load posts.");
  }
  const posts = (await response.json()) as Post[];
  render(posts);
  setStatus(posts.length ? "Posts are up to date." : "Start by publishing your first post.");
}

function validateForm(): string | null {
  const title = titleInput?.value.trim() ?? "";
  const body = bodyInput?.value.trim() ?? "";

  if (title.length < 3) return "Please add a clearer title.";
  if (!body) return "Please write a few lines before publishing.";
  return null;
}

async function handleSubmit(event: SubmitEvent): Promise<void> {
  event.preventDefault();
  if (!form || !titleInput || !bodyInput) return;

  const validationError = validateForm();
  if (validationError) {
    setStatus(validationError, "error");
    return;
  }

  setSubmitting(true);
  setStatus("Publishing your post...");

  try {
    const response = await fetch(`${API_BASE}/posts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: titleInput.value.trim(), body: bodyInput.value.trim() }),
    });

    if (!response.ok) {
      throw new Error("Unable to publish post.");
    }

    form.reset();
    await fetchPosts();
    setStatus("Published. You can keep writing the next one.", "success");
    titleInput.focus();
  } catch {
    setStatus("Publish failed. Check the API and try again.", "error");
  } finally {
    setSubmitting(false);
  }
}

form?.addEventListener("submit", (event) => {
  void handleSubmit(event);
});

clearButton?.addEventListener("click", () => {
  form?.reset();
  setStatus("Draft cleared.");
  titleInput?.focus();
});

retryButton?.addEventListener("click", () => {
  void fetchPosts().catch(() => {
    setStatus("Still unable to load posts. Confirm the API is running.", "error");
    retryButton.classList.remove("hidden");
  });
});

void fetchPosts().catch(() => {
  setStatus("Could not load posts. Confirm the API is running.", "error");
  retryButton?.classList.remove("hidden");
});
