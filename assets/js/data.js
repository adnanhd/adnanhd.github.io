// Theme management and page navigation
// Content is pre-rendered by build.py — this file only handles interactive behavior.

const VALID_PAGES = ["about", "cv", "blogs", "timeline"];

// Apply the visual state for a page (toggle sections, nav, scroll). Does NOT
// touch history -- callers decide whether to push/replace the URL.
function applyPage(pageId, scrollTo) {
  if (!VALID_PAGES.includes(pageId)) pageId = "about";

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
function showPage(pageId, scrollTo, push) {
  if (!VALID_PAGES.includes(pageId)) return false;
  var url = "?tab=" + pageId + (scrollTo ? "#" + scrollTo : "");
  if (push === false) history.replaceState(null, "", url);
  else history.pushState(null, "", url);
  applyPage(pageId, scrollTo);
  return false;
}

// Parse the current URL into {tab, scrollTo}, accepting both the new
// ?tab=<page>#anchor form and the legacy #page or #page:section form.
function parseRoute() {
  var tab = new URLSearchParams(window.location.search).get("tab");
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
  return { tab: tab, scrollTo: scrollTo };
}

// Initial route: canonicalize whatever URL we landed on to the ?tab= form.
function initRoute() {
  var r = parseRoute();
  showPage(r.tab, r.scrollTo, false);
}

// Follow an internal ?tab= link string (e.g. "?tab=cv#resume-papers").
// Returns true if it was a valid tab link and navigation happened.
function navigateTab(href, push) {
  var u = new URL(href, window.location.href);
  var tab = new URLSearchParams(u.search).get("tab");
  if (!tab || !VALID_PAGES.includes(tab)) return false;
  showPage(tab, u.hash ? u.hash.slice(1) : null, push !== false);
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

function initLinkableHeaders() {
  document.querySelectorAll(".content-section h2").forEach(function (h2) {
    var section = h2.closest(".content-section");
    var container = section.querySelector("[id]");
    if (!container) return;
    var page = h2.closest(".page-section");
    if (!page) return;
    var anchor = "?tab=" + page.id + "#" + container.id;
    h2.style.cursor = "pointer";
    h2.title = "Copy link to section";
    h2.addEventListener("click", function () {
      history.replaceState(null, "", anchor);
      container.scrollIntoView({ behavior: "smooth" });
    });
  });
}

function initBlogFilter() {
  const search = document.getElementById("blog-search");
  const filters = document.querySelectorAll(".blog-filter");
  const items = document.querySelectorAll("#blog-posts .blog-item");
  if (!items.length) return;
  let activeTag = "";

  function apply() {
    const q = ((search && search.value) || "").trim().toLowerCase();
    items.forEach((item) => {
      const tags = " " + (item.getAttribute("data-tags") || "") + " ";
      const hay = item.getAttribute("data-search") || "";
      const matchTag = !activeTag || tags.indexOf(" " + activeTag + " ") !== -1;
      const matchText = !q || hay.indexOf(q) !== -1;
      item.style.display = matchTag && matchText ? "" : "none";
    });
  }

  function setTag(tag) {
    activeTag = tag || "";
    filters.forEach((b) =>
      b.classList.toggle("active", (b.getAttribute("data-tag") || "") === activeTag),
    );
    apply();
  }

  if (search) search.addEventListener("input", apply);
  filters.forEach((btn) =>
    btn.addEventListener("click", () => setTag(btn.getAttribute("data-tag") || "")),
  );
  // Clicking a tag chip on a card activates that filter.
  document.querySelectorAll("#blog-posts .blog-tag").forEach((chip) =>
    chip.addEventListener("click", () => setTag(chip.getAttribute("data-tag") || "")),
  );
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

function initTimelineFilter() {
  const chips = document.querySelectorAll(".timeline-filter");
  if (!chips.length) return;
  // Cards and their rail markers both carry a timeline-<type> class, so a
  // single selector toggles each event together with its dot+arm.
  const items = document.querySelectorAll(
    "#timeline-container .timeline-item, #timeline-container .rail-marker",
  );

  function setType(type) {
    chips.forEach((c) =>
      c.classList.toggle("active", (c.getAttribute("data-tl-type") || "") === type),
    );
    items.forEach((el) => {
      const show = !type || el.classList.contains("timeline-" + type);
      el.style.display = show ? "" : "none";
    });
  }

  chips.forEach((c) =>
    c.addEventListener("click", () => setType(c.getAttribute("data-tl-type") || "")),
  );
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
  initBlogFilter();
  initTimelineFilter();
  initLinkableBoxes();
  initStats();
  initLocalTime();
  initAppointment();
});

// Back/forward buttons change ?tab= without a reload -> re-apply the page.
window.addEventListener("popstate", () => {
  var r = parseRoute();
  applyPage(r.tab, r.scrollTo);
});
