import "./styles.css";

type ComicPage = {
  id: number;
  title: string;
  image: string;
  alt: string;
  note: string;
};

type FitMode = "contain" | "width";
type ReadingMode = "spread" | "single";

const pages: ComicPage[] = [
  { id: 1, title: "第 1 页", image: "/demo-pages/page-01.svg", alt: "漫画第一页，主角在雨夜城市奔跑。", note: "雨夜·追逐" },
  { id: 2, title: "第 2 页", image: "/demo-pages/page-02.svg", alt: "漫画第二页，主角停下脚步看向高楼。", note: "停顿·抬头" },
  { id: 3, title: "第 3 页", image: "/demo-pages/page-03.svg", alt: "漫画第三页，空中出现神秘巨大植物。", note: "异象·蔓生" },
  { id: 4, title: "第 4 页", image: "/demo-pages/page-04.svg", alt: "漫画第四页，街道人群抬头震惊。", note: "街道·惊呼" },
  { id: 5, title: "第 5 页", image: "/demo-pages/page-05.svg", alt: "漫画第五页，主角进入温室般的奇异空间。", note: "坠入·温室" },
  { id: 6, title: "第 6 页", image: "/demo-pages/page-06.svg", alt: "漫画第六页，主角触碰发光叶脉。", note: "触碰·脉冲" },
  { id: 7, title: "第 7 页", image: "/demo-pages/page-07.svg", alt: "漫画第七页，空间展开成巨大双页景观。", note: "展开·全景" },
  { id: 8, title: "第 8 页", image: "/demo-pages/page-08.svg", alt: "漫画第八页，主角回到黎明中的城市。", note: "黎明·回响" },
];

const app = document.querySelector<HTMLDivElement>("#app");

if (!app) {
  throw new Error("App root not found");
}

app.innerHTML = `
  <main class="viewer-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">极简漫画分页浏览器</p>
        <h1>只做一件事：把翻页体验做到极致</h1>
      </div>
      <div class="topbar-meta">
        <span class="chip">← → 翻页</span>
        <span class="chip">点击两侧翻页</span>
        <span class="chip">触控滑动翻页</span>
      </div>
    </header>

    <section class="stage-card">
      <div class="stage-toolbar" aria-label="浏览控制栏">
        <button id="prev-btn" class="nav-btn" type="button" aria-label="上一页或上一组">← 上一页</button>
        <div class="toolbar-center">
          <div>
            <p id="spread-label" class="spread-label">第 1 页</p>
            <p id="spread-note" class="spread-note">雨夜·追逐</p>
          </div>
          <div class="toolbar-toggles">
            <button id="mode-btn" class="ghost-btn" type="button" aria-label="切换单页或双页模式">双页模式</button>
            <button id="fit-btn" class="ghost-btn" type="button" aria-label="切换适应模式">适应整页</button>
          </div>
        </div>
        <button id="next-btn" class="nav-btn" type="button" aria-label="下一页或下一组">下一页 →</button>
      </div>

      <div class="viewer-wrap">
        <button id="hit-prev" class="hit-zone hit-prev" type="button" aria-label="点击左侧翻到上一页"></button>
        <section id="viewer" class="viewer" aria-live="polite"></section>
        <button id="hit-next" class="hit-zone hit-next" type="button" aria-label="点击右侧翻到下一页"></button>
      </div>

      <div class="bottom-bar">
        <div class="progress-block">
          <label for="page-range">翻页进度</label>
          <input id="page-range" type="range" min="1" max="8" value="1" step="1" />
        </div>
        <div class="status-block">
          <span id="page-count">1 / 8</span>
          <span id="mode-hint">桌面端自动双页展开</span>
        </div>
      </div>
    </section>

    <section class="thumb-strip" aria-label="页面缩略导航">
      <div id="thumbs" class="thumb-grid"></div>
    </section>
  </main>
`;

const viewer = document.querySelector<HTMLElement>("#viewer");
const prevButton = document.querySelector<HTMLButtonElement>("#prev-btn");
const nextButton = document.querySelector<HTMLButtonElement>("#next-btn");
const hitPrev = document.querySelector<HTMLButtonElement>("#hit-prev");
const hitNext = document.querySelector<HTMLButtonElement>("#hit-next");
const pageRange = document.querySelector<HTMLInputElement>("#page-range");
const spreadLabel = document.querySelector<HTMLParagraphElement>("#spread-label");
const spreadNote = document.querySelector<HTMLParagraphElement>("#spread-note");
const pageCount = document.querySelector<HTMLSpanElement>("#page-count");
const thumbs = document.querySelector<HTMLDivElement>("#thumbs");
const fitButton = document.querySelector<HTMLButtonElement>("#fit-btn");
const modeButton = document.querySelector<HTMLButtonElement>("#mode-btn");
const modeHint = document.querySelector<HTMLSpanElement>("#mode-hint");

let currentPage = 1;
let fitMode: FitMode = "contain";
let readingMode: ReadingMode = window.innerWidth >= 900 ? "spread" : "single";
let touchStartX = 0;
let touchDeltaX = 0;

function spreadStep(): number {
  return readingMode === "spread" ? 2 : 1;
}

function spreadStart(page: number): number {
  if (readingMode === "single") return page;
  return page % 2 === 0 ? page - 1 : page;
}

function clampPage(page: number): number {
  return Math.min(Math.max(page, 1), pages.length);
}

function visiblePages(page: number): ComicPage[] {
  const start = spreadStart(page);
  const first = pages[start - 1];
  const second = readingMode === "spread" ? pages[start] : undefined;
  return [first, second].filter(Boolean) as ComicPage[];
}

function preloadNearby(): void {
  const candidates = [currentPage - 2, currentPage - 1, currentPage + 1, currentPage + 2]
    .map((page) => clampPage(page))
    .filter((page, index, arr) => arr.indexOf(page) === index);

  candidates.forEach((pageNumber) => {
    const img = new Image();
    img.src = pages[pageNumber - 1].image;
  });
}

function updateButtons(): void {
  const atStart = currentPage <= 1;
  const atEnd = currentPage >= pages.length || (readingMode === "spread" && spreadStart(currentPage) >= pages.length - 1);

  [prevButton, hitPrev].forEach((button) => {
    if (!button) return;
    button.disabled = atStart;
  });

  [nextButton, hitNext].forEach((button) => {
    if (!button) return;
    button.disabled = atEnd;
  });
}

function renderThumbs(): void {
  if (!thumbs) return;

  thumbs.innerHTML = "";
  pages.forEach((page) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "thumb";
    button.dataset.page = String(page.id);
    button.setAttribute("aria-label", `跳转到${page.title}`);

    button.innerHTML = `
      <img src="${page.image}" alt="${page.alt}" loading="lazy" />
      <span>${page.id}</span>
    `;

    button.addEventListener("click", () => {
      currentPage = page.id;
      render();
    });

    thumbs.append(button);
  });
}

function syncThumbs(): void {
  document.querySelectorAll<HTMLButtonElement>(".thumb").forEach((thumb) => {
    const page = Number(thumb.dataset.page);
    const visible = visiblePages(currentPage).some((item) => item.id === page);
    thumb.dataset.active = visible ? "true" : "false";
    if (visible) {
      thumb.scrollIntoView({ block: "nearest", inline: "center", behavior: "smooth" });
    }
  });
}

function render(): void {
  if (!viewer || !spreadLabel || !spreadNote || !pageCount || !pageRange || !fitButton || !modeButton || !modeHint) return;

  const current = visiblePages(currentPage);
  const [first, second] = current;

  viewer.dataset.fit = fitMode;
  viewer.dataset.mode = readingMode;
  viewer.innerHTML = current
    .map(
      (page) => `
        <article class="page-card" aria-label="${page.title}">
          <div class="page-meta">
            <span>${page.title}</span>
            <span>${page.note}</span>
          </div>
          <img src="${page.image}" alt="${page.alt}" draggable="false" />
        </article>
      `,
    )
    .join("");

  spreadLabel.textContent = second ? `第 ${first.id} - ${second.id} 页` : `第 ${first.id} 页`;
  spreadNote.textContent = second ? `${first.note} · ${second.note}` : first.note;
  pageCount.textContent = `${currentPage} / ${pages.length}`;
  pageRange.value = String(currentPage);
  fitButton.textContent = fitMode === "contain" ? "适应整页" : "适应宽度";
  modeButton.textContent = readingMode === "spread" ? "双页模式" : "单页模式";
  modeHint.textContent = readingMode === "spread" ? "当前为沉浸式双页展开" : "当前为专注单页阅读";

  updateButtons();
  syncThumbs();
  preloadNearby();
}

function turnPage(direction: 1 | -1): void {
  const next = clampPage(currentPage + direction * spreadStep());
  if (next === currentPage) return;
  currentPage = next;
  render();
}

prevButton?.addEventListener("click", () => turnPage(-1));
nextButton?.addEventListener("click", () => turnPage(1));
hitPrev?.addEventListener("click", () => turnPage(-1));
hitNext?.addEventListener("click", () => turnPage(1));

pageRange?.addEventListener("input", (event) => {
  const target = event.target as HTMLInputElement;
  currentPage = Number(target.value);
  render();
});

fitButton?.addEventListener("click", () => {
  fitMode = fitMode === "contain" ? "width" : "contain";
  render();
});

modeButton?.addEventListener("click", () => {
  readingMode = readingMode === "spread" ? "single" : "spread";
  currentPage = spreadStart(currentPage);
  render();
});

window.addEventListener("keydown", (event) => {
  if (["ArrowLeft", "a", "A"].includes(event.key)) {
    turnPage(-1);
  }
  if (["ArrowRight", "d", "D", " "].includes(event.key)) {
    turnPage(1);
  }
  if (event.key.toLowerCase() === "f") {
    fitMode = fitMode === "contain" ? "width" : "contain";
    render();
  }
});

viewer?.addEventListener("touchstart", (event) => {
  touchStartX = event.touches[0]?.clientX ?? 0;
  touchDeltaX = 0;
}, { passive: true });

viewer?.addEventListener("touchmove", (event) => {
  touchDeltaX = (event.touches[0]?.clientX ?? 0) - touchStartX;
}, { passive: true });

viewer?.addEventListener("touchend", () => {
  if (touchDeltaX <= -60) turnPage(1);
  if (touchDeltaX >= 60) turnPage(-1);
});

window.addEventListener("resize", () => {
  const nextMode: ReadingMode = window.innerWidth >= 900 ? readingMode : "single";
  if (window.innerWidth < 900 && readingMode !== nextMode) {
    readingMode = nextMode;
    render();
  }
});

renderThumbs();
render();
