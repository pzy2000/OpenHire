#!/usr/bin/env node

const ADMIN_URL = process.env.OPENHIRE_ADMIN_URL || "http://127.0.0.1:18790/admin";

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function loadPlaywright() {
  try {
    return await import("playwright");
  } catch (error) {
    console.error("Playwright is required for this smoke check. Install it in the active Node environment first.");
    throw error;
  }
}

const { chromium } = await loadPlaywright();
const browser = await chromium.launch({ headless: process.env.HEADLESS !== "false" });
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });

try {
  await page.goto(ADMIN_URL, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => {
    window.localStorage?.setItem("openhire.companion.runtimeReactions.v1", "true");
    window.localStorage?.removeItem("openhire.companion.reactionIntensity.v1");
  });
  await page.reload({ waitUntil: "domcontentloaded" });

  await page.waitForSelector("[data-companion-hotspot]", { timeout: 15000 });
  await page.waitForFunction(() => Boolean(window.OpenHireCompanion?.openChat), null, { timeout: 15000 });

  const menuActions = await page.$$eval("[data-companion-menu] [data-companion-action]", (items) =>
    items.map((item) => item.getAttribute("data-companion-action")),
  );
  assert(JSON.stringify(menuActions) === JSON.stringify(["pat", "feed", "chat"]), "Companion menu should expose Pat, Feed, Chat only.");

  await page.click("[data-companion-preferences-toggle]");
  await page.waitForSelector("[data-companion-preferences-panel]:not([hidden])");
  await page.waitForSelector('[data-companion-intensity="calm"]');
  await page.click('[data-companion-intensity="calm"]');

  const intensity = await page.evaluate(() => window.OpenHireCompanion?.reactionIntensity?.());
  assert(intensity === "calm", "Reaction intensity preference did not persist in the companion API.");

  const runtimeWasEnabled = await page.$eval('[data-companion-preference="runtime"]', (input) => input.checked);
  if (!runtimeWasEnabled) {
    await page.click('[data-companion-preference="runtime"]');
  }
  await page.click('[data-companion-preference="runtime"]');
  const runtimeReactionsDisabled = await page.evaluate(() => window.OpenHireCompanion?.runtimeReactionsEnabled?.() === false);
  assert(runtimeReactionsDisabled, "Runtime reactions preference did not disable companion runtime feedback.");

  await page.evaluate(() => window.OpenHireCompanion.openChat());
  await page.waitForSelector("#companion-chat-root");
  const chips = await page.$$eval("[data-companion-chat-chip]", (items) =>
    items.map((item) => item.getAttribute("data-companion-chat-chip")),
  );
  assert(JSON.stringify(chips) === JSON.stringify(["runtime", "error", "next"]), "Companion chat quick chips are incomplete.");

  const adminJsContainsGate = await page.evaluate(async () => {
    const url = new URL("/admin/assets/admin.js", window.location.href);
    const source = await fetch(url).then((response) => response.text());
    return source.includes("runtimeReactionsEnabled?.() === false");
  });
  assert(adminJsContainsGate, "Admin runtime feedback should check runtimeReactionsEnabled?.() === false before reacting.");

  console.log(`Companion smoke passed: ${ADMIN_URL}`);
} finally {
  await browser.close();
}
