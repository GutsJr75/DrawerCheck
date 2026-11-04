"use strict";

// Run through tests/test_web_browser.py, which owns the local test server.
const assert = require("node:assert/strict");
const { chromium, webkit } = require(process.env.DRAWERCHECK_PLAYWRIGHT_MODULE);
const [base, engine] = process.argv.slice(2);
const COUNTS = ["1", "3", "12", "6", "9", "0", "47", "0", "72", "35", "31", "60"];

async function fillDrawer(page, { report = true } = {}) {
  await page.fill('[data-field="business_date"]', "2026-11-02");
  await page.fill('[data-field="register_id"]', "R2");
  await page.fill('[data-field="cashier_id"]', "cashier_02");
  await page.fill('[data-field="opening_float"]', "200.00");
  await page.fill('[data-field="opened_at"]', "2026-11-02T08:00");
  await page.fill('[data-field="closed_at"]', "2026-11-02T20:00");
  const counts = page.locator('[data-field^="counts."]');
  for (let index = 0; index < COUNTS.length; index += 1) await counts.nth(index).fill(COUNTS[index]);
  if (report) {
    await page.check("#report-yes");
    await page.fill('[data-field="register_report.cash_sales"]', "1316.40");
    await page.fill('[data-field="register_report.cash_refunds"]', "18.25");
    await page.fill('[data-field="register_report.paid_ins"]', "20.00");
    await page.fill('[data-field="register_report.paid_outs"]', "32.50");
  } else {
    await page.check("#report-no");
  }
  await page.check("#drops-list");
  await page.fill("#drop-1-amount", "400.00");
  await page.click("#add-drop");
  await page.fill("#drop-2-amount", "400.00");
}

async function checkFromClose(page) {
  await page.click("#check-drawer");
  await page.waitForURL(/#\/review$/);
  await page.waitForSelector("#review-body:not([hidden])");
}

const tapeValues = (page) => page.locator('[data-tape="review"] td.money').allInnerTexts();
const leadTitles = (page) => page.locator("#review-leads .lead-title").allInnerTexts();
const coverage = (page) => page.locator("#coverage > li").evaluateAll((rows) =>
  rows.map((row) => [row.querySelector(".lead-title").textContent, row.querySelector(".status").textContent]));

async function reviewShowsTheWholeCheck(page) {
  await page.goto(`${base}/`);
  await page.click('#view-start a[href="#/close"]');
  await page.waitForURL(/#\/close$/);
  await fillDrawer(page);
  await checkFromClose(page);
  assert.deepEqual(await tapeValues(page), [
    "$200.00", "$1,316.40", "$20.00", "$18.25", "$32.50", "$800.00", "$685.65", "$665.65", "-$20.00",
  ]);
  const twenty = await page.locator("#review-count tbody tr").nth(2).locator("th, td").allInnerTexts();
  assert.deepEqual(twenty, ["$20.00", "12", "$240.00"]);
  assert.equal(await page.innerText("#review-count-total"), "$665.65");
  assert.deepEqual(await leadTitles(page), ["Cash difference to check", "Missing sign-off", "Possible single bill"]);
  assert.deepEqual(await coverage(page), [
    ["Cash difference to check", "Ran, lead found"],
    ["Possible single bill", "Ran, lead found"],
    ["Possible swapped digits", "Ran, no lead"],
    ["Missing sign-off", "Ran, lead found"],
    ["Missing or inconsistent records", "Ran, no lead"],
    ["Repeated shortages", "Not run"],
    ["Bank deposit to check", "Not run"],
  ]);
  assert.match(await page.innerText("#coverage"), /no other drawers were entered/);
  console.log(`${engine}: Review shows Python's tape, count lines, leads, and which checks ran`);
}

async function signOffClearsOnlyTheSignOffLead(page) {
  await page.fill('[data-field="verifier_id"]', "manager_01");
  assert.equal(await page.isVisible("#review-stale"), true);
  assert.equal(await page.isHidden("#review-result"), true);
  await page.fill('[data-field="variance_note"]', "Recounted with manager. Still short 20.00.");
  await page.click("#check-again");
  await page.waitForSelector("#review-result:not([hidden])");
  assert.deepEqual(await leadTitles(page), ["Cash difference to check", "Possible single bill"]);
  assert.equal(await page.innerText('[data-review="difference"]'), "-$20.00");
  const signoff = page.locator("#coverage > li", { hasText: "Missing sign-off" });
  assert.equal(await signoff.locator(".status").innerText(), "Ran, no lead");
  assert.match(await signoff.locator(".lead-message").innerText(), /does not confirm who signed/);
  console.log(`${engine}: a verifier and note clear the sign-off lead; the difference stays -$20.00`);
}

async function lateReplyIsIgnored(page) {
  let release;
  const gate = new Promise((resolve) => { release = resolve; });
  await page.route("**/api/drawer", async (route) => {
    const response = await route.fetch();
    await gate;
    await route.fulfill({ response });
  });
  await page.fill('[data-field="variance_note"]', "Recounted twice. Still short 20.00.");
  await page.click("#check-again");
  await page.waitForSelector("#review-cancel:not([hidden])");
  await page.fill('[data-field="variance_note"]', "Recounted twice with manager. Still short 20.00.");
  release();
  await page.waitForTimeout(500);
  assert.equal(await page.isVisible("#review-stale"), true, "the late reply must not replace the stale notice");
  assert.equal(await page.isHidden("#review-result"), true);
  await page.unroute("**/api/drawer");
  console.log(`${engine}: editing the sign-off while waiting ignores the late reply`);
}

async function invalidVerifierIsMarked(page) {
  await page.fill('[data-field="verifier_id"]', " manager_01");
  await page.click("#check-again");
  await page.waitForSelector("#review-summary:not([hidden]) li");
  assert.equal(await page.evaluate(() => document.activeElement.id), "review-summary");
  assert.equal(await page.getAttribute('[data-field="verifier_id"]', "aria-invalid"), "true");
  assert.match(await page.getAttribute('[data-field="verifier_id"]', "aria-describedby"), /^problem-verifier_id/);
  await page.click("#review-problems a");
  assert.equal(await page.evaluate(() => document.activeElement.id), "signoff-verifier");
  console.log(`${engine}: an invalid verifier ID is listed and marked on Review`);
}

async function newCheckClearsTheSignOff(page) {
  await page.click("text=Change the entries");
  await page.waitForURL(/#\/close$/);
  assert.equal(await page.inputValue('[data-field="counts.0.25"]'), "72");
  await checkFromClose(page);
  assert.equal(await page.inputValue('[data-field="verifier_id"]'), "");
  assert.deepEqual(await leadTitles(page), ["Cash difference to check", "Missing sign-off", "Possible single bill"]);
  console.log(`${engine}: going back keeps the entries; a new check clears the sign-off`);
}

async function missingReportIsExplained(browser) {
  const page = await browser.newPage();
  await page.goto(`${base}/#/close`);
  await fillDrawer(page, { report: false });
  await checkFromClose(page);
  assert.equal(await page.innerText('[data-review="expected"]'), "unknown");
  assert.equal(await page.isVisible("#review-no-report"), true);
  const states = Object.fromEntries(await coverage(page));
  assert.equal(states["Cash difference to check"], "Not run");
  assert.equal(states["Missing sign-off"], "Not run");
  assert.equal(states["Missing or inconsistent records"], "Ran, lead found");
  assert.match(await page.innerText("#coverage"), /Whether expected cash is negative: expected cash is unknown\./);
  console.log(`${engine}: a missing report leaves expected cash unknown and difference checks not run`);
  await page.close();
}

(async () => {
  const webkitPath = process.env.DRAWERCHECK_WEBKIT_EXECUTABLE;
  const browser = await (engine === "chrome"
    ? chromium.launch({ channel: "chrome" })
    : webkit.launch(webkitPath ? { executablePath: webkitPath } : {}));
  try {
    const page = await browser.newPage();
    await reviewShowsTheWholeCheck(page);
    await signOffClearsOnlyTheSignOffLead(page);
    await lateReplyIsIgnored(page);
    await invalidVerifierIsMarked(page);
    await newCheckClearsTheSignOff(page);
    await missingReportIsExplained(browser);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
