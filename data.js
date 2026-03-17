// Theme management and page navigation
// Content is pre-rendered by build.py — this file only handles interactive behavior.

const VALID_PAGES = ["about", "cv", "blogs", "timeline"];

function showPage(pageId, scrollTo) {
  if (!VALID_PAGES.includes(pageId)) return;

  document.querySelectorAll(".page-section").forEach((page) => {
    page.classList.remove("active");
  });
  var section = document.getElementById(pageId);
  section.classList.add("active");

  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.remove("active");
  });
  document
    .querySelector(`[data-page="${pageId}"]`)
    .classList.add("active");

  // Update hash without triggering hashchange
  history.replaceState(null, "", `#${pageId}`);

  // Scroll to a specific element within the page if requested
  if (scrollTo) {
    var target = document.getElementById(scrollTo);
    if (target) {
      target.scrollIntoView({ behavior: "smooth" });
      return;
    }
  }

  // Scroll to top and move focus for accessibility
  window.scrollTo(0, 0);
  section.focus({ preventScroll: true });
}

function handleHash() {
  const hash = window.location.hash.replace("#", "");
  // Support page:section format (e.g., #cv:resume-papers)
  const parts = hash.split(":");
  const pageId = parts[0];
  const sectionId = parts[1] || null;
  if (pageId && VALID_PAGES.includes(pageId)) {
    showPage(pageId, sectionId);
  }
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
    var anchor = page.id + ":" + container.id;
    h2.style.cursor = "pointer";
    h2.title = "Copy link to section";
    h2.addEventListener("click", function () {
      history.replaceState(null, "", "#" + anchor);
      container.scrollIntoView({ behavior: "smooth" });
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  handleHash();
  initCategoryToggles();
  initImageLightbox();
  initLinkableHeaders();
});

window.addEventListener("hashchange", handleHash);
