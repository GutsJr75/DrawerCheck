"use strict";

// Run through tests/test_web_browser.py, which owns the local test server.
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const os = require("node:os");
const path = require("node:path");
const { pathToFileURL } = require("node:url");
const { chromium, webkit } = require(process.env.DRAWERCHECK_PLAYWRIGHT_MODULE);
const [base, engine] = process.argv.slice(2);
const COUNTS = ["1", "3", "12", "6", "9", "0", "47", "0", "72", "35", "31", "60"];

async function downloadSheet(page, directory) {
  const ready = page.waitForEvent("download");
  await page.click("#download-closing");
  const download = await ready;
  assert.equal(download.suggestedFilename(), "drawercheck-closing-2026-11-02.html");
  // Playwright's internal download path has no .html suffix; save the real name.
  const saved = path.join(directory, download.suggestedFilename());
  await download.saveAs(saved);
  return { path: saved, content: await fs.readFile(saved, "utf8") };
}

(async () => {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), "drawercheck-sheet-"));
  const webkitPath = process.env.DRAWERCHECK_WEBKIT_EXECUTABLE;
  const browser = await (engine === "chrome"
    ? chromium.launch({ channel: "chrome" })
    : webkit.launch(webkitPath ? { executablePath: webkitPath } : {}));
  try {
    const page = await browser.newPage();
    await page.goto(`${base}/#/close`);
    for (const [field, value] of Object.entries({
      business_date: "2026-11-02", register_id: "R2", cashier_id: "cashier_02",
      opening_float: "200.00", opened_at: "2026-11-02T08:00", closed_at: "2026-11-02T20:00",
    })) await page.fill(`[data-field="${field}"]`, value);
    const counts = page.locator('[data-field^="counts."]');
    for (let i = 0; i < COUNTS.length; i += 1) await counts.nth(i).fill(COUNTS[i]);
    await page.check("#report-yes");
    for (const [field, value] of Object.entries({ cash_sales: "1316.40", cash_refunds: "18.25", paid_ins: "20.00", paid_outs: "32.50" })) {
      await page.fill(`[data-field="register_report.${field}"]`, value);
    }
    await page.check("#drops-list");
    await page.fill("#drop-1-amount", "800.00");
    await page.click("#check-drawer");
    await page.waitForSelector("#review-result:not([hidden])");
    const first = await downloadSheet(page, directory);
    assert.match(first.content, /-\$20\.00/);
    assert.match(first.content, /Missing verifier and variance note/);

    const note = "Reviewed <count> & kept the original figures.";
    await page.fill('[data-field="verifier_id"]', "manager_01");
    await page.fill('[data-field="variance_note"]', note);
    assert.equal(await page.isHidden("#download-closing"), true, "a stale result cannot be downloaded");
    await page.click("#check-again");
    await page.waitForSelector("#review-result:not([hidden])");
    const signed = await downloadSheet(page, directory);
    assert.match(signed.content, /supplied, not verified/);
    assert.match(signed.content, /Reviewed &lt;count&gt; &amp; kept/);
    assert.doesNotMatch(signed.content, /Missing verifier and variance note/);
    assert.doesNotMatch(first.content, /manager_01/);

    await page.click("#recount-toggle");
    const recount = page.locator('[data-field^="recount."]');
    for (let i = 0; i < COUNTS.length; i += 1) await recount.nth(i).fill(i === 2 ? "13" : COUNTS[i]);
    await page.click("#check-again");
    await page.waitForSelector("#review-result:not([hidden])");
    const recounted = await downloadSheet(page, directory);
    assert.match(recounted.content, /First count and recount/);
    assert.match(recounted.content, /-\$20\.00/);
    assert.match(recounted.content, /\$0\.00/);
    assert.match(recounted.content, /\$240\.00/);
    assert.match(recounted.content, /\$260\.00/);
    console.log(`${engine}: downloads preserve each checked snapshot, both counts, and unverified reviewer details`);

    const offline = await browser.newContext({ offline: true });
    const sheet = await offline.newPage();
    const requests = [];
    sheet.on("request", request => { if (/^https?:/.test(request.url())) requests.push(request.url()); });
    await sheet.goto(pathToFileURL(recounted.path).href);
    await sheet.getByRole("heading", { name: "Drawer closing sheet", exact: true }).waitFor();
    assert.match(await sheet.innerText("body"), /Repeated shortages: Not run/);
    assert.match(await sheet.innerText("body"), /Bank deposit to check: Not run/);
    assert.match(await sheet.innerText("body"), /Reviewed <count> & kept/);
    await sheet.emulateMedia({ media: "print" });
    assert.equal(await sheet.evaluate(() => getComputedStyle(document.querySelector("main")).marginTop), "0px");
    assert.deepEqual(requests, [], "the downloaded file must not request external resources");
    await offline.close();
    console.log(`${engine}: downloaded file opens offline and applies its print styles`);

    await page.click("text=Change the entries");
    await page.check("#report-no");
    await page.click("#check-drawer");
    await page.waitForSelector("#review-result:not([hidden])");
    const missing = await downloadSheet(page, directory);
    assert.match(missing.content, /Register report: not available/);
    assert.match(missing.content, /expected cash is unknown/);
    await page.fill('[data-field="variance_note"]', "Unsubmitted edit");
    assert.equal(await page.isHidden("#download-closing"), true);
  } finally {
    await browser.close();
    await fs.rm(directory, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
