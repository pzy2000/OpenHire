// OpenHire Live2D companion: zero-build ESM module that mounts a desktop pet
// inside the admin sidebar and exposes a small public API on window.

// jsdelivr requires a literal at-sign in package versions and does NOT decode
// percent-40 back to at-sign before routing. At the same time, some upstream
// proxies (e.g. Cloudflare ScrapeShield Email Address Obfuscation) rewrite
// any literal at-sign substring in served files to placeholder tokens, which
// breaks the URL. Workaround: build the at-sign at runtime via fromCharCode
// so the source text we ship contains none of those triggers, yet the browser
// sends a real at-sign when fetching jsdelivr.
const _AT = String.fromCharCode(64);
const _JSDELIVR = "https://cdn.jsdelivr.net";
const DEFAULT_MODEL_URL =
  _JSDELIVR + "/npm/live2d-widget-model-shizuku" + _AT + "latest/assets/shizuku.model.json";
const VENDOR_SCRIPTS = [
  // Cubism 2.x SDK first; pixi-live2d-display/cubism2 expects window.Live2DModelWebGL.
  _JSDELIVR + "/gh/dylanNew/live2d/webgl/Live2D/lib/live2d.min.js",
  // Pixi v6 full UMD bundle.
  _JSDELIVR + "/npm/pixi.js" + _AT + "6.5.10/dist/browser/pixi.min.js",
  // pixi-live2d-display Cubism 2 bundle, attaches to PIXI.live2d.
  _JSDELIVR + "/npm/pixi-live2d-display" + _AT + "0.4.0/dist/cubism2.min.js",
];
const VENDOR_TIMEOUT_MS = 12000;
const RUNTIME_TIMEOUT_MS = 9000;
const STAGE_DIMENSIONS_TIMEOUT_MS = 4000;
const LOG_PREFIX = "[companion]";
const STORAGE_KEY = "openhire.companion.history.v1";
const MAX_HISTORY = 24;
const MAX_DISPLAY_MESSAGES = 60;
const IDLE_INTERVAL_MS = 12000;
const MAIN_AGENT_SESSION_ID = "live2d-companion";

const I18N = {
  zh: {
    "companion.action.pat": "摸摸",
    "companion.action.feed": "投喂",
    "companion.action.chat": "对话",
    "companion.chat.title": "和小伙伴聊聊",
    "companion.chat.placeholder": "对小伙伴说点什么...",
    "companion.chat.send": "发送",
    "companion.chat.toggle.label": "对话出口",
    "companion.chat.toggle.side": "侧信道（轻量）",
    "companion.chat.toggle.main": "主控（吃 context）",
    "companion.chat.warning.main":
      "主控通道开启：对话会写入主 agent session，注意 context 占用与延迟。",
    "companion.chat.clear": "清空对话",
    "companion.chat.empty": "和小伙伴打个招呼吧。",
    "companion.chat.error": "网络抽风了，要不再试一次？",
    "companion.chat.thinking": "小伙伴正在想...",
    "companion.mood.idle": "随时待命",
    "companion.mood.pat": "好痒呀~",
    "companion.mood.feed": "好好吃！",
    "companion.mood.thinking": "嗯嗯...",
    "companion.mood.error": "出错啦...",
    "companion.fallback.body": "Live2D 引擎未就绪，先用霓虹版陪你聊。",
    "companion.hotspot.aria": "点一下小伙伴",
  },
  en: {
    "companion.action.pat": "Pat",
    "companion.action.feed": "Feed",
    "companion.action.chat": "Chat",
    "companion.chat.title": "Talk to the companion",
    "companion.chat.placeholder": "Say something to the companion...",
    "companion.chat.send": "Send",
    "companion.chat.toggle.label": "Chat backend",
    "companion.chat.toggle.side": "Side channel (light)",
    "companion.chat.toggle.main": "Main agent (uses context)",
    "companion.chat.warning.main":
      "Main agent channel is on: replies will be written to the main agent session and may use context budget.",
    "companion.chat.clear": "Clear chat",
    "companion.chat.empty": "Say hi to your sidebar buddy.",
    "companion.chat.error": "Network hiccup. Mind giving it another try?",
    "companion.chat.thinking": "Companion is thinking...",
    "companion.mood.idle": "Standing by",
    "companion.mood.pat": "Tickles!",
    "companion.mood.feed": "Yum!",
    "companion.mood.thinking": "Hmm...",
    "companion.mood.error": "Glitching...",
    "companion.fallback.body": "Live2D runtime offline; chatting with neon outline mode.",
    "companion.hotspot.aria": "Tap the companion",
  },
};

const FALLBACK_SVG = `
<svg viewBox="0 0 220 280" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
  <defs>
    <linearGradient id="cmp-fb-grad" x1="0" x2="0" y1="0" y2="1">
      <stop offset="0%" stop-color="var(--neon-cyan, #6df7ff)" stop-opacity="0.95" />
      <stop offset="100%" stop-color="var(--neon-violet, #b07bff)" stop-opacity="0.85" />
    </linearGradient>
    <radialGradient id="cmp-fb-glow" cx="50%" cy="40%" r="60%">
      <stop offset="0%" stop-color="var(--neon-cyan, #6df7ff)" stop-opacity="0.45" />
      <stop offset="100%" stop-color="var(--neon-cyan, #6df7ff)" stop-opacity="0" />
    </radialGradient>
  </defs>
  <ellipse cx="110" cy="240" rx="70" ry="14" fill="url(#cmp-fb-glow)" />
  <g fill="none" stroke="url(#cmp-fb-grad)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
    <path d="M70 110 q40 -68 80 0 v74 q0 18 -18 22 h-44 q-18 -4 -18 -22 z" />
    <path d="M82 124 v22" />
    <path d="M138 124 v22" />
    <circle cx="92" cy="142" r="4.4" fill="var(--neon-cyan, #6df7ff)" stroke="none" />
    <circle cx="128" cy="142" r="4.4" fill="var(--neon-cyan, #6df7ff)" stroke="none" />
    <path d="M96 168 q14 10 28 0" />
    <path d="M62 96 q-6 -22 18 -34" />
    <path d="M158 96 q6 -22 -18 -34" />
    <path d="M88 84 q22 -18 44 0" />
    <path d="M70 200 q-12 6 -16 24" />
    <path d="M150 200 q12 6 16 24" />
  </g>
  <g fill="var(--neon-cyan, #6df7ff)" opacity="0.85">
    <circle cx="46" cy="86" r="1.6" />
    <circle cx="178" cy="68" r="1.4" />
    <circle cx="190" cy="156" r="1.4" />
    <circle cx="32" cy="170" r="1.6" />
  </g>
</svg>
`;

const STATE = {
  mounted: false,
  pixiApp: null,
  model: null,
  resizeObserver: null,
  language: () => "en",
  modelName: "openhire",
  history: [],
  useMain: false,
  fallback: false,
  bootError: null,
  motionGroups: { idle: [], pat: [], feed: [], chat: [] },
  idleTimer: null,
  moodTimer: null,
  lastInteractionAt: 0,
  menuOpen: false,
  chatOpen: false,
  busy: false,
};

// ------------------------------- Utilities ---------------------------------

function t(key, lang) {
  const dict = I18N[lang] || I18N.en;
  return dict[key] ?? I18N.en[key] ?? key;
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;" }[ch]),
  );
}

function escMultiline(value) {
  return esc(value).replace(/\n/g, "<br />");
}

function loadHistory() {
  try {
    const raw = window.localStorage?.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed
      .slice(-MAX_HISTORY)
      .filter((m) => m && typeof m === "object" && typeof m.content === "string");
  } catch (_err) {
    return [];
  }
}

function saveHistory(history) {
  try {
    window.localStorage?.setItem(STORAGE_KEY, JSON.stringify(history.slice(-MAX_HISTORY)));
  } catch (_err) {
    // best-effort persistence
  }
}

function $(selector, root = document) {
  return root.querySelector(selector);
}

// ------------------------------- Live2D boot -------------------------------

const _vendorPromises = new Map();

function loadVendorScript(src) {
  if (_vendorPromises.has(src)) return _vendorPromises.get(src);
  const promise = new Promise((resolve, reject) => {
    // Reuse an existing tag if a previous defer-loaded copy already completed.
    const existing = document.querySelector(`script[data-companion-vendor="${src}"]`);
    if (existing && existing.dataset.companionVendorReady === "true") {
      resolve();
      return;
    }
    const script = document.createElement("script");
    script.src = src;
    script.async = false;
    script.crossOrigin = "anonymous";
    script.dataset.companionVendor = src;
    let timeoutId = null;
    const cleanup = () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
    script.onload = () => {
      script.dataset.companionVendorReady = "true";
      cleanup();
      console.info(LOG_PREFIX, "vendor loaded", src);
      resolve();
    };
    script.onerror = (event) => {
      cleanup();
      console.warn(LOG_PREFIX, "vendor failed", src, event);
      reject(new Error(`Failed to load vendor script: ${src}`));
    };
    timeoutId = setTimeout(() => {
      cleanup();
      reject(new Error(`Vendor script timeout: ${src}`));
    }, VENDOR_TIMEOUT_MS);
    document.head.appendChild(script);
  });
  _vendorPromises.set(src, promise);
  return promise;
}

async function loadVendorScripts() {
  for (const src of VENDOR_SCRIPTS) {
    await loadVendorScript(src);
  }
}

async function waitForRuntimes() {
  const deadline = performance.now() + RUNTIME_TIMEOUT_MS;
  while (performance.now() < deadline) {
    if (window.PIXI && window.PIXI.live2d && window.Live2D && window.Live2DModelWebGL) {
      return;
    }
    await new Promise((r) => setTimeout(r, 100));
  }
  const missing = [];
  if (!window.PIXI) missing.push("PIXI");
  if (!window.PIXI?.live2d) missing.push("PIXI.live2d");
  if (!window.Live2D) missing.push("Live2D");
  if (!window.Live2DModelWebGL) missing.push("Live2DModelWebGL");
  throw new Error(`Live2D runtime not ready (missing: ${missing.join(", ")})`);
}

async function waitForStageDimensions(stage) {
  const deadline = performance.now() + STAGE_DIMENSIONS_TIMEOUT_MS;
  while (performance.now() < deadline) {
    if (stage.clientWidth > 0 && stage.clientHeight > 0) {
      return { width: stage.clientWidth, height: stage.clientHeight };
    }
    await new Promise((r) => setTimeout(r, 80));
  }
  return {
    width: Math.max(220, stage.clientWidth),
    height: Math.max(160, stage.clientHeight),
  };
}

async function bootLive2D() {
  console.info(LOG_PREFIX, "boot start");
  await loadVendorScripts();
  await waitForRuntimes();
  console.info(LOG_PREFIX, "runtimes ready", {
    pixiVersion: window.PIXI?.VERSION,
    live2d: typeof window.Live2D,
    cubismVersion: window.PIXI?.live2d?.VERSION,
  });

  const stage = $("[data-companion-stage]");
  const canvas = $("[data-companion-canvas]");
  if (!stage || !canvas) {
    throw new Error("companion stage/canvas missing in DOM");
  }
  const dimensions = await waitForStageDimensions(stage);
  const width = Math.max(1, dimensions.width);
  const height = Math.max(1, dimensions.height);
  const dpr = Math.min(window.devicePixelRatio || 1, 2);

  const app = new window.PIXI.Application({
    view: canvas,
    width,
    height,
    resolution: dpr,
    autoDensity: true,
    backgroundAlpha: 0,
    antialias: true,
  });
  STATE.pixiApp = app;
  console.info(LOG_PREFIX, "pixi app ready", { width, height, dpr });

  const model = await window.PIXI.live2d.Live2DModel.from(DEFAULT_MODEL_URL);
  STATE.model = model;
  console.info(LOG_PREFIX, "model loaded", {
    naturalWidth: model.internalModel?.width,
    naturalHeight: model.internalModel?.height,
    motions: Object.keys(model.internalModel?.settings?.motions || {}),
  });
  applyLayout(width, height);
  app.stage.addChild(model);

  if (typeof ResizeObserver === "function") {
    STATE.resizeObserver = new ResizeObserver(() => {
      const w = Math.max(1, stage.clientWidth);
      const h = Math.max(1, stage.clientHeight);
      app.renderer.resize(w, h);
      applyLayout(w, h);
    });
    STATE.resizeObserver.observe(stage);
  }

  collectMotionGroups(model);
  startIdleLoop();
  console.info(LOG_PREFIX, "boot complete");
}

function applyLayout(width, height) {
  const model = STATE.model;
  if (!model || !model.internalModel) return;
  const naturalWidth = model.internalModel.width || width || 1;
  const naturalHeight = model.internalModel.height || height || 1;
  // Fit the whole model inside the stage with a small breathing margin so the
  // PIXI canvas never clips the head or feet. The previous `* 1.2` upscale
  // pushed the model beyond the canvas, hiding the lower body.
  const fit = Math.min(width / naturalWidth, height / naturalHeight);
  const scale = fit * 0.94;
  model.scale.set(scale);
  model.anchor?.set?.(0.5, 1);
  model.x = width / 2;
  // Anchor the feet at (or just inside) the canvas bottom so the full body
  // sits inside the visible viewport.
  model.y = height - 2;
}

function collectMotionGroups(model) {
  const definitions = model?.internalModel?.settings?.motions || {};
  const keys = Object.keys(definitions);
  STATE.motionGroups.idle = keys.filter((key) => /idle/i.test(key));
  STATE.motionGroups.pat = keys.filter((key) =>
    /(tap_head|head|stroke|pat|tap)/i.test(key),
  );
  STATE.motionGroups.feed = keys.filter((key) =>
    /(flick|pinch|shake|surprise|disgust|hungry)/i.test(key),
  );
  STATE.motionGroups.chat = keys.filter((key) => /(talk|speak|greet|smile|happy|express)/i.test(key));
  // Fallbacks: if a category is empty, use any non-idle group.
  const nonIdle = keys.filter((key) => !/idle/i.test(key));
  if (!STATE.motionGroups.pat.length) STATE.motionGroups.pat = nonIdle;
  if (!STATE.motionGroups.feed.length) STATE.motionGroups.feed = nonIdle;
  if (!STATE.motionGroups.chat.length) STATE.motionGroups.chat = nonIdle;
}

function pickMotion(category) {
  const groups = STATE.motionGroups[category];
  if (groups && groups.length) {
    return groups[Math.floor(Math.random() * groups.length)];
  }
  return null;
}

function playMotion(category) {
  if (!STATE.model) return;
  const name = pickMotion(category);
  if (!name) return;
  try {
    STATE.model.motion(name);
  } catch (err) {
    console.warn("[companion] motion failed", category, err);
  }
}

function startIdleLoop() {
  if (STATE.idleTimer) clearInterval(STATE.idleTimer);
  STATE.idleTimer = setInterval(() => {
    if (document.hidden) return;
    if (STATE.lastInteractionAt && Date.now() - STATE.lastInteractionAt < 5000) return;
    if (STATE.busy) return;
    playMotion("idle");
  }, IDLE_INTERVAL_MS);
}

function showFallback(error) {
  console.warn("[companion] fallback", error);
  STATE.fallback = true;
  STATE.bootError = error ? String(error.message || error) : null;
  const fallback = $("[data-companion-fallback]");
  const canvas = $("[data-companion-canvas]");
  if (fallback) {
    fallback.hidden = false;
    fallback.innerHTML = FALLBACK_SVG;
    fallback.setAttribute("data-fallback-active", "true");
  }
  if (canvas) canvas.style.display = "none";
}

// ------------------------------- Interactions ------------------------------

function bindHotspot() {
  const hotspot = $("[data-companion-hotspot]");
  if (!hotspot) return;

  hotspot.addEventListener("click", (event) => {
    event.preventDefault();
    event.stopPropagation();
    STATE.lastInteractionAt = Date.now();
    toggleMenu();
  });

  hotspot.addEventListener("contextmenu", (event) => {
    event.preventDefault();
    STATE.lastInteractionAt = Date.now();
    toggleMenu();
  });

  hotspot.addEventListener("mousemove", (event) => {
    if (!STATE.model || typeof STATE.model.focus !== "function") return;
    const rect = hotspot.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    const nx = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    const ny = ((event.clientY - rect.top) / rect.height) * 2 - 1;
    try {
      STATE.model.focus(nx, -ny);
    } catch (_err) {
      // best-effort focus tracking
    }
  });

  hotspot.addEventListener("mouseleave", () => {
    if (!STATE.model || typeof STATE.model.focus !== "function") return;
    try {
      STATE.model.focus(0, 0);
    } catch (_err) {
      // ignore
    }
  });
}

function bindMenu() {
  const menu = $("[data-companion-menu]");
  if (!menu) return;
  menu.addEventListener("click", (event) => {
    const button = event.target.closest("[data-companion-action]");
    if (!button) return;
    event.preventDefault();
    closeMenu();
    const action = button.dataset.companionAction;
    if (action === "pat") doPat();
    else if (action === "feed") doFeed();
    else if (action === "chat") openChat();
  });

  document.addEventListener("click", (event) => {
    if (!STATE.menuOpen) return;
    if (
      event.target.closest("[data-companion-menu]") ||
      event.target.closest("[data-companion-hotspot]")
    ) {
      return;
    }
    closeMenu();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") {
      if (STATE.chatOpen) {
        closeChat();
        return;
      }
      if (STATE.menuOpen) closeMenu();
    }
  });
}

function toggleMenu() {
  STATE.menuOpen ? closeMenu() : openMenu();
}

function openMenu() {
  const menu = $("[data-companion-menu]");
  if (!menu) return;
  menu.hidden = false;
  STATE.menuOpen = true;
}

function closeMenu() {
  const menu = $("[data-companion-menu]");
  if (!menu) return;
  menu.hidden = true;
  STATE.menuOpen = false;
}

function doPat() {
  STATE.lastInteractionAt = Date.now();
  playMotion("pat");
  spawnFx("sparkle");
  setMood("pat");
}

function doFeed() {
  STATE.lastInteractionAt = Date.now();
  playMotion("feed");
  spawnFx("heart");
  setMood("feed");
}

function spawnFx(kind) {
  const fx = $("[data-companion-fx]");
  if (!fx) return;
  if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  const count = 7;
  for (let i = 0; i < count; i++) {
    const span = document.createElement("span");
    span.className = `companion-fx-particle companion-fx-${esc(kind)}`;
    const x = 25 + Math.random() * 60;
    const dx = (Math.random() - 0.5) * 70;
    const delay = Math.random() * 220;
    const duration = 1500 + Math.random() * 600;
    span.style.setProperty("--fx-x", `${x}%`);
    span.style.setProperty("--fx-dx", `${dx}px`);
    span.style.setProperty("--fx-duration", `${duration}ms`);
    span.style.animationDelay = `${delay}ms`;
    fx.appendChild(span);
    setTimeout(() => span.remove(), duration + delay + 60);
  }
}

function setMood(key) {
  const moodEl = $("[data-companion-mood]");
  if (!moodEl) return;
  if (STATE.moodTimer) {
    clearTimeout(STATE.moodTimer);
    STATE.moodTimer = null;
  }
  const moodKey = `companion.mood.${key}`;
  moodEl.dataset.companionMoodKey = moodKey;
  moodEl.textContent = t(moodKey, STATE.language());
  if (key !== "idle") {
    STATE.moodTimer = setTimeout(() => setMood("idle"), 4200);
  }
}

// ----------------------------------- Chat ----------------------------------

function openChat() {
  STATE.lastInteractionAt = Date.now();
  if (STATE.chatOpen) return;
  STATE.chatOpen = true;
  renderChatPanel();
  const ta = $("[data-companion-chat-input]");
  ta?.focus();
}

function closeChat() {
  STATE.chatOpen = false;
  const root = document.getElementById("companion-chat-root");
  if (root) root.innerHTML = "";
}

function renderChatPanel() {
  const root = document.getElementById("companion-chat-root");
  if (!root) return;
  const lang = STATE.language();
  root.innerHTML = `
    <aside class="companion-chat" role="dialog" aria-label="${esc(t("companion.chat.title", lang))}">
      <header class="companion-chat-head">
        <div class="companion-chat-title">${esc(t("companion.chat.title", lang))}</div>
        <button class="companion-chat-close" type="button" data-companion-chat-close="true" aria-label="Close">×</button>
      </header>
      <div class="companion-chat-toggle">
        <span class="companion-chat-toggle-label">${esc(t("companion.chat.toggle.label", lang))}</span>
        <label class="companion-chat-switch">
          <input type="checkbox" data-companion-chat-main="true" ${STATE.useMain ? "checked" : ""} />
          <span class="companion-chat-switch-track" aria-hidden="true"></span>
          <span class="companion-chat-switch-knob" aria-hidden="true"></span>
          <span class="companion-chat-switch-mode">${esc(STATE.useMain ? t("companion.chat.toggle.main", lang) : t("companion.chat.toggle.side", lang))}</span>
        </label>
      </div>
      ${STATE.useMain ? `<div class="companion-chat-warning">${esc(t("companion.chat.warning.main", lang))}</div>` : ""}
      <div class="companion-chat-list" data-companion-chat-list="true"></div>
      <form class="companion-chat-input" data-companion-chat-form="true">
        <textarea data-companion-chat-input="true" rows="2" placeholder="${esc(t("companion.chat.placeholder", lang))}"></textarea>
        <div class="companion-chat-actions">
          <button type="button" class="companion-chat-clear" data-companion-chat-clear="true">${esc(t("companion.chat.clear", lang))}</button>
          <button type="submit" class="companion-chat-send">${esc(t("companion.chat.send", lang))}</button>
        </div>
      </form>
    </aside>
  `;
  bindChatPanel();
  renderChatList();
}

function bindChatPanel() {
  const root = document.getElementById("companion-chat-root");
  if (!root) return;
  root.querySelector("[data-companion-chat-close]")?.addEventListener("click", closeChat);
  root.querySelector("[data-companion-chat-form]")?.addEventListener("submit", onChatSubmit);
  root.querySelector("[data-companion-chat-input]")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      onChatSubmit(event);
    }
  });
  root.querySelector("[data-companion-chat-main]")?.addEventListener("change", (event) => {
    STATE.useMain = Boolean(event.target.checked);
    renderChatPanel();
  });
  root.querySelector("[data-companion-chat-clear]")?.addEventListener("click", () => {
    STATE.history = [];
    saveHistory(STATE.history);
    renderChatList();
  });
}

function renderChatList() {
  const root = document.getElementById("companion-chat-root");
  if (!root) return;
  const list = root.querySelector("[data-companion-chat-list]");
  if (!list) return;
  if (!STATE.history.length) {
    list.innerHTML = `<div class="companion-chat-empty">${esc(t("companion.chat.empty", STATE.language()))}</div>`;
    return;
  }
  list.innerHTML = STATE.history
    .slice(-MAX_DISPLAY_MESSAGES)
    .map((msg) => `
      <div class="companion-chat-msg companion-chat-msg-${esc(msg.role || "assistant")}">
        <div class="companion-chat-bubble">${escMultiline(msg.content)}</div>
      </div>
    `)
    .join("");
  if (STATE.busy) {
    list.insertAdjacentHTML(
      "beforeend",
      `<div class="companion-chat-msg companion-chat-msg-pending"><div class="companion-chat-bubble companion-chat-bubble-pending">${esc(t("companion.chat.thinking", STATE.language()))}</div></div>`,
    );
  }
  list.scrollTop = list.scrollHeight;
}

async function onChatSubmit(event) {
  event.preventDefault?.();
  if (STATE.busy) return;
  const root = document.getElementById("companion-chat-root");
  if (!root) return;
  const textarea = root.querySelector("[data-companion-chat-input]");
  const text = (textarea?.value || "").trim();
  if (!text) return;
  if (text.length > 2000) {
    setMood("error");
    return;
  }
  textarea.value = "";
  textarea.disabled = true;
  STATE.busy = true;
  STATE.history.push({ role: "user", content: text });
  saveHistory(STATE.history);
  setMood("thinking");
  renderChatList();
  try {
    const reply = await sendChat(text);
    STATE.history.push({ role: "assistant", content: reply || "..." });
    saveHistory(STATE.history);
    playMotion("chat");
    setMood("idle");
  } catch (err) {
    console.error("[companion] chat error", err);
    STATE.history.push({
      role: "assistant",
      content: t("companion.chat.error", STATE.language()),
    });
    saveHistory(STATE.history);
    setMood("error");
  } finally {
    STATE.busy = false;
    renderChatList();
    if (textarea) {
      textarea.disabled = false;
      textarea.focus();
    }
  }
}

async function sendChat(text) {
  if (STATE.useMain) {
    const res = await fetch("/v1/chat/completions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        model: STATE.modelName || "openhire",
        messages: [{ role: "user", content: text }],
        stream: false,
        session_id: MAIN_AGENT_SESSION_ID,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    return json.choices?.[0]?.message?.content || "";
  }

  const messages = STATE.history.slice(-MAX_HISTORY).map((msg) => ({
    role: msg.role,
    content: msg.content,
  }));
  const res = await fetch("/admin/api/companion/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const json = await res.json();
  return json.content || "";
}

// ------------------------------- Public API --------------------------------

function refreshLanguage() {
  const lang = STATE.language();
  document.querySelectorAll("[data-companion-action]").forEach((btn) => {
    const action = btn.dataset.companionAction;
    if (!action) return;
    btn.textContent = t(`companion.action.${action}`, lang);
  });
  const moodEl = $("[data-companion-mood]");
  if (moodEl) {
    const key = moodEl.dataset.companionMoodKey || "companion.mood.idle";
    moodEl.textContent = t(key, lang);
  }
  const hotspot = $("[data-companion-hotspot]");
  if (hotspot) hotspot.setAttribute("aria-label", t("companion.hotspot.aria", lang));
  if (STATE.chatOpen) renderChatPanel();
}

function syncTheme(_theme) {
  // Fallback SVG already references CSS variables, no work needed yet.
}

function destroy() {
  if (STATE.idleTimer) clearInterval(STATE.idleTimer);
  if (STATE.moodTimer) clearTimeout(STATE.moodTimer);
  STATE.resizeObserver?.disconnect();
  STATE.pixiApp?.destroy?.(true, { children: true, texture: true });
  STATE.pixiApp = null;
  STATE.model = null;
  STATE.idleTimer = null;
  STATE.moodTimer = null;
}

async function mount(opts) {
  if (STATE.mounted) return;
  STATE.mounted = true;
  STATE.language = typeof opts?.lang === "function" ? opts.lang : () => "en";
  STATE.modelName = opts?.modelName || "openhire";
  STATE.history = loadHistory();

  bindMenu();
  bindHotspot();
  refreshLanguage();
  setMood("idle");

  const stage = $("[data-companion-stage]");
  const startBoot = () => {
    bootLive2D().catch(showFallback);
  };
  if (!stage) {
    startBoot();
    return;
  }
  if (typeof IntersectionObserver === "function") {
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        observer.disconnect();
        startBoot();
      }
    }, { threshold: 0.1 });
    observer.observe(stage);
  } else {
    startBoot();
  }
}

window.OpenHireCompanion = {
  mount,
  refreshLanguage,
  syncTheme,
  destroy,
  pat: doPat,
  feed: doFeed,
  openChat,
};

export { mount, refreshLanguage, syncTheme, destroy };
