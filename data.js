// Theme management and page navigation
// Content is pre-rendered by build.py — this file only handles interactive behavior.

const VALID_PAGES = ["about", "resume", "blogs", "news"];

function showPage(pageId) {
  if (!VALID_PAGES.includes(pageId)) return;

  document.querySelectorAll(".page-section").forEach((page) => {
    page.classList.remove("active");
  });
  document.getElementById(pageId).classList.add("active");

  document.querySelectorAll(".nav-link").forEach((link) => {
    link.classList.remove("active");
  });
  document
    .querySelector(`[data-page="${pageId}"]`)
    .classList.add("active");

  // Update hash without triggering hashchange
  history.replaceState(null, "", `#${pageId}`);
}

function handleHash() {
  const hash = window.location.hash.replace("#", "");
  if (hash && VALID_PAGES.includes(hash)) {
    showPage(hash);
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

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  handleHash();
});

window.addEventListener("hashchange", handleHash);
