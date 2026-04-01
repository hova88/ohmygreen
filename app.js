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
    chapterMeta: document.getElementById("chapter-meta"),
    chapterSelect: document.getElementById("chapter-select"),
    prevBtn: document.getElementById("prev-btn"),
    nextBtn: document.getElementById("next-btn"),
    zoomInBtn: document.getElementById("zoom-in-btn"),
    zoomOutBtn: document.getElementById("zoom-out-btn"),
    fitBtn: document.getElementById("fit-btn"),
    layoutBtn: document.getElementById("layout-btn"),
    zoomLabel: document.getElementById("zoom-label")
  };

  const state = {
    chapters: [],
    currentIndex: 0,
    imageCache: new Map(),
    io: null,
    preloadCache: new Map(),
    currentPageUrls: [],
    zoom: 1,
    manualLayout: null
  };

  const collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

  const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

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

  function updateQuery(chapterId) {
    const url = new URL(window.location.href);
    url.searchParams.set("chapter", chapterId);
    window.history.replaceState({}, "", url);
  }

  function updateHeader(imageCount) {
    const chapter = state.chapters[state.currentIndex];
    els.seriesName.textContent = CONFIG.seriesName;
    els.chapterMeta.textContent = `${state.currentIndex + 1}/${state.chapters.length} · ${chapter.id} · ${imageCount} pages`;
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
      { rootMargin: "1800px 0px" }
    );
  }

  function buildPageNode(url, index) {
    const article = document.createElement("article");
    article.className = "page loading";
    article.dataset.index = index;

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

  function applyViewMode() {
    const autoDouble = state.zoom <= 0.85;
    const useDouble = state.manualLayout === null ? autoDouble : state.manualLayout === "double";

    els.pages.classList.toggle("layout-double", useDouble);
    els.layoutBtn.textContent = useDouble ? "双页" : "单页";

    const width = useDouble ? clamp(state.zoom * 1.5, 0.8, 1.8) : state.zoom;
    document.documentElement.style.setProperty("--page-width", `min(100%, ${Math.round(1100 * width)}px)`);
    els.zoomLabel.textContent = `${Math.round(state.zoom * 100)}%`;
  }

  function setZoom(nextZoom) {
    state.zoom = clamp(nextZoom, 0.5, 2.3);
    applyViewMode();
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
    window.scrollTo({ top: 0, behavior: "instant" });
  }

  function bindEvents() {
    els.prevBtn.addEventListener("click", () => openChapter(state.currentIndex - 1));
    els.nextBtn.addEventListener("click", () => openChapter(state.currentIndex + 1));

    els.zoomInBtn.addEventListener("click", () => setZoom(state.zoom + 0.1));
    els.zoomOutBtn.addEventListener("click", () => setZoom(state.zoom - 0.1));
    els.fitBtn.addEventListener("click", () => {
      state.manualLayout = null;
      setZoom(1);
    });

    els.layoutBtn.addEventListener("click", () => {
      const isNowDouble = els.pages.classList.contains("layout-double");
      state.manualLayout = isNowDouble ? "single" : "double";
      applyViewMode();
    });

    els.chapterSelect.addEventListener("change", (event) => {
      const idx = state.chapters.findIndex((c) => c.id === event.target.value);
      if (idx >= 0) openChapter(idx);
    });

    window.addEventListener("keydown", (event) => {
      if (event.key === "ArrowLeft") openChapter(state.currentIndex - 1);
      if (event.key === "ArrowRight") openChapter(state.currentIndex + 1);
      if (event.key === "+" || event.key === "=") setZoom(state.zoom + 0.1);
      if (event.key === "-") setZoom(state.zoom - 0.1);
      if (event.key.toLowerCase() === "d") {
        state.manualLayout = els.pages.classList.contains("layout-double") ? "single" : "double";
        applyViewMode();
      }
    });

    window.addEventListener(
      "wheel",
      (event) => {
        if (!event.ctrlKey && !event.metaKey) return;
        event.preventDefault();
        const delta = event.deltaY > 0 ? -0.06 : 0.06;
        setZoom(state.zoom + delta);
      },
      { passive: false }
    );
  }

  async function init() {
    try {
      state.chapters = await loadManifest();
      renderChapterOptions();
      applyViewMode();

      const requested = new URLSearchParams(window.location.search).get("chapter");
      const initialIndex = state.chapters.findIndex((c) => c.id === requested);

      bindEvents();
      await openChapter(initialIndex >= 0 ? initialIndex : 0);
    } catch (error) {
      console.error(error);
      els.chapterMeta.textContent = "Failed to load chapter list";
      els.pages.innerHTML = `<p style='padding:20px'>${error.message}</p>`;
    }
  }

  init();
})();
