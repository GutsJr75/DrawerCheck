"use strict";

// Run through tests/test_web_browser.py, which owns the local test server.
const assert = require("node:assert/strict");
const { chromium, webkit } = require(process.env.DRAWERCHECK_PLAYWRIGHT_MODULE);
const [base, engine] = process.argv.slice(2);
const COUNTS = ["1", "3", "12", "6", "9", "0", "47", "0", "72", "35", "31", "60"];

async function fillDrawer(page, { register = "R2", cashier = "cashier_02" } = {}) {
  await page.fill('[data-field="business_date"]', "2026-11-02");
  await page.fill('[data-field="register_id"]', register);
  await page.fill('[data-field="cashier_id"]', cashier);
  await page.fill('[data-field="opening_float"]', "200.00");
  await page.fill('[data-field="opened_at"]', "2026-11-02T08:00");
  await page.fill('[data-field="closed_at"]', "2026-11-02T20:00");
  const counts = page.locator('[data-field^="counts."]');
  for (let index = 0; index < COUNTS.length; index += 1) await counts.nth(index).fill(COUNTS[index]);
  await page.check("#report-yes");
  await page.fill('[data-field="register_report.cash_sales"]', "1316.40");
  await page.fill('[data-field="register_report.cash_refunds"]', "18.25");
  await page.fill('[data-field="register_report.paid_ins"]', "20.00");
  await page.fill('[data-field="register_report.paid_outs"]', "32.50");
  await page.check("#drops-list");
  await page.fill("#drop-1-amount", "400.00");
  await page.click("#add-drop");
  await page.fill("#drop-2-amount", "400.00");
}

async function reviewVisible(page) {
  await page.waitForURL(/#\/review$/);
  await page.waitForSelector("#review-result:not([hidden])");
}

const focusedId = (page) => page.evaluate(() => document.activeElement.id);

// Holds /api/drawer replies until release() is called.
async function holdReplies(page) {
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  await page.route("**/api/drawer", async (route) => {
    const response = await route.fetch();
    await gate;
    await route.fulfill({ response }).catch(() => {});
  });
  return () => release();
}

async function keyboardCompletesTheClose(page) {
  await page.goto(`${base}/#/close`);
  await fillDrawer(page);
  // Choices and checks by keyboard alone: Space picks a radio, Enter submits.
  await page.check("#report-no");
  await page.focus("#report-yes");
  await page.keyboard.press("Space");
  assert.equal(await page.isChecked("#report-yes"), true);
  await page.fill('[data-field="register_report.paid_outs"]', "32.5");
  await page.focus('[data-field="counts.0.01"]');
  await page.keyboard.press("Enter");
  await page.waitForSelector("#close-summary:not([hidden]) li");
  assert.equal(await focusedId(page), "close-summary");
  // WebKit, like Safari by default, moves to links with Option+Tab.
  await page.keyboard.press(engine === "webkit" ? "Alt+Tab" : "Tab");
  await page.keyboard.press("Enter");
  assert.equal(await focusedId(page), "close-paid-out");
  await page.keyboard.press("ControlOrMeta+A");
  await page.keyboard.type("32.50");
  await page.keyboard.press("Enter");
  await reviewVisible(page);
  assert.equal(await focusedId(page), "review-heading");
  await page.focus('[data-field="verifier_id"]');
  await page.keyboard.type("manager_01");
  await page.focus('[data-field="variance_note"]');
  await page.keyboard.type("Recounted with manager.");
  await page.focus("#check-again");
  await page.keyboard.press("Enter");
  await page.waitForSelector("#review-result:not([hidden])");
  assert.equal(await page.locator("#review-leads > li").count(), 2);
  console.log(`${engine}: Close and Review complete by keyboard, with summary links followed by Enter`);
}

async function refreshForgetsEverything(page) {
  await page.reload();
  assert.equal(await page.isVisible("#review-empty"), true);
  assert.equal(await page.isHidden("#review-body"), true);
  await page.goto(`${base}/#/close`);
  assert.equal(await page.inputValue('[data-field="counts.20.00"]'), "");
  assert.equal(await page.isChecked("#report-yes"), false);
  console.log(`${engine}: refreshing clears the result and every entry, as the page says`);
}

async function cancelStopsWaitingOnBothPages(page) {
  await page.goto(`${base}/#/close`);
  await page.reload();
  await fillDrawer(page);
  let release = await holdReplies(page);
  await page.click("#check-drawer");
  await page.waitForSelector("#close-cancel:not([hidden])");
  await page.focus("#close-cancel");
  await page.keyboard.press("Enter");
  assert.equal(await focusedId(page), "check-drawer");
  release();
  await page.waitForTimeout(400);
  assert.match(page.url(), /#\/close$/);
  assert.equal(await page.inputValue('[data-field="counts.20.00"]'), "12");
  await page.unroute("**/api/drawer");
  console.log(`${engine}: Cancel on Close a drawer keeps the entries and ignores the late reply`);

  await page.click("#check-drawer");
  await reviewVisible(page);
  release = await holdReplies(page);
  await page.fill('[data-field="verifier_id"]', "manager_01");
  await page.click("#check-again");
  await page.waitForSelector("#review-cancel:not([hidden])");
  await page.click("#review-cancel");
  assert.equal(await focusedId(page), "check-again");
  release();
  await page.waitForTimeout(400);
  assert.equal(await page.isVisible("#review-stale"), true, "a cancelled check leaves the result stale");
  await page.unroute("**/api/drawer");
  console.log(`${engine}: Cancel on Review keeps the sign-off and the stale notice`);
}

async function failuresOfferRetryWithoutLosingEntries(page) {
  await page.goto(`${base}/#/close`);
  await page.reload();
  await fillDrawer(page);
  await page.route("**/api/drawer", (route) => route.abort());
  await page.click("#check-drawer");
  await page.waitForSelector("#close-error p");
  assert.equal(await page.innerText("#close-error p"),
    "The demo server could not be reached. Check your connection and try again.");
  await page.unroute("**/api/drawer");
  await page.route("**/api/drawer", (route) => route.fulfill({
    status: 503, contentType: "application/json",
    body: JSON.stringify({ error: { message: "The check could not finish. Try again with the example or upload the seven CSVs again." } }),
  }));
  await page.click("#close-error button");
  await page.waitForSelector("#close-error p");
  assert.match(await page.innerText("#close-error p"), /could not finish/);
  assert.equal(await page.inputValue('[data-field="counts.20.00"]'), "12");
  await page.unroute("**/api/drawer");
  await page.click("#close-error button");
  await reviewVisible(page);
  console.log(`${engine}: a network failure and a server error each offer Try again; entries stay`);
}

async function userTextIsShownAsText(page) {
  await page.goto(`${base}/#/close`);
  await page.reload();
  await fillDrawer(page, { register: "<b>R2</b>", cashier: "x<img src=x>" });
  await page.click("#check-drawer");
  await reviewVisible(page);
  const about = await page.innerText("#review-about");
  assert.match(about, /Register <b>R2<\/b>, Monday/);
  assert.match(about, /Cashier ID x<img src=x>\./);
  assert.equal(await page.locator("#view-review b, #view-review img").count(), 0);
  const [download] = await Promise.all([page.waitForEvent("download"), page.click("#download-closing")]);
  const sheet = require("node:fs").readFileSync(await download.path(), "utf8");
  assert.ok(sheet.includes("&lt;b&gt;R2&lt;/b&gt;") && !sheet.includes("<b>R2</b>"));
  console.log(`${engine}: IDs that look like markup stay text on Review and in the closing sheet`);
}

async function dropListStopsAtTwenty(page) {
  await page.goto(`${base}/#/close`);
  await page.reload();
  await page.check("#drops-list");
  while (await page.isVisible("#add-drop")) await page.click("#add-drop");
  assert.equal(await page.locator("#drop-rows > li").count(), 20);
  console.log(`${engine}: Add a drop disappears at the 20-drop limit`);
}

(async () => {
  const webkitPath = process.env.DRAWERCHECK_WEBKIT_EXECUTABLE;
  const browser = await (engine === "chrome"
    ? chromium.launch({ channel: "chrome" })
    : webkit.launch(webkitPath ? { executablePath: webkitPath } : {}));
  try {
    const page = await browser.newPage({ acceptDownloads: true });
    await keyboardCompletesTheClose(page);
    await refreshForgetsEverything(page);
    await cancelStopsWaitingOnBothPages(page);
    await failuresOfferRetryWithoutLosingEntries(page);
    await userTextIsShownAsText(page);
    await dropListStopsAtTwenty(page);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
