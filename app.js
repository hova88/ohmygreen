(() => {
  const CONFIG = {
    seriesName: "Berserk",
    dataRoot: "data/berserk",
    manifestFile: "chapters.json",
    imageExtensions: [".jpg", ".jpeg", ".png", ".webp", ".avif"],
    preloadAhead: 8
  };

  const els = {
    pages: document.getElementById("pages"),
    seriesName: document.getElementById("series-name"),
    readerStatus: document.getElementById("reader-status"),
    chapterMeta: document.getElementById("chapter-meta"),
    currentChapterLabel: document.getElementById("current-chapter-label"),
    currentChapterTitle: document.getElementById("current-chapter-title"),
    currentPageCount: document.getElementById("current-page-count"),
    totalChapters: document.getElementById("total-chapters"),
    totalPages: document.getElementById("total-pages"),
    chapterList: document.getElementById("chapter-list"),
    chapterSelect: document.getElementById("chapter-select"),
    prevBtn: document.getElementById("prev-btn"),
    nextBtn: document.getElementById("next-btn"),
    zoomOutBtn: document.getElementById("zoom-out-btn"),
    zoomInBtn: document.getElementById("zoom-in-btn"),
    zoomIndicator: document.getElementById("zoom-indicator")
  };

  const state = {
    chapters: [],
    currentIndex: 0,
    imageCache: new Map(),
    io: null,
    preloadCache: new Map(),
    currentPageUrls: [],
    zoom: 1,
    totalPages: null
  };

  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
  const ZOOM = {
    min: 0.5,
    max: 1.8,
    step: 0.1
  };

  function byName(a, b) {
    return collator.compare(a, b);
  }

  function isImageFile(name) {
    const lower = name.toLowerCase();
    return CONFIG.imageExtensions.some((ext) => lower.endsWith(ext));
  }

  function parseIndexLinks(htmlText) {
    const doc = new DOMParser().parseFromString(htmlText, "text/html");
    return [...doc.querySelectorAll("a")]
      .map((a) => a.getAttribute("href") || "")
      .filter(Boolean)
      .filter((href) => href !== "../")
      .map((href) => decodeURIComponent(href));
  }

  async function fetchAutoIndexList(url) {
    const response = await fetch(url, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`Failed to read index: ${url} (${response.status})`);
    }

    return parseIndexLinks(await response.text());
  }

  async function loadManifest() {
    const url = `${CONFIG.dataRoot}/${CONFIG.manifestFile}`;

    try {
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) throw new Error("no manifest");
      const json = await response.json();
      const chapters = (json.chapters || []).map((item, index) => {
        const folder = typeof item === "string" ? item : item.folder;
        return {
          id: folder,
          title: (item.title || folder || `Chapter ${index + 1}`).replace(/\/$/, "")
        };
      });

      if (!chapters.length) throw new Error("empty chapters");
      CONFIG.seriesName = json.series || CONFIG.seriesName;
      return chapters;
    } catch (_error) {
      const links = await fetchAutoIndexList(`${CONFIG.dataRoot}/`);
      const chapterFolders = links.filter((name) => name.endsWith("/"));
      const chapters = chapterFolders.map((name) => {
        const id = name.replace(/\/$/, "");
        return { id, title: id.replaceAll("_", " ") };
      });

      if (!chapters.length) {
        throw new Error("No chapters found. Add chapters.json or enable directory listing.");
      }

      return chapters.sort((a, b) => byName(a.id, b.id));
    }
  }

  async function listImagesForChapter(chapterId) {
    if (state.imageCache.has(chapterId)) return state.imageCache.get(chapterId);

    const chapterPath = `${CONFIG.dataRoot}/${chapterId}/`;
    const links = await fetchAutoIndexList(chapterPath);
    const files = links
      .filter((name) => !name.endsWith("/"))
      .filter(isImageFile)
      .sort(byName);

    state.imageCache.set(chapterId, files);
    return files;
  }

  async function warmTotalPages() {
    if (typeof state.totalPages === "number") return state.totalPages;

    const lists = await Promise.all(state.chapters.map((chapter) => listImagesForChapter(chapter.id)));
    state.totalPages = lists.reduce((total, files) => total + files.length, 0);
    return state.totalPages;
  }

  function updateQuery(chapterId) {
    const url = new URL(window.location.href);
    url.searchParams.set("chapter", chapterId);
    window.history.replaceState({}, "", url);
  }

  function updateHeader(imageCount) {
    const chapter = state.chapters[state.currentIndex];
    const currentNo = `${String(state.currentIndex + 1).padStart(2, "0")}/${String(
      state.chapters.length
    ).padStart(2, "0")}`;

    els.seriesName.textContent = CONFIG.seriesName;
    els.chapterMeta.textContent = currentNo;
    els.currentChapterLabel.textContent = `${chapter.id}`;
    els.currentChapterTitle.textContent = `${chapter.title}`;
    els.currentPageCount.textContent = String(imageCount);
    els.readerStatus.textContent = `${chapter.id} · ${imageCount} pages`;
    els.chapterSelect.value = chapter.id;
    els.prevBtn.disabled = state.currentIndex === 0;
    els.nextBtn.disabled = state.currentIndex === state.chapters.length - 1;
  }

  function renderChapterOptions() {
    els.chapterSelect.innerHTML = "";

    state.chapters.forEach((chapter, index) => {
      const option = document.createElement("option");
      option.value = chapter.id;
      option.textContent = `${String(index + 1).padStart(2, "0")} · ${chapter.title}`;
      els.chapterSelect.appendChild(option);
    });
  }

  function renderChapterList() {
    els.chapterList.innerHTML = "";

    state.chapters.forEach((chapter, index) => {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      button.className = "chapter-item";
      button.dataset.index = String(index);
      button.innerHTML = `${String(index + 1).padStart(2, "0")} · ${chapter.title}<small>${chapter.id}</small>`;

      button.addEventListener("click", () => {
        openChapter(index);
      });

      li.appendChild(button);
      els.chapterList.appendChild(li);
    });
  }

  function highlightCurrentChapter() {
    [...els.chapterList.querySelectorAll(".chapter-item")].forEach((node) => {
      const active = Number(node.dataset.index) === state.currentIndex;
      node.classList.toggle("active", active);
    });
  }

  function preloadImage(url) {
    if (state.preloadCache.has(url)) return state.preloadCache.get(url);

    const task = new Promise((resolve) => {
      const img = new Image();
      img.decoding = "async";
      img.loading = "eager";
      img.src = url;

      const done = () => resolve(url);
      img.addEventListener("load", done, { once: true });
      img.addEventListener("error", done, { once: true });
    });

    state.preloadCache.set(url, task);
    return task;
  }

  function queueAhead(startIndex) {
    const begin = clamp(startIndex, 0, state.currentPageUrls.length);
    const end = Math.min(begin + CONFIG.preloadAhead, state.currentPageUrls.length);

    for (let idx = begin; idx < end; idx += 1) {
      preloadImage(state.currentPageUrls[idx]);
    }
  }

  function ensureIO() {
    if (state.io) state.io.disconnect();

    state.io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const article = entry.target;
          const img = article.querySelector("img[data-src]");
          if (!img) return;

          const currentIndex = Number(article.dataset.index || 0);
          queueAhead(currentIndex);

          img.src = img.dataset.src;
          img.removeAttribute("data-src");
          state.io.unobserve(article);
        });
      },
      { rootMargin: "1300px 0px" }
    );
  }

  function updateZoomLayout() {
    const viewportWidth = window.innerWidth;
    const usableWidth = viewportWidth >= 1040 ? viewportWidth - 360 : viewportWidth - 40;
    const baseTileWidth = 520;
    const targetTileWidth = baseTileWidth * state.zoom;
    const columns = Math.max(1, Math.floor(usableWidth / targetTileWidth));
    const zoomPercent = Math.round(state.zoom * 100);

    document.documentElement.style.setProperty("--columns", String(columns));
    els.zoomIndicator.textContent = `${zoomPercent}%`;
    els.zoomOutBtn.disabled = state.zoom <= ZOOM.min;
    els.zoomInBtn.disabled = state.zoom >= ZOOM.max;
  }

  function setZoom(nextZoom) {
    const normalized = clamp(Number(nextZoom.toFixed(2)), ZOOM.min, ZOOM.max);
    if (normalized === state.zoom) return;
    state.zoom = normalized;
    updateZoomLayout();
  }

  function bumpZoom(delta) {
    setZoom(state.zoom + delta);
  }

  function buildPageNode(url, index) {
    const article = document.createElement("article");
    article.className = "page loading";
    article.dataset.index = index;
    article.dataset.page = `P${String(index + 1).padStart(3, "0")}`;

    const img = document.createElement("img");
    img.alt = `Page ${index + 1}`;
    img.decoding = "async";

    if (index < 2) {
      img.fetchPriority = "high";
      img.src = url;
    } else {
      img.dataset.src = url;
    }

    img.addEventListener(
      "load",
      () => {
        article.classList.remove("loading");
      },
      { once: true }
    );

    article.appendChild(img);
    return article;
  }

  async function openChapter(index) {
    if (index < 0 || index >= state.chapters.length) return;
    state.currentIndex = index;

    const chapter = state.chapters[state.currentIndex];
    const files = await listImagesForChapter(chapter.id);

    state.currentPageUrls = files.map(
      (file) => `${CONFIG.dataRoot}/${chapter.id}/${encodeURIComponent(file)}`
    );

    els.pages.innerHTML = "";
    ensureIO();

    state.currentPageUrls.forEach((imageUrl, pageIndex) => {
      const node = buildPageNode(imageUrl, pageIndex);
      els.pages.appendChild(node);
      if (pageIndex >= 2) state.io.observe(node);
    });

    queueAhead(0);
    updateQuery(chapter.id);
    updateHeader(files.length);
    highlightCurrentChapter();
    window.scrollTo({ top: 0, behavior: "auto" });
  }

  function bindEvents() {
    els.prevBtn.addEventListener("click", () => openChapter(state.currentIndex - 1));
    els.nextBtn.addEventListener("click", () => openChapter(state.currentIndex + 1));

    els.chapterSelect.addEventListener("change", (event) => {
      const idx = state.chapters.findIndex((c) => c.id === event.target.value);
      if (idx >= 0) openChapter(idx);
    });

    els.zoomOutBtn.addEventListener("click", () => bumpZoom(-ZOOM.step));
    els.zoomInBtn.addEventListener("click", () => bumpZoom(ZOOM.step));
    els.zoomIndicator.addEventListener("dblclick", () => setZoom(1));

    window.addEventListener("resize", updateZoomLayout);
    window.addEventListener(
      "wheel",
      (event) => {
        if (!event.ctrlKey) return;
        event.preventDefault();
        const direction = event.deltaY > 0 ? -1 : 1;
        bumpZoom(direction * ZOOM.step);
      },
      { passive: false }
    );

    window.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") openChapter(state.currentIndex - 1);
      if (event.key === "ArrowRight") openChapter(state.currentIndex + 1);
      if (event.key === "+" || event.key === "=") bumpZoom(ZOOM.step);
      if (event.key === "-") bumpZoom(-ZOOM.step);
      if (event.key === "0") setZoom(1);
    });
  }

  async function init() {
    try {
      state.chapters = await loadManifest();
      renderChapterOptions();
      renderChapterList();

      els.totalChapters.textContent = String(state.chapters.length);
      els.totalPages.textContent = "...";

      const requested = new URLSearchParams(window.location.search).get("chapter");
      const initialIndex = state.chapters.findIndex((c) => c.id === requested);

      bindEvents();
      updateZoomLayout();
      await openChapter(initialIndex >= 0 ? initialIndex : 0);

      warmTotalPages()
        .then((total) => {
          els.totalPages.textContent = String(total);
        })
        .catch(() => {
          els.totalPages.textContent = "--";
        });
    } catch (error) {
      console.error(error);
      els.readerStatus.textContent = "加载失败";
      els.pages.innerHTML = `<p style='padding:20px'>${error.message}</p>`;
    }
  }

  init();
})();
