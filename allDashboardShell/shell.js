const renderZone = document.getElementById("render-zone");
const controlsPanel = document.getElementById("controls-panel");

let currentIframe = null;

// -------------------------
// LOAD DASH (iframe)
// -------------------------
function loadDash(url) {
  renderZone.innerHTML = "";

  const iframe = document.createElement("iframe");
  iframe.src = url;

  renderZone.appendChild(iframe);
  currentIframe = iframe;
}

// -------------------------
// GLOBAL STATE
// -------------------------
const state = {
  range: null
};

// -------------------------
// SEND MESSAGE TO DASH
// -------------------------
function sendToDash(payload) {
  if (!currentIframe) return;

  currentIframe.contentWindow.postMessage({
    type: "FILTER_UPDATE",
    payload
  }, "*");
}

// -------------------------
// CONTROLS
// -------------------------
function buildControls() {
  controlsPanel.innerHTML = "";

  const title = document.createElement("h4");
  title.innerText = "Filters";
  controlsPanel.appendChild(title);

  const btn6m = document.createElement("button");
  btn6m.innerText = "Last 6 months";
  btn6m.onclick = () => {
    state.range = "6m";
    sendToDash({ range: "6m" });
  };

  const btnAll = document.createElement("button");
  btnAll.innerText = "All";
  btnAll.onclick = () => {
    state.range = "all";
    sendToDash({ range: "all" });
  };

  controlsPanel.appendChild(btn6m);
  controlsPanel.appendChild(document.createElement("br"));
  controlsPanel.appendChild(btnAll);
}

// -------------------------
// INIT
// -------------------------
function init() {
  buildControls();

  // 🔥 Load your existing Dash dev app
  loadDash("/dev/epu/en/");
}

init();