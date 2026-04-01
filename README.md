# Berserk Image Reader (Static, Very Fast)

This reader now uses **image-folder rendering** (not PDF). It is designed for your structure like:

```text
data/berserk/chapter_01/*.jpg|*.png
```

Exactly matching your example (`chapter_01` with many page images).

## 1) Data format (recommended)

Put chapter folders under `data/berserk`:

```text
data/
  berserk/
    chapter_01/
      Berserk - 001 ... p001.png
      Berserk - 001 ... p002.png
      ...
    chapter_02/
      ...
    chapters.json
```

Create `data/berserk/chapters.json`:

```json
{
  "series": "Berserk",
  "chapters": [
    { "folder": "chapter_01", "title": "Chapter 01" },
    { "folder": "chapter_02", "title": "Chapter 02" }
  ]
}
```

## 2) How chapter/image reading works

### Preferred mode (production)
- Read `chapters.json` for chapter order.
- For each chapter, request directory index and parse image file names.
- Sort file names with numeric-aware ordering, then render continuous long-scroll pages.

### Fallback mode
If `chapters.json` is missing, app tries to parse directory listing at `data/berserk/` to discover `chapter_XX/` folders automatically.

> For fallback to work, your web server must allow directory listing (`autoindex`).

## 3) Performance design

- `img.decoding = "async"`
- `loading="lazy"`
- `IntersectionObserver` with large `rootMargin` (preload before entering viewport)
- First 3 pages `fetchPriority="high"`
- Warm-up prefetch for next pages
- `content-visibility: auto` to reduce off-screen rendering cost

This combination is very fast for long manga chapters with hundreds of images.

## 4) Local run

```bash
python3 -m http.server 8080
```

Open:

- `http://localhost:8080/`
- Direct chapter: `http://localhost:8080/?chapter=chapter_01`

## 5) Public deployment example: `https://ohmygreen.cc/berserk/`

### Nginx (recommended)

Put files under:

```text
/var/www/ohmygreen/berserk/
```

Server config example:

```nginx
server {
    listen 80;
    server_name ohmygreen.cc;
    root /var/www/ohmygreen;

    location /berserk/ {
        try_files $uri $uri/ /berserk/index.html;
        autoindex on;               # needed if you use fallback directory discovery
        charset utf-8;              # keep image names with spaces safe
    }

    types {
        image/webp webp;
        image/avif avif;
    }
}
```

Then visit:

- `https://ohmygreen.cc/berserk/`
- `https://ohmygreen.cc/berserk/?chapter=chapter_01`

## 6) Notes for your exact filenames

Your files contain spaces and symbols like `[ ]` and `-`. This reader URL-encodes each file name automatically before requesting image assets, so names like:

- `Berserk - 001 (v01) - p003 [Digital] [Cyborgzx-repack].png`

will load correctly in the browser.
