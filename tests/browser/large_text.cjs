"use strict";

// Run through tests/test_web_browser.py, which owns the local test server.
const assert = require("node:assert/strict");
const { chromium, webkit } = require(process.env.DRAWERCHECK_PLAYWRIGHT_MODULE);
const [base, engine] = process.argv.slice(2);
const COUNTS = ["1", "3", "12", "6", "9", "0", "47", "0", "72", "35", "31", "60"];
const KEYS = ["100.00", "50.00", "20.00", "10.00", "5.00", "2.00", "1.00", "0.50", "0.25", "0.10", "0.05", "0.01"];

const enlarge = (page, size) => page.evaluate((value) => {
  document.documentElement.style.fontSize = value;
  return new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
}, size);

// Every count box must be fully inside its sheet, with nothing to scroll sideways.
async function sheetFits(page, sheetSelector, field) {
  return page.evaluate(({ sheetSelector, field }) => {
    const sheet = document.querySelector(sheetSelector);
    const box = sheet.getBoundingClientRect();
    const inputs = [...sheet.querySelectorAll(`[data-field^="${field}."]`)];
    return {
      inputs: inputs.length,
      outside: inputs.filter((input) => input.getBoundingClientRect().right > box.right + 1).length,
      sideways: sheet.scrollWidth - sheet.clientWidth,
      page: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      stacked: getComputedStyle(sheet.querySelector("th")).display === "block",
    };
  }, { sheetSelector, field });
}

async function checkSheet(page, sheetSelector, field, label) {
  assert.equal((await sheetFits(page, sheetSelector, field)).stacked, false, `${label}: two columns at normal text`);
  await enlarge(page, "200%");
  const fit = await sheetFits(page, sheetSelector, field);
  assert.deepEqual(fit, { inputs: 12, outside: 0, sideways: 0, page: 0, stacked: true }, `${label} at 200% text`);
  await enlarge(page, "");
}

(async () => {
  const webkitPath = process.env.DRAWERCHECK_WEBKIT_EXECUTABLE;
  const browser = await (engine === "chrome"
    ? chromium.launch({ channel: "chrome" })
    : webkit.launch(webkitPath ? { executablePath: webkitPath } : {}));
  try {
    const page = await browser.newPage({ viewport: { width: 320, height: 900 } });
    await page.goto(`${base}/#/close`);
    await checkSheet(page, "#view-close .entry-paper", "counts", "Close count sheet");
    console.log(`${engine}: the Close count sheet keeps every box on screen at 200% text in 320 px`);

    const payload = {
      business_date: "2026-11-02", register_id: "R2", cashier_id: "cashier_02",
      opened_at: "2026-11-02T08:00", closed_at: "2026-11-02T20:00", opening_float: "200.00",
      counts: Object.fromEntries(KEYS.map((key, index) => [key, COUNTS[index]])), recount: null,
      register_report: { cash_sales: "1316.40", cash_refunds: "18.25", paid_ins: "20.00", paid_outs: "32.50" },
      safe_drops: [{ amount: "800.00", bag_number: "" }], verifier_id: "", variance_note: "",
    };
    const counts = page.locator('[data-field^="counts."]');
    for (let index = 0; index < 12; index += 1) await counts.nth(index).fill(COUNTS[index]);
    for (const [field, value] of [["business_date", "2026-11-02"], ["register_id", "R2"], ["cashier_id", "cashier_02"],
      ["opening_float", "200.00"], ["opened_at", "2026-11-02T08:00"], ["closed_at", "2026-11-02T20:00"]]) {
      await page.fill(`[data-field="${field}"]`, value);
    }
    await page.check("#report-no");
    await page.check("#drops-none");
    await page.click("#check-drawer");
    await page.waitForSelector("#review-result:not([hidden])");
    await page.click("#recount-toggle");
    await checkSheet(page, "#recount-sheet", "recount", "Recount sheet");
    console.log(`${engine}: the recount sheet keeps every box on screen at 200% text in 320 px`);

    // The downloadable sheet must follow the reader's text size, not fixed pixels.
    // A downloaded sheet opens on its own, outside the site's style policy, so it
    // gets a fresh blank page; on the site's page its inline styles would be blocked.
    const response = await page.request.post(`${base}/api/drawer`, { data: payload });
    const content = (await response.json()).closing_summary.content;
    await page.close();
    const sheet = await browser.newPage({ viewport: { width: 320, height: 900 } });
    await sheet.setContent(content);
    const bodySize = () => sheet.evaluate(() => parseFloat(getComputedStyle(document.body).fontSize));
    const normal = await bodySize();
    assert.equal(normal, 15, "the sheet's own styles apply");
    await enlarge(sheet, "200%");
    assert.equal(await bodySize(), normal * 2, "closing sheet text doubles at 200%");
    const overflow = await sheet.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    assert.equal(overflow, 0, "closing sheet page fits 320 px at 200% text");
    const unnamed = await sheet.evaluate(() => [...document.querySelectorAll("body *")].filter((node) =>
      ["auto", "scroll"].includes(getComputedStyle(node).overflowX) && node.scrollWidth > node.clientWidth + 1
      && node.getAttribute("role") !== "region").length);
    assert.equal(unnamed, 0, "only named regions scroll sideways");
    // The report frame hides overflow, so wide content would be cut off without a scrollbar.
    const clipped = await sheet.evaluate(() => [...document.querySelectorAll("body *")].filter((node) => {
      const style = getComputedStyle(node);
      return ["hidden", "clip"].includes(style.overflowX) && node.scrollWidth > node.clientWidth + 1;
    }).map((node) => node.tagName.toLowerCase()));
    assert.deepEqual(clipped, [], "nothing is cut off at 200% text");
    console.log(`${engine}: the closing sheet's text doubles at 200% and fits 320 px`);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
