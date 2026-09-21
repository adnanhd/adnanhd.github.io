// Theme management and page navigation
// Content is pre-rendered by build.py — this file only handles interactive behavior.

const VALID_PAGES = ["about", "cv", "blogs", "timeline"];

// Apply the visual state for a page (toggle sections, nav, scroll). Does NOT
// touch history -- callers decide whether to push/replace the URL.
// Show the pre-built rail for ?filter=<key>; the others stay hidden.
function applyTimelineFilter(filter) {
  document.querySelectorAll(".timeline-view").forEach((v) => {
    v.hidden = (v.getAttribute("data-filter") || "") !== (filter || "");
  });
}

function applyPage(pageId, scrollTo, filter) {
  if (!VALID_PAGES.includes(pageId)) pageId = "about";
  applyTimelineFilter(filter);

  document.querySelectorAll(".page-section").forEach((page) => {
    page.classList.remove("active");
  });
  var section = document.getElementById(pageId);
  section.classList.add("active");

  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.remove("active");
  });
  var navLink = document.querySelector(`[data-page="${pageId}"]`);
  if (navLink) navLink.classList.add("active");

  // Scroll to a specific element within the page if requested.
  // Double rAF lets the layout settle (section just toggled display).
  if (scrollTo) {
    var target = document.getElementById(scrollTo);
    if (target) {
      requestAnimationFrame(() =>
        requestAnimationFrame(() =>
          target.scrollIntoView({ behavior: "smooth", block: "center" })
        )
      );
      return;
    }
  }

  // Scroll to top and move focus for accessibility
  window.scrollTo(0, 0);
  section.focus({ preventScroll: true });
}

// Navigate to a page, writing a GitHub-style ?tab=<page> URL (plus an optional
// #anchor for a subsection). push=false replaces the current history entry
// (used on initial load / canonicalizing legacy #hash links).
function showPage(pageId, scrollTo, push, filter) {
  if (!VALID_PAGES.includes(pageId)) return false;
  // keep whatever else the address carries (blog tags, for instance)
  var params = new URLSearchParams(window.location.search);
  params.set("tab", pageId);
  if (filter) params.set("filter", filter);
  else params.delete("filter");
  var url = "?" + params.toString().replace(/%2C/g, ",") +
            (scrollTo ? "#" + scrollTo : "");
  if (push === false) history.replaceState(null, "", url);
  else history.pushState(null, "", url);
  applyPage(pageId, scrollTo, filter);
  return false;
}

// Parse the current URL into {tab, scrollTo}, accepting both the new
// ?tab=<page>#anchor form and the legacy #page or #page:section form.
function parseRoute() {
  var params = new URLSearchParams(window.location.search);
  var tab = params.get("tab");
  var filter = params.get("filter");
  var hash = window.location.hash.replace("#", "");
  var scrollTo = hash || null;
  if (!tab && hash) {
    var parts = hash.split(":");
    if (VALID_PAGES.includes(parts[0])) {
      tab = parts[0];
      scrollTo = parts[1] || null;
    }
  }
  if (!VALID_PAGES.includes(tab)) tab = "about";
  return { tab: tab, scrollTo: scrollTo, filter: filter };
}

// Initial route: canonicalize whatever URL we landed on to the ?tab= form.
function initRoute() {
  var r = parseRoute();
  showPage(r.tab, r.scrollTo, false, r.filter);
}

// Follow an internal ?tab= link string (e.g. "?tab=cv#resume-papers").
// Returns true if it was a valid tab link and navigation happened.
function navigateTab(href, push) {
  var u = new URL(href, window.location.href);
  var q = new URLSearchParams(u.search);
  var tab = q.get("tab");
  if (!tab || !VALID_PAGES.includes(tab)) return false;
  showPage(tab, u.hash ? u.hash.slice(1) : null, push !== false, q.get("filter"));
  return true;
}

// Intercept clicks on internal ?tab= links so they navigate without a reload.
function initTabLinks() {
  document.addEventListener("click", (e) => {
    var a = e.target.closest("a");
    if (!a) return;
    var href = a.getAttribute("href");
    if (!href || href[0] !== "?") return;
    if (navigateTab(href)) e.preventDefault();
  });
}

function initTheme() {
  const themeToggle = document.getElementById("theme-toggle");
  const htmlElement = document.documentElement;

  themeToggle.addEventListener("click", () => {
    const currentTheme = htmlElement.getAttribute("data-theme");
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    htmlElement.setAttribute("data-theme", newTheme);
    localStorage.setItem("theme", newTheme);
  });

  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", (e) => {
      if (!localStorage.getItem("theme")) {
        htmlElement.setAttribute("data-theme", e.matches ? "dark" : "light");
      }
    });
}

function initCategoryToggles() {
  document.querySelectorAll(".links-category-toggle").forEach((btn) => {
    btn.addEventListener("click", () => {
      const expanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", !expanded);
    });
  });
}

function initImageLightbox() {
  var overlay = document.createElement("div");
  overlay.className = "lightbox-overlay";
  overlay.innerHTML = '<img class="lightbox-img" />';
  document.body.appendChild(overlay);

  var lbImg = overlay.querySelector(".lightbox-img");

  document.querySelectorAll(".publication-image img").forEach(function (img) {
    img.style.cursor = "zoom-in";
    img.addEventListener("click", function () {
      lbImg.src = img.src;
      lbImg.alt = img.alt;
      overlay.classList.add("active");
    });
  });

  overlay.addEventListener("click", function () {
    overlay.classList.remove("active");
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") overlay.classList.remove("active");
  });
}

// Hovering any element tied to a position (a publication card, a news
// line, a rail dot, the position bar itself) lights up every element
// of that position: card, dot and bar glow together.
function initTimelinePosHover() {
  // Dot <-> card pairing: hovering a rail dot highlights only its own
  // card (and vice versa via the CSS sibling rule), never the group.
  document.querySelectorAll(".rail-marker .rail-dot-hit").forEach(function (hit) {
    var marker = hit.parentElement;
    var card = marker.previousElementSibling;
    if (!card || !card.classList.contains("timeline-item")) card = null;
    hit.addEventListener("mouseenter", function () {
      marker.classList.add("pair-hot");
      if (card) card.classList.add("pair-hot");
    });
    hit.addEventListener("mouseleave", function () {
      marker.classList.remove("pair-hot");
      if (card) card.classList.remove("pair-hot");
    });
  });
  var nodes = document.querySelectorAll("[data-pos]:not(.rail-marker)");
  nodes.forEach(function (el) {
    var pid = el.getAttribute("data-pos");
    el.addEventListener("mouseenter", function () {
      document.querySelectorAll('[data-pos="' + pid + '"]').forEach(function (m) {
        m.classList.add("pos-hot");
      });
    });
    el.addEventListener("mouseleave", function () {
      document.querySelectorAll('[data-pos="' + pid + '"]').forEach(function (m) {
        m.classList.remove("pos-hot");
      });
    });
  });
}

function initLinkableHeaders() {
  document.querySelectorAll(".content-section h2").forEach(function (h2) {
    var section = h2.closest(".content-section");
    var container = section.querySelector("[id]");
    if (!container) return;
    var page = h2.closest(".page-section");
    if (!page) return;
    h2.style.cursor = "pointer";
    h2.title = "Copy link to section";
    h2.addEventListener("click", function () {
      var params = new URLSearchParams(window.location.search);
      params.set("tab", page.id);
      var anchor = "?" + params.toString().replace(/%2C/g, ",") + "#" + container.id;
      history.replaceState(null, "", anchor);
      container.scrollIntoView({ behavior: "smooth" });
    });
  });
}

function initTimelineAnchors() {
  // Year pills and month labels are deep-linkable: clicking one puts
  // ?tab=timeline#<id> in the address bar, same as the section headers.
  document.querySelectorAll(".timeline-year-label[id], .timeline-month-label[id]").forEach(function (el) {
    el.style.cursor = "pointer";
    el.title = "Copy link to this point";
    el.addEventListener("click", function () {
      history.replaceState(null, "", "?tab=timeline#" + el.id);
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  });
}

function initBlogFilter() {
  const search = document.getElementById("blog-search");
  const tagBox = document.getElementById("tag-search");
  const chips = document.querySelectorAll(".blog-filter");
  const list = document.getElementById("blog-posts");
  const items = [...document.querySelectorAll("#blog-posts .blog-item")];
  if (!items.length) return;
  const active = new Set();
  let ranked = null;          // urls in relevance order, or null for "no query"
  let excerpts = {};          // url -> the matched passage, already marked up

  // Say so in plain words when a query or a tag leaves nothing.
  function note() {
    let box = document.getElementById("blog-empty");
    if (!box) {
      box = document.createElement("p");
      box.id = "blog-empty";
      box.className = "blog-empty";
      list.parentElement.insertBefore(box, list.nextSibling);
    }
    const left = items.filter((i) => i.style.display !== "none").length;
    const q = ((search && search.value) || "").trim();
    const tags = [...active].join(", ");
    box.hidden = left > 0;
    box.textContent = q
      ? 'No results for "' + q + '"' + (tags ? " in " + tags : "") + "."
      : "No posts tagged " + tags + ".";
  }

  // pagefind reports "/blogs/foo/", the listing links "blogs/foo/index.html"
  const norm = (u) =>
    u.replace(/^.*?\/\/[^/]*/, "").replace(/index\.html$/, "")
     .replace(/^\//, "").replace(/\/$/, "");

  const tagged = (item) => {
    const tags = " " + (item.getAttribute("data-tags") || "") + " ";
    return !active.size ||
      [...active].some((t) => tags.indexOf(" " + t + " ") !== -1);
  };

  function render() {
    items.forEach((item) => {
      const href = norm(item.querySelector(".blog-link").getAttribute("href"));
      const hit = !ranked || ranked.indexOf(href) !== -1;
      item.style.display = hit && tagged(item) ? "" : "none";
      // show the passage that matched, with the words marked
      let ex = item.querySelector(".blog-excerpt");
      if (hit && excerpts[href]) {
        if (!ex) {
          ex = document.createElement("p");
          ex.className = "blog-excerpt";
          item.appendChild(ex);
        }
        ex.innerHTML = "..." + excerpts[href] + "...";
      } else if (ex) {
        ex.remove();
      }
    });
    note();
    if (ranked) {
      // pagefind hands back the best match first, so follow its order
      ranked.forEach((href) => {
        const row = items.find(
          (i) => norm(i.querySelector(".blog-link").getAttribute("href")) === href);
        if (row) list.appendChild(row);
      });
    } else {
      items.forEach((i) => list.appendChild(i));   // back to date order
    }
  }

  // The full text lives in the pagefind index next to the posts; until it
  // loads (or if it is missing) the row's own title/summary/tags answer.
  let lib = null, tried = false;
  async function index() {
    if (lib || tried) return lib;
    tried = true;
    try {
      // resolve against the page, not against this script's own folder
      const url = new URL("pagefind/pagefind.js", document.baseURI).href;
      lib = await import(url);
      await lib.options({ excerptLength: 40 });
    } catch (e) {
      lib = null;
    }
    return lib;
  }

  function fallback(q) {
    const terms = q.split(/\s+/);
    return items
      .filter((i) => terms.every(
        (t) => (i.getAttribute("data-head") || "").indexOf(t) !== -1))
      .map((i) => norm(i.querySelector(".blog-link").getAttribute("href")));
  }

  let timer = null;
  async function apply() {
    const q = ((search && search.value) || "").trim().toLowerCase();
    if (!q) {
      ranked = null;
      excerpts = {};
      render();
      return;
    }
    const pf = await index();
    if (!pf) {
      ranked = fallback(q);
      excerpts = {};
      render();
      return;
    }
    const res = await pf.search(q);
    // ten is plenty on screen, and each one carries the passage it matched
    const data = await Promise.all(res.results.slice(0, 10).map((r) => r.data()));
    ranked = data.map((d) => norm(d.url));
    excerpts = {};
    data.forEach((d) => { excerpts[norm(d.url)] = d.excerpt; });
    render();
  }

  function queue() {
    clearTimeout(timer);
    timer = setTimeout(apply, 120);
  }

  // Tags are addressable and stack: ?tab=blogs&tags=optimization,papers
  function sync(writeUrl) {
    const row = document.querySelector(".tag-chips");
    chips.forEach((c) =>
      c.classList.toggle("active", active.has(c.getAttribute("data-tag"))),
    );
    // chosen tags move to the front, so they stay visible on the one row
    if (row) {
      [...chips]
        .filter((c) => active.has(c.getAttribute("data-tag")))
        .forEach((c) => row.insertBefore(c, row.firstChild));
      [...chips]
        .filter((c) => !active.has(c.getAttribute("data-tag")))
        .sort((a, b) => a.textContent.localeCompare(b.textContent))
        .forEach((c) => row.appendChild(c));
    }
    render();
    if (writeUrl) {
      const picked = [...active].join(",");
      history.replaceState(null, "",
        "?tab=blogs" + (picked ? "&tags=" + picked : "") + window.location.hash);
    }
  }

  function toggle(tag) {
    if (!tag) return;
    if (active.has(tag)) active.delete(tag);
    else active.add(tag);
    sync(true);
  }

  if (search) search.addEventListener("input", queue);

  // The tag row is long, so it has its own box: typing narrows the chips,
  // and a selected chip always stays on screen.
  if (tagBox) {
    tagBox.addEventListener("input", () => {
      const t = tagBox.value.trim().toLowerCase();
      chips.forEach((c) => {
        const tag = c.getAttribute("data-tag") || "";
        c.hidden = t && !active.has(tag) && tag.indexOf(t) === -1;
      });
    });
  }

  const more = document.querySelector(".tags-toggle");
  if (more) {
    more.addEventListener("click", () => {
      const row = document.querySelector(".tag-chips");
      const open = row.classList.toggle("expanded");
      more.setAttribute("aria-expanded", open ? "true" : "false");
      more.textContent = open ? "less" : "more";
    });
  }

  chips.forEach((c) =>
    c.addEventListener("click", () => toggle(c.getAttribute("data-tag"))),
  );
  document.querySelectorAll("#blog-posts .blog-tag-inline").forEach((a) =>
    a.addEventListener("click", (ev) => {
      ev.preventDefault();
      toggle(a.getAttribute("data-tag"));
    }),
  );

  (new URLSearchParams(window.location.search).get("tags") || "")
    .split(",").filter(Boolean).forEach((t) => active.add(t));
  sync(false);
}

function initLinkableBoxes() {
  // Generic click-anywhere-on-the-box handler. Used for:
  //   * news rows (data-href is "?tab=timeline#tl-...", in-page tab nav)
  //   * open-source work cards (data-href is "projects/.../index.html",
  //     full navigation; the card's own title <a> goes to GitHub).
  // Inner anchors are honoured first so the title link still takes the
  // user to its own destination instead of being intercepted.
  const boxes = document.querySelectorAll(
    ".news-row[data-href], .work-item[data-href]",
  );
  boxes.forEach((box) => {
    function go() {
      const href = box.getAttribute("data-href");
      if (!href) return;
      if (href[0] === "?") {
        navigateTab(href);
      } else {
        window.location.href = href;
      }
    }
    box.addEventListener("click", (e) => {
      if (e.target.closest("a")) return;
      go();
    });
    box.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        go();
      }
    });
  });
}

// Refresh the GitHub sidebar metrics live on top of the baked values: total
// stars across all public repos + merged PRs. Cached in sessionStorage to stay
// under GitHub's 60 req/hr unauthenticated limit. Scholar (citations / h-index
// / i10) has no live API, so those badges keep their baked values from
// bio.yaml. Any fetch failure just leaves the baked number in place.
function initStats() {
  const links = document.querySelector(".links[data-github]");
  if (!links) return;
  const user = links.getAttribute("data-github");
  if (!user) return;

  function fmt(n) {
    n = Number(n);
    return n >= 1000 ? (n / 1000).toFixed(1).replace(/\.0$/, "") + "k" : n.toLocaleString();
  }

  function setMetric(name, value) {
    const span = links.querySelector('.lm-value[data-stat="' + name + '"]');
    if (!span || value === null || value === undefined || isNaN(value)) return;
    span.textContent = fmt(value);
  }

  function cached(key, ttlMs, producer) {
    try {
      const raw = sessionStorage.getItem(key);
      if (raw) {
        const obj = JSON.parse(raw);
        if (obj && Date.now() - obj.t < ttlMs) return Promise.resolve(obj.v);
      }
    } catch (e) {}
    return producer().then((v) => {
      try {
        sessionStorage.setItem(key, JSON.stringify({ t: Date.now(), v: v }));
      } catch (e) {}
      return v;
    });
  }

  function jget(url) {
    return fetch(url).then((r) => {
      if (!r.ok) throw new Error(r.status);
      return r.json();
    });
  }

  // Total stars across all public repos (paginate up to 300 repos).
  cached("stats:stars:" + user, 6 * 3600e3, () => {
    const pages = [1, 2, 3];
    return Promise.all(
      pages.map((p) =>
        jget(
          "https://api.github.com/users/" +
            user +
            "/repos?per_page=100&type=owner&page=" +
            p,
        ).catch(() => []),
      ),
    ).then((lists) =>
      lists.flat().reduce((sum, repo) => sum + (repo.stargazers_count || 0), 0),
    );
  })
    .then((n) => setMetric("stars", n))
    .catch(() => {});

  // Merged pull requests authored by the user.
  cached("stats:prs:" + user, 6 * 3600e3, () =>
    jget(
      "https://api.github.com/search/issues?q=" +
        encodeURIComponent("type:pr author:" + user + " is:merged") +
        "&per_page=1",
    ).then((d) => d.total_count),
  )
    .then((n) => setMetric("prs", n))
    .catch(() => {});
}

// GitHub-style local clock: show the site owner's current time in their
// timezone (data-tz), refreshed every 30s. Hides itself if the timezone is
// invalid / unsupported.
function initLocalTime() {
  const els = document.querySelectorAll(".local-time[data-tz]");
  if (!els.length) return;

  function offset(tz, now) {
    try {
      const parts = new Intl.DateTimeFormat("en-US", {
        timeZone: tz,
        timeZoneName: "shortOffset",
      }).formatToParts(now);
      const p = parts.find((x) => x.type === "timeZoneName");
      return p ? "(" + p.value.replace("GMT", "UTC") + ")" : "";
    } catch (e) {
      return "";
    }
  }

  function tick() {
    const now = new Date();
    els.forEach((el) => {
      const tz = el.getAttribute("data-tz");
      try {
        const t = new Intl.DateTimeFormat("en-GB", {
          hour: "2-digit",
          minute: "2-digit",
          timeZone: tz,
        }).format(now);
        const off = offset(tz, now);
        el.textContent = off ? t + " " + off : t;
      } catch (e) {
        const wrap = el.closest(".sidebar-localtime");
        if (wrap) wrap.style.display = "none";
      }
    });
  }

  tick();
  setInterval(tick, 30000);
}

// "Schedule a meeting" opens the booking calendar in an in-page overlay
// (dimmed backdrop + centered white dialog, same window) -- the same behavior
// as Google's own scheduling button, but triggered by our plain link. The
// dialog is forced white so it never clashes with the page theme.
function initAppointment() {
  const links = document.querySelectorAll(".sidebar-schedule[data-booking]");
  if (!links.length) return;

  let overlay, frame, loaded;
  function ensure() {
    if (overlay) return;
    overlay = document.createElement("div");
    overlay.className = "booking-overlay";
    overlay.innerHTML =
      '<div class="booking-dialog" role="dialog" aria-modal="true" aria-label="Book a meeting">' +
      '<button class="booking-close" aria-label="Close">&times;</button>' +
      '<iframe class="booking-frame" title="Book a meeting"></iframe>' +
      "</div>";
    document.body.appendChild(overlay);
    frame = overlay.querySelector(".booking-frame");
    overlay.addEventListener("click", (e) => {
      if (e.target === overlay || e.target.closest(".booking-close")) close();
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") close();
    });
  }
  function open(src) {
    ensure();
    if (loaded !== src) {
      frame.src = src;
      loaded = src;
    }
    overlay.classList.add("active");
    document.body.style.overflow = "hidden";
  }
  function close() {
    if (!overlay) return;
    overlay.classList.remove("active");
    document.body.style.overflow = "";
  }

  links.forEach((a) => {
    a.addEventListener("click", (e) => {
      e.preventDefault();
      open(a.getAttribute("data-booking"));
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initRoute();
  initTabLinks();
  initCategoryToggles();
  initImageLightbox();
  initLinkableHeaders();
  initTimelinePosHover();
  initTimelineAnchors();
  initBlogFilter();
  initLinkableBoxes();
  initStats();
  initLocalTime();
  initAppointment();
});

// Back/forward buttons change ?tab= without a reload -> re-apply the page.
window.addEventListener("popstate", () => {
  var r = parseRoute();
  applyPage(r.tab, r.scrollTo, r.filter);
});
