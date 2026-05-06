function initOutframe() {
  const body = document.body;

  // Prevent double init
  if (document.getElementById("app-shell")) return;

  // Create structure
  const shell = document.createElement("div");
  shell.id = "app-shell";

  const header = document.createElement("div");
  header.id = "shell-header";
  const path = window.location.pathname;

  let title = "Epu";
  let lang = "EN";

  // detect language from URL
  if (path.includes("/es/")) {
    lang = "ES";
  }

  header.innerHTML = `
    <span style="flex:1"><strong>${title} (${lang})</strong></span>
    <button id="menu-toggle">☰ Filters</button>
  `;

  const main = document.createElement("div");
  main.id = "shell-main";

  const controls = document.createElement("div");
  controls.id = "shell-controls";

  const render = document.createElement("div");
  render.id = "shell-render";

  // Move existing content into render zone
  const original = Array.from(body.children);
  original.forEach(el => {
    if (el.id !== "app-shell") {
      render.appendChild(el);
    }
  });

  // Build layout
  // Create menu container (collapsible)
  const menu = document.createElement("div");
  menu.id = "shell-menu";

  menu.appendChild(controls);

  // Build layout
  shell.appendChild(header);
  shell.appendChild(menu);
  shell.appendChild(render);

  body.appendChild(shell);

  // expose hooks
  window.SHELL = {
    controlsContainer: controls,
    renderContainer: render
  };

  const toggleBtn = document.getElementById("menu-toggle");
  const menuEl = document.getElementById("shell-menu");

  toggleBtn.onclick = () => {
    menuEl.classList.toggle("open");
  };
}

// Run after load
window.addEventListener("load", initOutframe);