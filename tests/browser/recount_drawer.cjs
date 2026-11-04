"use strict";

// Run through tests/test_web_browser.py, which owns the local test server.
const assert = require("node:assert/strict");
const { chromium, webkit } = require(process.env.DRAWERCHECK_PLAYWRIGHT_MODULE);
const [base, engine] = process.argv.slice(2);
const COUNTS = ["1", "3", "12", "6", "9", "0", "47", "0", "72", "35", "31", "60"];
const RECOUNT = ["1", "3", "13", "6", "9", "0", "47", "0", "72", "35", "31", "60"];

async function fillDrawer(page) {
  await page.fill('[data-field="business_date"]', "2026-11-02");
  await page.fill('[data-field="register_id"]', "R2");
  await page.fill('[data-field="cashier_id"]', "cashier_02");
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

async function fillRecount(page, values) {
  const inputs = page.locator('[data-field^="recount."]');
  for (let index = 0; index < values.length; index += 1) await inputs.nth(index).fill(values[index]);
}

async function checkFromClose(page) {
  await page.click("#check-drawer");
  await page.waitForURL(/#\/review$/);
  await page.waitForSelector("#review-body:not([hidden])");
}

async function checkAgain(page) {
  await page.click("#check-again");
  await page.waitForSelector("#review-result:not([hidden])");
}

const compare = (page) => page.locator("#recount-compare tbody tr").evaluateAll((rows) =>
  rows.map((row) => [...row.querySelectorAll("th, td")].map((cell) => cell.textContent)));
const leadCount = (page) => page.locator("#review-leads > li").count();

(async () => {
  const webkitPath = process.env.DRAWERCHECK_WEBKIT_EXECUTABLE;
  const browser = await (engine === "chrome"
    ? chromium.launch({ channel: "chrome" })
    : webkit.launch(webkitPath ? { executablePath: webkitPath } : {}));
  try {
    const page = await browser.newPage();
    await page.goto(`${base}/#/close`);
    await fillDrawer(page);
    await checkFromClose(page);
    assert.equal(await leadCount(page), 3);

    await page.click("#recount-toggle");
    assert.equal(await page.getAttribute("#recount-toggle", "aria-expanded"), "true");
    assert.equal(await page.evaluate(() => document.activeElement.dataset.field), "recount.100.00");
    assert.equal(await page.isVisible("#review-stale"), true);
    await fillRecount(page, RECOUNT.map((value, index) => (index === 2 ? "" : value)));
    await page.click("#check-again");
    await page.waitForSelector("#review-summary:not([hidden]) li");
    assert.deepEqual(await page.locator("#review-problems li").allInnerTexts(), [
      "Recount: enter how many $20 bills were counted, as a whole number. Write 0 if none.",
    ]);
    assert.equal(await page.getAttribute('[data-field="recount.20.00"]', "aria-invalid"), "true");
    console.log(`${engine}: a blank recount line is named as the recount's and marked`);

    await page.fill('[data-field="recount.20.00"]', "13");
    await checkAgain(page);
    assert.deepEqual(await compare(page), [
      ["Counted cash", "$665.65", "$685.65"],
      ["Difference", "-$20.00", "$0.00"],
      ["Status", "Short", "Balanced (within $1.00)"],
    ]);
    assert.equal(await page.innerText("#review-count-heading"), "Count sheet: recount");
    assert.equal(await page.innerText('[data-review="difference"]'), "$0.00");
    assert.equal(await leadCount(page), 0);
    const firstTwenty = await page.locator("#first-count tbody tr").nth(2).locator("th, td").allTextContents();
    assert.deepEqual(firstTwenty, ["$20.00", "12", "$240.00"]);
    console.log(`${engine}: the recount is checked and both counts are compared from Python's figures`);

    await page.click("text=Change the entries");
    await page.waitForURL(/#\/close$/);
    assert.equal(await page.inputValue('[data-field="counts.20.00"]'), "12");
    await page.goBack();
    await page.waitForSelector("#review-result:not([hidden])");
    assert.equal(await page.inputValue('[data-field="recount.20.00"]'), "13");
    console.log(`${engine}: the first count is untouched by the recount`);

    await page.fill('[data-field="recount.0.01"]', "61");
    assert.equal(await page.isVisible("#review-stale"), true);
    assert.equal(await page.isHidden("#recount-compare"), true);
    await page.click("#recount-toggle");
    assert.equal(await page.isHidden("#recount-sheet"), true);
    assert.equal(await page.inputValue('[data-field="recount.20.00"]'), "");
    await checkAgain(page);
    assert.equal(await page.isHidden("#recount-compare"), true);
    assert.equal(await page.innerText("#review-count-heading"), "Count sheet");
    assert.equal(await leadCount(page), 3);
    console.log(`${engine}: editing the recount marks the result stale; removing it checks the first count`);

    await page.click("#recount-toggle");
    await fillRecount(page, RECOUNT);
    await checkAgain(page);
    await page.click("text=Change the entries");
    await checkFromClose(page);
    assert.equal(await page.isHidden("#recount-sheet"), true);
    assert.equal(await page.getAttribute("#recount-toggle", "aria-expanded"), "false");
    assert.equal(await page.inputValue('[data-field="recount.20.00"]'), "");
    assert.equal(await page.isHidden("#recount-compare"), true);
    console.log(`${engine}: a new check from Close a drawer clears the recount`);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
