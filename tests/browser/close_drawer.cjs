"use strict";

// Run through tests/test_web_browser.py, which owns the local test server.
const assert = require("node:assert/strict");
const { chromium, webkit } = require(process.env.DRAWERCHECK_PLAYWRIGHT_MODULE);
const [base, engine] = process.argv.slice(2);
const COUNTS = ["1", "3", "12", "6", "9", "0", "47", "0", "72", "35", "31", "60"];

async function fillDrawer(page, { paidOut = "32.50" } = {}) {
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
  await page.fill('[data-field="register_report.paid_outs"]', paidOut);
  await page.check("#drops-list");
  await page.fill("#drop-1-amount", "400.00");
  await page.click("#add-drop");
  await page.fill("#drop-2-amount", "400.00");
}

async function submit(page) {
  await page.click("#check-drawer");
  await page.waitForSelector("#close-summary:not([hidden]) li");
}

const problems = (page) => page.locator("#close-problems li").allInnerTexts();
const invalid = (page, selector) => page.getAttribute(selector, "aria-invalid");

async function describedBy(page, selector) {
  // The owner's description must name a visible message with the summary's words.
  return page.evaluate((selector) => {
    const ids = (document.querySelector(selector).getAttribute("aria-describedby") ?? "").split(" ");
    return ids.map((id) => document.getElementById(id)).filter((node) => node?.classList.contains("field-error"))
      .map((node) => node.textContent);
  }, selector);
}

async function fresh(browser) {
  const page = await browser.newPage();
  await page.goto(`${base}/#/close`);
  return page;
}

async function hiddenFieldErrorsClear(browser) {
  const page = await fresh(browser);
  await fillDrawer(page, { paidOut: "32.5" });
  await submit(page);
  assert.deepEqual(await problems(page), ["Enter paid out in dollars and cents, like 1316.40, without $ or commas."]);
  await page.check("#report-no");
  assert.equal(await page.isHidden("#close-summary"), true);
  assert.equal(await invalid(page, '[data-field="register_report.paid_outs"]'), null);
  assert.equal(await page.locator("#report-figures .field-error").count(), 0);
  assert.equal(await page.getAttribute('[data-field="register_report.paid_outs"]', "aria-describedby"), "money-hint");
  console.log(`${engine}: hiding the report figures clears their message and summary link`);
  await page.close();
}

async function choiceErrorsAreAssociated(browser) {
  const page = await fresh(browser);
  await page.click("#check-drawer");
  const words = await problems(page);
  assert.deepEqual(words, ["Choose whether you have the register report.", "Choose whether there were safe drops."]);
  for (const [group, text] of [["#report-group", words[0]], ["#drops-group", words[1]]]) {
    assert.equal(await invalid(page, group), "true");
    assert.deepEqual(await describedBy(page, group), [text]);
  }
  await page.check("#report-yes");
  assert.equal(await invalid(page, "#report-group"), null);
  assert.deepEqual(await problems(page), [words[1]]);
  console.log(`${engine}: choice-group messages are named by their fieldset and clear when answered`);

  await fillDrawer(page);
  await page.check("#times-missing");
  await submit(page);
  const times = "This version cannot check a drawer without its opening and closing times. Find the shift slip or the register report.";
  assert.deepEqual(await problems(page), [times]);
  assert.equal(await invalid(page, "#times-missing"), "true");
  assert.deepEqual(await describedBy(page, "#times-missing"), [times]);
  await page.click("#close-problems a");
  assert.equal(await page.evaluate(() => document.activeElement.id), "times-missing");
  await page.uncheck("#times-missing");
  assert.equal(await page.isHidden("#close-summary"), true);
  assert.equal(await invalid(page, "#times-missing"), null);
  console.log(`${engine}: the unavailable-times message is named by its checkbox and clears when unchecked`);
  await page.close();
}

async function removedDropsLeaveNoStaleErrors(browser) {
  const page = await fresh(browser);
  await fillDrawer(page);
  await page.fill("#drop-1-amount", "0.00");
  await page.fill("#drop-2-amount", "0.00");
  await submit(page);
  assert.equal((await problems(page)).length, 2);
  await page.click("text=Remove drop 1");
  assert.equal(await page.locator("#drop-rows [aria-invalid]").count(), 0);
  assert.equal(await page.locator("#drop-rows .field-error").count(), 0);
  assert.equal(await page.isHidden("#close-summary"), true);
  await page.fill("#drop-1-amount", "800.00");
  await page.click("#check-drawer");
  await page.waitForSelector("#review-body:not([hidden])");
  const outcome = await page.locator("#review-outcome dd").allInnerTexts();
  assert.deepEqual(outcome.slice(0, 3), ["$685.65", "$665.65", "-$20.00"]);
  console.log(`${engine}: removing a drop clears drop messages; the corrected drawer checks`);
  await page.close();
}

(async () => {
  const webkitPath = process.env.DRAWERCHECK_WEBKIT_EXECUTABLE;
  const browser = await (engine === "chrome"
    ? chromium.launch({ channel: "chrome" })
    : webkit.launch(webkitPath ? { executablePath: webkitPath } : {}));
  try {
    await hiddenFieldErrorsClear(browser);
    await choiceErrorsAreAssociated(browser);
    await removedDropsLeaveNoStaleErrors(browser);
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
