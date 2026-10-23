// DrawerCheck page behaviour. Python does every calculation and file check;
// this script only switches views, tracks chosen files, and sends requests.
// Text from the server is always inserted with textContent, never as HTML.
"use strict";

(() => {
  const maxUploadBytes = Number(document.body.dataset.maxUploadBytes);
  const views = {
    start: document.getElementById("view-start"),
    prepare: document.getElementById("view-prepare"),
    results: document.getElementById("view-results"),
    drawer: document.getElementById("view-drawer"),
  };
  const announcer = document.getElementById("announcer");
  const startError = document.getElementById("start-error");
  const tryExample = document.getElementById("try-example");
  const fileInput = document.getElementById("file-input");
  const chooserNotes = document.getElementById("chooser-notes");
  const filesProgress = document.getElementById("files-progress");
  const checkFiles = document.getElementById("check-files");
  const errorSummary = document.getElementById("error-summary");
  const errorList = document.getElementById("error-list");
  const resultsRange = document.getElementById("results-range");
  const severityChips = document.getElementById("severity-chips");
  const leadList = document.getElementById("lead-list");
  const noLeads = document.getElementById("no-leads");
  const dayDetails = document.getElementById("day-details");
  const cashierDetails = document.getElementById("cashier-details");
  const drawerHeading = document.getElementById("drawer-heading");
  const drawerAbout = document.getElementById("drawer-about");
  const drawerGrid = document.getElementById("drawer-grid");
  const drawerTape = document.querySelector('[data-tape="drawer"]');
  const tapeNote = document.getElementById("tape-note");
  const countSheet = document.getElementById("count-sheet");
  const countMissing = document.getElementById("count-missing");
  const drawerLeads = document.getElementById("drawer-leads");
  const drawerNoLeads = document.getElementById("drawer-no-leads");
  const dayLeadsBlock = document.getElementById("day-leads-block");
  const dayLeads = document.getElementById("day-leads");
  const limitsText = document.getElementById("limits-text");
  const depositText = document.getElementById("deposit-text");
  const severityOrder = ["review", "warn", "info"];
  const severityClass = { review: "status-review", warn: "status-check", info: "status-note" };
  // Business dates are calendar days; formatting in UTC keeps them from shifting.
  const dateFormat = new Intl.DateTimeFormat("en-US", { dateStyle: "long", timeZone: "UTC" });
  let results = null;
  let shiftsByCode = new Map();
  const rows = new Map(
    [...document.querySelectorAll("[data-file]")].map((row) => [row.dataset.file, row]),
  );
  const chosen = new Map();
  const problemFiles = new Set();
  const fileStatus = {
    waiting: ["Waiting", "status-waiting"],
    ready: ["Ready", "status-ready"],
    problem: ["Problem", "status-problem"],
  };
  let busy = false;

  function fill(template, values) {
    return template.replace(/\{(\w+)\}/g, (placeholder, key) =>
      key in values ? String(values[key]) : placeholder,
    );
  }

  function message(name, values = {}) {
    // Wording lives in errors.py and reaches the page through the template.
    return fill(document.querySelector(`[data-message="${name}"]`).textContent, values);
  }

  function announce(text) {
    // Clearing first lets screen readers announce a repeated message again.
    announcer.textContent = "";
    window.setTimeout(() => {
      announcer.textContent = text;
    }, 50);
  }

  function showView(name) {
    for (const [key, view] of Object.entries(views)) {
      view.hidden = key !== name;
    }
    if (name === "start") {
      // An old example failure should not greet a visitor who comes back later.
      startError.textContent = "";
    }
    document.title = views[name].dataset.title;
    views[name].querySelector("h1").focus();
  }

  function formatSize(bytes) {
    if (bytes < 1000) {
      return `${bytes} ${bytes === 1 ? "byte" : "bytes"}`;
    }
    if (bytes < 1000000) {
      return `${(bytes / 1000).toFixed(1)} KB`;
    }
    return `${(bytes / 1000000).toFixed(2)} MB`;
  }

  async function send(url, body) {
    // Resolves to {payload} on success, or {error, status} for anything else.
    let response;
    try {
      response = await fetch(url, { method: "POST", body });
    } catch {
      return { error: { message: message("network") }, status: 0 };
    }
    let data = null;
    try {
      data = await response.json();
    } catch {
      data = null;
    }
    if (response.ok && data) {
      return { payload: data };
    }
    const error =
      data && data.error && typeof data.error.message === "string"
        ? data.error
        : { message: message("unavailable") };
    return { error, status: response.status };
  }

  async function run(button, url, body) {
    // aria-disabled keeps keyboard focus on the button while it is busy.
    busy = true;
    const idleText = button.textContent;
    button.textContent = button.dataset.busyText;
    button.setAttribute("aria-disabled", "true");
    announce(button.dataset.busyText);
    try {
      return await send(url, body);
    } finally {
      busy = false;
      button.textContent = idleText;
      button.removeAttribute("aria-disabled");
    }
  }

  function element(tag, className = "", text = undefined) {
    const node = document.createElement(tag);
    if (className) {
      node.className = className;
    }
    if (text !== undefined) {
      node.textContent = text;
    }
    return node;
  }

  function formatDate(isoDate) {
    return dateFormat.format(new Date(`${isoDate}T00:00:00Z`));
  }

  function clockTime(timestamp, businessDate) {
    // Show only the time, plus the date when a shift crosses midnight.
    const time = timestamp.slice(11, 16);
    const day = timestamp.slice(0, 10);
    return day === businessDate ? time : `${formatDate(day)} ${time}`;
  }

  function amountCell(value) {
    // Amounts arrive formatted from Python; "unknown" and other words stay in the body font.
    return element("td", /^-?\$/.test(value) ? "number money" : "number", value);
  }

  function levelLabel(severity) {
    return element("span", `status ${severityClass[severity]}`, results.labels.severities[severity]);
  }

  function worstSeverity(flags) {
    return severityOrder.find((severity) => flags.some((flag) => flag.severity === severity));
  }

  function sortLeads(flags) {
    // Needs review first, then by date and drawer; the server's order is kept otherwise.
    return [...flags].sort(
      (first, second) =>
        severityOrder.indexOf(first.severity) - severityOrder.indexOf(second.severity) ||
        first.business_date.localeCompare(second.business_date) ||
        (first.shift_code ?? "").localeCompare(second.shift_code ?? ""),
    );
  }

  function leadItem(flag, shiftCode, openable) {
    const item = element("li", "lead-item");
    const level = element("div", "lead-level");
    level.append(levelLabel(flag.severity));
    const body = element("div", "lead-body");
    const place = shiftCode
      ? fill(leadList.dataset.drawerTemplate, { code: shiftCode })
      : leadList.dataset.wholeDay;
    body.append(
      element("h3", "lead-title", results.labels.rules[flag.rule_code] ?? flag.rule_code),
      element("p", "lead-message", flag.message),
      element(
        "p",
        "lead-meta",
        `${formatDate(flag.business_date)}. ${place}. ${fill(leadList.dataset.ruleTemplate, { code: flag.rule_code })}.`,
      ),
    );
    item.append(level, body);
    if (openable && shiftCode && shiftsByCode.has(shiftCode)) {
      const open = element("button", "link-button lead-open", leadList.dataset.openText);
      open.type = "button";
      open.append(element("span", "visually-hidden", ` ${shiftCode}`));
      open.addEventListener("click", () => openDrawer(shiftCode));
      item.append(open);
    }
    return item;
  }

  function renderFacts() {
    for (const number of views.results.querySelectorAll("[data-fact]")) {
      const count = results.summary[number.dataset.fact];
      const label = number.nextElementSibling;
      number.textContent = count.toLocaleString("en-US");
      label.textContent = count === 1 ? label.dataset.one : label.dataset.many;
    }
    severityChips.replaceChildren(
      ...severityOrder.map((severity, index) => {
        const chip = element("span", "severity-count");
        chip.append(
          levelLabel(severity),
          ` ${results.summary.leads_by_severity[severity].toLocaleString("en-US")}`,
        );
        if (index < severityOrder.length - 1) {
          // Spoken separator; the gap between labels is enough on screen.
          chip.append(element("span", "visually-hidden", ","));
        }
        return chip;
      }),
    );
  }

  function fillDayTable() {
    const table = document.getElementById("day-table");
    for (const header of table.querySelectorAll("[data-status]")) {
      header.textContent = results.labels.statuses[header.dataset.status];
    }
    table.tBodies[0].replaceChildren(
      ...results.days.map((day) => {
        const row = element("tr");
        const date = element("th", "", formatDate(day.business_date));
        date.scope = "row";
        row.append(
          date,
          ...[day.shifts, day.balanced, day.over, day.short, day.incomplete, day.open].map(
            (count) => element("td", "number", count.toLocaleString("en-US")),
          ),
          amountCell(day.expected_deposit_amount),
        );
        return row;
      }),
    );
  }

  function fillCashierTable() {
    const table = document.getElementById("cashier-table");
    table.tBodies[0].replaceChildren(
      ...results.cashiers.map((cashier) => {
        const row = element("tr");
        const id = element("th", "", cashier.cashier_id);
        id.scope = "row";
        row.append(
          id,
          element("td", "", cashier.display_name),
          element("td", "number", cashier.shifts.toLocaleString("en-US")),
          amountCell(cashier.over_amount),
          amountCell(cashier.short_amount),
          amountCell(cashier.net_amount),
          element("td", "number", cashier.incomplete.toLocaleString("en-US")),
          element("td", "number", cashier.open.toLocaleString("en-US")),
        );
        return row;
      }),
    );
  }

  function showResults(payload) {
    results = payload;
    shiftsByCode = new Map(payload.shifts.map((item) => [item.shift.shift_code, item]));
    resultsRange.textContent = fill(resultsRange.dataset.template, {
      from: formatDate(payload.from_date),
      to: formatDate(payload.to_date),
    });
    renderFacts();
    const leads = sortLeads(payload.flags);
    leadList.replaceChildren(...leads.map((flag) => leadItem(flag, flag.shift_code, true)));
    leadList.hidden = leads.length === 0;
    noLeads.hidden = leads.length > 0;
    // The day and cashier tables fill when first opened, so large uploads show quickly.
    for (const details of [dayDetails, cashierDetails]) {
      details.open = false;
      details.dataset.filled = "";
      details.querySelector("tbody").replaceChildren();
    }
    showView("results");
    announce(views.results.dataset.announce);
  }

  function renderDrawer(item) {
    const { shift } = item;
    const unknown = drawerGrid.dataset.unknown;
    const pos = shift.pos;
    drawerHeading.textContent = fill(drawerHeading.dataset.template, { code: shift.shift_code });
    const about = fill(drawerAbout.dataset.template, {
      register: shift.register_id,
      date: formatDate(shift.business_date),
      cashier: shift.cashier_id,
    });
    const opened = clockTime(shift.opened_at, shift.business_date);
    const times = shift.closed_at
      ? fill(drawerAbout.dataset.times, {
          opened,
          closed: clockTime(shift.closed_at, shift.business_date),
        })
      : fill(drawerAbout.dataset.stillOpen, { opened });
    drawerAbout.textContent = `${about} ${times}`;

    const amounts = {
      opening_float: shift.opening_float_amount,
      cash_sales: pos ? pos.cash_sales_amount : unknown,
      paid_ins: pos ? pos.paid_ins_amount : unknown,
      cash_refunds: pos ? pos.cash_refunds_amount : unknown,
      paid_outs: pos ? pos.paid_outs_amount : unknown,
      safe_drops: shift.safe_drops_amount,
      expected: item.expected_amount,
      counted: item.counted_amount,
      difference: item.variance_amount,
    };
    for (const [line, value] of Object.entries(amounts)) {
      drawerTape.querySelector(`[data-line="${line}"] td`).textContent = value;
    }
    // Each drawer opens with its line meanings closed.
    for (const term of drawerTape.querySelectorAll("details")) {
      term.open = false;
    }
    drawerTape.querySelector('[data-role="word"]').textContent =
      results.labels.statuses[item.status];
    const level = drawerTape.querySelector('[data-role="level"]');
    const worst = worstSeverity(item.flags);
    // A drawer without leads clears the label rather than hiding the last one.
    level.hidden = !worst;
    level.className = worst ? `status ${severityClass[worst]}` : "status";
    level.textContent = worst ? results.labels.severities[worst] : "";

    const notes = [];
    if (item.status === "open") {
      notes.push(tapeNote.dataset.open);
    } else {
      if (!pos) {
        notes.push(tapeNote.dataset.noPos);
      }
      if (shift.counts.length === 0) {
        notes.push(tapeNote.dataset.noCount);
      }
    }
    tapeNote.textContent = notes.join(" ");
    tapeNote.hidden = notes.length === 0;

    countSheet.tBodies[0].replaceChildren(
      ...shift.counts.map((count) => {
        const row = element("tr");
        // The bill or coin labels its row, so it lines up with its heading on the left.
        const denomination = element("th", "money", count.denomination);
        denomination.scope = "row";
        row.append(
          denomination,
          element("td", "number", count.quantity.toLocaleString("en-US")),
          amountCell(count.line_total_amount),
        );
        return row;
      }),
    );
    document.getElementById("count-total").textContent = item.counted_amount;
    countSheet.closest(".sheet-paper").hidden = shift.counts.length === 0;
    countMissing.hidden = shift.counts.length > 0;
    countMissing.textContent =
      item.status === "open" ? countMissing.dataset.open : countMissing.dataset.none;

    drawerLeads.replaceChildren(
      ...sortLeads(item.flags).map((flag) => leadItem(flag, shift.shift_code, false)),
    );
    drawerLeads.hidden = item.flags.length === 0;
    drawerNoLeads.hidden = item.flags.length > 0;
    dayLeads.replaceChildren(...sortLeads(item.daily_flags).map((flag) => leadItem(flag, "", false)));
    dayLeadsBlock.hidden = item.daily_flags.length === 0;

    limitsText.textContent =
      item.review_threshold_amount === unknown
        ? fill(limitsText.dataset.unknown, { tolerance: item.within_tolerance_amount })
        : fill(limitsText.dataset.template, {
            tolerance: item.within_tolerance_amount,
            review: item.review_threshold_amount,
          });
    depositText.textContent = depositSentence(item, unknown);
  }

  function depositSentence(item, unknown) {
    // Python leaves a drawer's share blank whenever its whole day is incomplete,
    // so the sentence names the actual reason, checked in this order.
    if (item.status === "open") {
      return depositText.dataset.open;
    }
    if (item.counted_amount === unknown) {
      return depositText.dataset.noCount;
    }
    if (item.deposit_contribution_amount === unknown) {
      return depositText.dataset.dayIncomplete;
    }
    return fill(depositText.dataset.template, {
      contribution: item.deposit_contribution_amount,
      date: formatDate(item.shift.business_date),
      counted: item.counted_amount,
      drops: item.shift.safe_drops_amount,
      retained: item.retained_float_amount,
      daily: item.daily_deposit_amount,
    });
  }

  function openDrawer(shiftCode) {
    renderDrawer(shiftsByCode.get(shiftCode));
    views.drawer.dataset.title = fill(views.drawer.dataset.titleTemplate, { code: shiftCode });
    showView("drawer");
  }

  function setRow(name, state, detail = "") {
    const row = rows.get(name);
    const status = row.querySelector('[data-role="status"]');
    const [label, className] = fileStatus[state];
    status.textContent = label;
    status.className = `status ${className}`;
    row.querySelector('[data-role="size"]').textContent = state === "ready" ? detail : "";
    const problem = row.querySelector('[data-role="problem"]');
    problem.textContent = state === "problem" ? detail : "";
    problem.hidden = state !== "problem";
    if (state === "problem") {
      problemFiles.add(name);
    } else {
      problemFiles.delete(name);
    }
    // A chosen file that the server reported a problem with is not ready.
    filesProgress.textContent = fill(filesProgress.dataset.template, {
      ready: chosen.size - problemFiles.size,
      total: rows.size,
    });
  }

  function hideErrorSummary() {
    errorSummary.hidden = true;
    errorList.replaceChildren();
  }

  function showErrorSummary(problems) {
    errorList.replaceChildren(
      ...problems.map(({ text, target }) => {
        const item = document.createElement("li");
        if (!target) {
          item.textContent = text;
          return item;
        }
        const link = document.createElement("a");
        link.href = `#${target.id}`;
        link.textContent = text;
        link.addEventListener("click", (event) => {
          // Move focus without changing the address, which belongs to views.
          event.preventDefault();
          target.focus();
        });
        item.append(link);
        return item;
      }),
    );
    errorSummary.hidden = false;
    errorSummary.focus();
  }

  function addFiles(files) {
    hideErrorSummary();
    chooserNotes.replaceChildren();
    const names = [...rows.keys()];
    for (const file of files) {
      if (rows.has(file.name)) {
        chosen.set(file.name, file);
        setRow(file.name, "ready", formatSize(file.size));
        continue;
      }
      const expected = names.find((name) => name.toLowerCase() === file.name.toLowerCase());
      const note = document.createElement("p");
      note.textContent = expected
        ? message("rename", { name: file.name, expected })
        : message("unknown_name", { name: file.name });
      chooserNotes.append(note);
    }
  }

  for (const button of document.querySelectorAll("[data-go]")) {
    button.addEventListener("click", () => {
      if (!busy) {
        showView(button.dataset.go);
      }
    });
  }

  dayDetails.addEventListener("toggle", () => {
    if (dayDetails.open && !dayDetails.dataset.filled) {
      fillDayTable();
      dayDetails.dataset.filled = "yes";
    }
  });

  cashierDetails.addEventListener("toggle", () => {
    if (cashierDetails.open && !cashierDetails.dataset.filled) {
      fillCashierTable();
      cashierDetails.dataset.filled = "yes";
    }
  });

  tryExample.addEventListener("click", async () => {
    if (busy) {
      return;
    }
    startError.textContent = "";
    const outcome = await run(tryExample, "/api/demo");
    if (outcome.payload) {
      showResults(outcome.payload);
    } else {
      startError.textContent = outcome.error.message;
    }
  });

  fileInput.addEventListener("change", () => {
    addFiles([...fileInput.files]);
    // Clearing the input lets the same file be chosen again after it is edited.
    fileInput.value = "";
  });

  checkFiles.addEventListener("click", async () => {
    if (busy) {
      return;
    }
    // The browser checks only names, the number of files, and their total size.
    const problems = [];
    let totalBytes = 0;
    for (const [name, row] of rows) {
      const file = chosen.get(name);
      if (file) {
        totalBytes += file.size;
      } else {
        problems.push({ text: message("missing", { name }), target: row });
      }
    }
    if (totalBytes > maxUploadBytes) {
      problems.push({
        text: message("too_large", {
          size: formatSize(totalBytes),
          limit: formatSize(maxUploadBytes),
        }),
        target: fileInput,
      });
    }
    if (problems.length > 0) {
      showErrorSummary(problems);
      return;
    }
    hideErrorSummary();
    // Rows describe the latest attempt, so earlier problems clear before resending.
    for (const name of [...problemFiles]) {
      setRow(name, "ready", formatSize(chosen.get(name).size));
    }
    const form = new FormData();
    for (const name of rows.keys()) {
      form.append("files", chosen.get(name), name);
    }
    const outcome = await run(checkFiles, "/api/check", form);
    if (outcome.payload) {
      showResults(outcome.payload);
      return;
    }
    const { error, status } = outcome;
    const row = error.file_name ? rows.get(error.file_name) : undefined;
    if (row) {
      setRow(error.file_name, "problem", error.message);
    }
    // Input problems point at the file or the chooser; server outages point nowhere.
    const target = row ?? (status === 400 || status === 413 ? fileInput : null);
    showErrorSummary([{ text: error.message, target }]);
  });
})();
