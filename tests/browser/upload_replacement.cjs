"use strict";

// Run through tests/test_web_browser.py, which owns the local test server.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium, webkit } = require(process.env.DRAWERCHECK_PLAYWRIGHT_MODULE);
const [base, engine, directory] = process.argv.slice(2);
const files = fs.readdirSync(directory).filter(name => name.endsWith(".csv"))
  .map(name => ({ name, mimeType: "text/csv", buffer: fs.readFileSync(path.join(directory, name)) }));
const original = files.find(file => file.name === "pos_totals.csv");

function withCashSales(value) {
  const rows = original.buffer.toString("utf8").trimEnd().split(/\r?\n/);
  const fields = rows[1].split(",");
  fields[1] = value;
  rows[1] = fields.join(",");
  return { ...original, buffer: Buffer.from(rows.join("\n") + "\n") };
}

async function add(page, method, selected) {
  if (method === "chooser") {
    await page.locator("#file-input").setInputFiles(selected);
  } else {
    await page.evaluate(files => {
      const data = new DataTransfer();
      for (const file of files) data.items.add(new File([file.text], file.name, { type: "text/csv" }));
      document.getElementById("file-drop").dispatchEvent(
        new DragEvent("drop", { dataTransfer: data, bubbles: true, cancelable: true }),
      );
    }, selected.map(file => ({ name: file.name, text: file.buffer.toString("utf8") })));
  }
}

async function waitForGate(context, token, finished = false) {
  const deadline = Date.now() + 5000;
  while (Date.now() < deadline) {
    const response = await context.request.get(`${base}/__test__/gate/${token}`);
    const state = await response.json();
    if (state.waiting && (!finished || state.finished)) return state;
    await new Promise(resolve => setTimeout(resolve, 20));
  }
  throw new Error(`Upload gate did not reach ${finished ? "finished" : "waiting"}: ${token}`);
}

async function checkReplacement(browser, method, oldStatus) {
  const token = `${method}-${oldStatus}`;
  const width = oldStatus === 400 ? 320 : 1280;
  const theme = oldStatus === 400 ? "light" : "dark";
  const context = await browser.newContext({
    viewport: { width, height: 900 }, colorScheme: theme,
    extraHTTPHeaders: { "X-Test-Upload-Gate": token },
  });
  try {
    // Prove the late-answer guard too: receiving continues despite abort().
    await context.addInitScript(() => {
      const fetch = window.fetch;
      window.fetch = (url, options) => fetch(url, { ...options, signal: undefined });
    });
    const page = await context.newPage();
    page.setDefaultTimeout(5000);
    await page.goto(`${base}/#/prepare`);
    await add(page, "chooser", files);
    if (oldStatus === 400) await add(page, "chooser", [withCashSales("BAD")]);
    const oldResponse = page.waitForResponse(response => response.url().endsWith("/api/check") &&
      response.request().headers()["x-test-upload-gate"] === token, { timeout: 0 });
    oldResponse.catch(() => {}); // Cleanup can close the page after a failed assertion.
    await page.locator("#check-files").click();
    assert.equal((await waitForGate(context, token)).status, oldStatus);
    await page.locator("#file-input").focus();
    await add(page, method, [oldStatus === 400 ? original : withCashSales("0.00")]);
    await page.waitForFunction(() => !document.getElementById("check-files").hasAttribute("aria-disabled"), undefined, { timeout: 1000 });
    await page.waitForFunction(() => {
      const announcer = document.getElementById("announcer");
      return announcer.textContent === announcer.dataset.stopped;
    });
    assert.equal(await page.evaluate(() => document.activeElement.id), "file-input");
    assert.equal(await page.locator("#file-pos_totals [data-role='status']").textContent(), "Ready");
    assert.equal(await page.locator("#error-summary").isVisible(), false);
    assert.equal(await page.locator("#prepare-cancel").isVisible(), false);
    assert.equal(await page.locator("#prepare-slow").isVisible(), false);
    const captures = process.env.DRAWERCHECK_SCREENSHOT_DIR;
    if (captures) {
      const filename = `${path.basename(captures)}-prepare-${method}-old${oldStatus}-${engine}-${theme}-${width}.png`;
      const target = path.join(captures, filename);
      assert.equal(fs.existsSync(target), false, "Use a new capture folder; never overwrite screenshots");
      fs.mkdirSync(captures, { recursive: true });
      await page.evaluate(() => document.fonts.ready);
      await page.screenshot({ path: target, fullPage: true });
    }

    // Start a new check before the old response arrives.
    await context.setExtraHTTPHeaders({});
    const newResponse = page.waitForResponse(response => response.url().endsWith("/api/check"));
    await page.locator("#check-files").click();
    const current = await newResponse;
    assert.equal(current.status(), 200);
    const payload = await current.json();
    await page.locator("#view-results").waitFor({ state: "visible" });
    const headline = await page.locator("#summary-headline").textContent();
    await context.request.delete(`${base}/__test__/gate/${token}`);
    const stale = await oldResponse;
    assert.equal(stale.status(), oldStatus);
    await stale.finished();
    await waitForGate(context, token, true);
    // Let the earlier fetch/JSON handlers finish before checking the visible run.
    await page.evaluate(() => new Promise(resolve => setTimeout(resolve, 100)));
    assert.equal(await page.locator("#summary-headline").textContent(), headline);
    assert.equal(await page.locator("#lead-list .group-lead").count(), payload.flags.length);
    assert.equal(await page.locator("#error-summary").isVisible(), false);
    const drawer = payload.shifts[0];
    await page.evaluate(code => { location.hash = `#/drawer/${encodeURIComponent(code)}`; }, drawer.shift.shift_code);
    await page.locator("#view-drawer").waitFor({ state: "visible" });
    assert.equal(await page.locator("[data-outcome='difference']").textContent(), drawer.variance_amount);
    console.log(`${engine}: ${method} ignores late ${oldStatus}, keeps replacement, and reruns successfully`);
  } finally {
    await context.request.delete(`${base}/__test__/gate/${token}`).catch(() => {});
    await context.close();
  }
}

async function checkIgnoredFiles(browser, method) {
  const token = `${method}-ignored`;
  const context = await browser.newContext({ extraHTTPHeaders: { "X-Test-Upload-Gate": token } });
  try {
    const page = await context.newPage();
    await page.goto(`${base}/#/prepare`);
    await add(page, "chooser", files);
    await page.locator("#check-files").click();
    await waitForGate(context, token);
    await add(page, method, [{ name: "notes.txt", buffer: Buffer.from("Fictional ignored file") }]);
    assert.equal(await page.locator("#check-files").getAttribute("aria-disabled"), "true");
    assert.ok((await page.locator("#chooser-notes").textContent()).includes("notes.txt"));
    await context.request.delete(`${base}/__test__/gate/${token}`);
    await page.locator("#view-results").waitFor({ state: "visible" });
    await page.evaluate(() => { location.hash = "#/prepare"; });
    await page.locator("#view-prepare").waitFor({ state: "visible" });
    const cancelToken = `${token}-cancel`;
    await context.setExtraHTTPHeaders({ "X-Test-Upload-Gate": cancelToken });
    await page.locator("#check-files").click();
    await waitForGate(context, cancelToken);
    await page.locator("#prepare-cancel").click();
    await page.waitForFunction(() => !document.getElementById("check-files").hasAttribute("aria-disabled"));
    assert.equal(await page.evaluate(() => document.activeElement.id), "check-files");
    await context.request.delete(`${base}/__test__/gate/${cancelToken}`);
    await waitForGate(context, cancelToken, true);
    assert.equal(await page.locator("#view-prepare").isVisible(), true);
    console.log(`${engine}: ignored ${method} file keeps the check; explicit Cancel restores focus`);
  } finally {
    await context.request.delete(`${base}/__test__/gate/${token}`).catch(() => {});
    await context.close();
  }
}

(async () => {
  const browser = await (engine === "chrome" ? chromium.launch({ channel: "chrome" }) : webkit.launch());
  try {
    for (const method of ["chooser", "drop"]) {
      for (const status of [400, 200]) await checkReplacement(browser, method, status);
      await checkIgnoredFiles(browser, method);
    }
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
