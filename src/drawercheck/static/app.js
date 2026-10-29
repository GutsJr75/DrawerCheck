"use strict";

(() => {
  const body = document.body;
  const maxUploadBytes = Number(body.dataset.maxUploadBytes);
  const views = {
    start: document.getElementById("view-start"),
    prepare: document.getElementById("view-prepare"),
    results: document.getElementById("view-results"),
    drawer: document.getElementById("view-drawer"),
    missing: document.getElementById("view-missing"),
  };
  const announcer = document.getElementById("announcer");
  const notSaved = document.getElementById("not-saved");
  const startError = document.getElementById("start-error");
  const startCancel = document.getElementById("start-cancel");
  const startSlow = document.getElementById("start-slow");
  const tryExample = document.getElementById("try-example");
  const fileInput = document.getElementById("file-input");
  const fileDrop = document.getElementById("file-drop");
  const chooserNotes = document.getElementById("chooser-notes");
  const filesProgress = document.getElementById("files-progress");
  const checkFiles = document.getElementById("check-files");
  const prepareError = document.getElementById("prepare-error");
  const prepareCancel = document.getElementById("prepare-cancel");
  const prepareSlow = document.getElementById("prepare-slow");
  const errorSummary = document.getElementById("error-summary");
  const errorList = document.getElementById("error-list");
  const resultsRange = document.getElementById("results-range");
  const summaryTick = document.getElementById("summary-tick");
  summaryTick.addEventListener("animationend", () => summaryTick.classList.add("drawn"));
  const severityChips = document.getElementById("severity-chips");
  const filters = document.getElementById("filters");
  const dateSelect = document.getElementById("filter-date");
  const filterLevel = document.getElementById("filter-level");
  const filterStatus = document.getElementById("filter-status");
  const leadList = document.getElementById("lead-list");
  const noLeads = document.getElementById("no-leads");
  const noMatches = document.getElementById("no-matches");
  const drawerHeading = document.getElementById("drawer-heading");
  const drawerAbout = document.getElementById("drawer-about");
  const drawerGrid = document.getElementById("drawer-grid");
  const drawerTape = document.querySelector('[data-tape="drawer"]');
  const tapeNote = document.getElementById("tape-note");
  const countSheet = document.getElementById("count-sheet");
  const countToggle = document.getElementById("count-toggle");
  const nextDrawer = document.getElementById("next-drawer");
  const countMissing = document.getElementById("count-missing");
  const drawerLeads = document.getElementById("drawer-leads");
  const drawerNoLeads = document.getElementById("drawer-no-leads");
  const dayLeadsBlock = document.getElementById("day-leads-block");
  const dayLeads = document.getElementById("day-leads");
  const limitsText = document.getElementById("limits-text");
  const depositText = document.getElementById("deposit-text");
  const missingCode = document.getElementById("missing-code");
  const severityOrder = ["review", "warn", "info"];
  const severityClass = { review: "status-review", warn: "status-check", info: "status-note" };
  const showSeverity = { all: null, review: "review", check: "warn", note: "info" };
  let results = null;
  let sortedLeads = [];
  let drawerGroups = new Map();
  let reviewOrder = [];
  let leadDates = new Set();
  let shiftsByCode = new Map();
  let shiftsByDate = new Map();
  let request = null;
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

  function fill(template, values) {
    return template.replace(/\{(\w+)\}/g, (placeholder, key) =>
      key in values ? String(values[key]) : placeholder,
    );
  }

  function message(name, values = {}) {
    return fill(document.querySelector(`[data-message="${name}"]`).textContent, values);
  }

  function announce(text) {
    // Clearing first lets screen readers announce a repeated message again.
    announcer.textContent = "";
    window.setTimeout(() => {
      announcer.textContent = text;
    }, 50);
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

  function link(text, href, className = "") {
    const anchor = element("a", className, text);
    anchor.href = href;
    return anchor;
  }

  function formatDate(isoDate) {
    return results.labels.dates[isoDate];
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

  function drawerAddress(code) {
    return `#/drawer/${encodeURIComponent(code)}`;
  }

  function resultsAddress(date, show) {
    const query = new URLSearchParams();
    if (date) {
      query.set("date", date);
    }
    if (show !== "all") {
      query.set("show", show);
    }
    const text = query.toString();
    return text ? `#/results?${text}` : "#/results";
  }

  function parseAddress(hash) {
    if (hash === "" || hash === "#") {
      return { view: "start" };
    }
    if (!hash.startsWith("#/")) {
      // Other hashes, such as the skip link's #main, are not views.
      return null;
    }
    const [path, query = ""] = hash.slice(2).split("?");
    if (path === "") {
      return { view: "start" };
    }
    if (path === "prepare") {
      return { view: "prepare" };
    }
    if (path === "results") {
      return { view: "results", params: new URLSearchParams(query) };
    }
    if (path.startsWith("drawer/")) {
      try {
        return { view: "drawer", code: decodeURIComponent(path.slice("drawer/".length)) };
      } catch {
        return { view: "start", unknown: true };
      }
    }
    return { view: "start", unknown: true };
  }

  function navigate(hash) {
    if (location.hash === hash) {
      route();
    } else {
      location.hash = hash;
    }
  }

  function showView(name, { focus = true } = {}) {
    for (const [key, view] of Object.entries(views)) {
      view.hidden = key !== name;
    }
    if (name === "start") {
      clearRequestError(startError);
    }
    document.title = views[name].dataset.title;
    if (focus) {
      views[name].querySelector("h1").focus();
    }
  }

  function route({ initial = false } = {}) {
    const address = parseAddress(location.hash);
    if (!address) {
      if (initial) {
        showView("start", { focus: false });
      }
      return;
    }
    if (request && request.view !== address.view) {
      // Leaving the view stops waiting; a late answer is ignored.
      stopWaiting(request, "left");
    }
    notSaved.hidden = true;
    if (address.unknown) {
      history.replaceState(null, "", "#/");
    }
    if ((address.view === "results" || address.view === "drawer") && !results) {
      history.replaceState(null, "", "#/");
      notSaved.hidden = false;
      showView("start", { focus: !initial });
      return;
    }
    if (address.view === "results") {
      applyFilters(address.params);
    } else if (address.view === "drawer") {
      const item = shiftsByCode.get(address.code);
      if (!item) {
        missingCode.textContent = fill(missingCode.dataset.template, { code: address.code });
        showView("missing", { focus: !initial });
        return;
      }
      renderDrawer(item);
      views.drawer.dataset.title = fill(views.drawer.dataset.titleTemplate, {
        title: drawerHeading.textContent,
      });
    }
    showView(address.view, { focus: !initial });
  }

  async function send(url, requestBody, signal) {
    let response;
    try {
      response = await fetch(url, { method: "POST", body: requestBody, signal });
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

  function stopWaiting(current, reason) {
    if (current.stopped) {
      return;
    }
    current.stopped = reason;
    current.controller.abort();
    current.finish({ stopped: reason });
  }

  async function run({ button, cancel, slow, view, url, requestBody }) {
    // aria-disabled keeps keyboard focus on the button while it is busy.
    let finish;
    const stoppedEarly = new Promise((resolve) => {
      finish = resolve;
    });
    const current = { controller: new AbortController(), view, stopped: "", finish };
    request = current;
    const idleText = button.textContent;
    button.textContent = button.dataset.busyText;
    button.setAttribute("aria-disabled", "true");
    cancel.hidden = false;
    announce(button.dataset.busyText);
    const slowTimer = window.setTimeout(() => {
      slow.hidden = false;
      announce(slow.textContent);
    }, Number(body.dataset.slowNoticeMs));
    const giveUpTimer = window.setTimeout(
      () => stopWaiting(current, "timeout"),
      Number(body.dataset.giveUpMs),
    );
    try {
      const outcome = await Promise.race([
        send(url, requestBody, current.controller.signal),
        stoppedEarly,
      ]);
      return current.stopped ? { stopped: current.stopped } : outcome;
    } finally {
      window.clearTimeout(slowTimer);
      window.clearTimeout(giveUpTimer);
      if (request === current) {
        request = null;
      }
      button.textContent = idleText;
      button.removeAttribute("aria-disabled");
      cancel.hidden = true;
      slow.hidden = true;
    }
  }

  function clearRequestError(box) {
    box.replaceChildren();
  }

  function showRequestError(box, text, retry) {
    const again = element("button", "button button-secondary", box.dataset.retry);
    again.type = "button";
    again.addEventListener("click", retry);
    box.replaceChildren(element("p", "", text), again);
  }

  function handledStop(outcome, button, box, retry) {
    if (["cancel", "changed"].includes(outcome.stopped)) {
      announce(announcer.dataset.stopped);
      if (outcome.stopped === "cancel") button.focus();
    } else if (outcome.stopped === "timeout") {
      showRequestError(box, message("timeout"), retry);
    }
    return Boolean(outcome.stopped);
  }

  function amountCell(value) {
    return element("td", /^-?\$/.test(value) ? "number money" : "number", value);
  }

  function levelLabel(severity) {
    return element("span", `status ${severityClass[severity]}`, results.labels.severities[severity]);
  }

  function worstSeverity(flags) {
    return severityOrder.find((severity) => flags.some((flag) => flag.severity === severity));
  }

  function sortLeads(flags) {
    return [...flags].sort(
      (first, second) =>
        severityOrder.indexOf(first.severity) - severityOrder.indexOf(second.severity) ||
        first.business_date.localeCompare(second.business_date) ||
        (first.shift_code ?? "").localeCompare(second.shift_code ?? ""),
    );
  }

  function groupLeads(flags, key) {
    const groups = new Map();
    for (const flag of flags) {
      if (!groups.has(flag[key])) groups.set(flag[key], []);
      groups.get(flag[key]).push(flag);
    }
    return groups;
  }

  function leadRow(flag, scope) {
    const row = element("li", scope === "drawer" ? "lead-item" : "group-lead");
    const content = element("div", "lead-body");
    content.append(
      element("strong", "lead-title", results.labels.rules[flag.rule_code] ?? flag.rule_code),
      element("p", "lead-message", flag.message),
    );
    if (scope === "day") {
      const detail = element("details", "help rule-detail");
      detail.append(element("summary", "", leadList.dataset.ruleLabel), element("p", "", flag.rule_code));
      content.append(detail);
    } else if (scope === "drawer") {
      content.append(element("p", "lead-meta", flag.limit_text),
        element("p", "lead-meta", fill(leadList.dataset.ruleTemplate, { code: flag.rule_code })));
    }
    row.append(levelLabel(flag.severity), content);
    return row;
  }

  function drawerGroup(code, flags) {
    const item = shiftsByCode.get(code);
    const row = element("li", "drawer-group");
    row.dataset.drawer = code;
    const heading = element("div", "group-heading");
    const title = element("h4");
    const open = link(fill(leadList.dataset.title, {
      register: item.shift.register_id, date: formatDate(item.shift.business_date),
    }), drawerAddress(code), "drawer-title");
    open.append(element("span", "visually-hidden", ` ${code}`));
    title.append(open);
    const about = element("div");
    about.append(title, element("p", "lead-meta", fill(leadList.dataset.drawerTemplate, { code })),
      levelLabel(worstSeverity(drawerGroups.get(code))));
    const outcome = element("p", "group-outcome");
    outcome.append(
      element("span", "hint", leadList.dataset.difference),
      element("strong", /^-?\$/.test(item.variance_amount) ? "money" : "", item.variance_amount),
      element("span", "", results.labels.statuses[item.status]),
    );
    heading.append(about, outcome);
    const leads = element("ul", "group-leads");
    leads.append(...flags.map(flag => leadRow(flag, "group")));
    row.append(heading, leads);
    return row;
  }

  function dayGroup(date, flags) {
    const row = element("li", "drawer-group");
    row.dataset.day = date;
    row.append(element("h4", "", formatDate(date)));
    const leads = element("ul", "group-leads");
    leads.append(...flags.map(flag => leadRow(flag, "day")));
    row.append(leads);
    const codes = shiftsByDate.get(date) ?? [];
    if (codes.length) {
      const drawers = element("p", "lead-drawers", `${fill(leadList.dataset.dayDrawers, { date: formatDate(date) })} `);
      drawers.append(...codes.map(code => link(code, drawerAddress(code))));
      row.append(drawers);
    }
    return row;
  }

  function renderGroups(shown, filtered) {
    const matching = groupLeads(shown.filter(flag => flag.shift_id !== null), "shift_code");
    const days = groupLeads(shown.filter(flag => flag.shift_id === null), "business_date");
    const ordered = [...drawerGroups.keys()].filter(code => matching.has(code));
    reviewOrder = ordered;
    leadList.replaceChildren();
    function section(label, rows, count, unit) {
      if (!rows.length) return;
      const panel = element("div", "lead-section");
      const title = element("h3", "", filtered ? label : fill(leadList.dataset[unit], {
        level: label, count: count.toLocaleString("en-US"),
        unit: leadList.dataset[unit + (count === 1 ? "One" : "Many")],
      }));
      const list = element("ol", "group-list");
      list.append(...rows);
      panel.append(title, list);
      leadList.append(panel);
    }
    const dayRows = [...days].sort(([first], [second]) => first.localeCompare(second)).map(([date, flags]) => dayGroup(date, flags));
    if (filtered) {
      section(leadList.dataset.matching, ordered.map(code => drawerGroup(code, matching.get(code))));
      section(leadList.dataset.wholeDay, dayRows);
    } else {
      for (const severity of severityOrder) {
        const codes = ordered.filter(code => worstSeverity(drawerGroups.get(code)) === severity);
        section(results.labels.severities[severity],
          codes.map(code => drawerGroup(code, matching.get(code))),
          results.summary.drawers_by_highest_severity[severity], "drawers");
        if (severity === "review") section(leadList.dataset.wholeDay, dayRows, results.summary.whole_day_lead_days, "dates");
      }
    }
  }

  function renderSummary() {
    const summary = results.summary;
    summaryTick.toggleAttribute("hidden", summary.drawers_without_leads === 0);
    summaryTick.classList.remove("drawn");
    const headline = document.getElementById("summary-headline");
    const wording =
      summary.drawers_checked === 0 ? "empty" : summary.drawers_checked === 1 ? "one" : "many";
    headline.textContent = fill(headline.dataset[wording], {
      affected: summary.drawers_with_leads.toLocaleString("en-US"),
      checked: summary.drawers_checked.toLocaleString("en-US"),
    });
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
        if (index < severityOrder.length - 1) chip.append(", ");
        return chip;
      }),
    );
  }

  function buildFilters() {
    dateSelect.replaceChildren(
      new Option(dateSelect.dataset.all, ""),
      ...[...leadDates].sort().map((date) => new Option(formatDate(date), date)),
    );
    filterLevel.replaceChildren(
      ...Object.keys(showSeverity).map((show) => {
        const choice = element("label", "choice");
        const input = element("input");
        input.type = "radio";
        input.name = "show";
        input.value = show;
        input.addEventListener("change", changeFilters);
        const words =
          show === "all" ? filterLevel.dataset.all : results.labels.severities[showSeverity[show]];
        choice.append(input, ` ${words}`);
        return choice;
      }),
    );
  }

  function selectedShow() {
    return filterLevel.querySelector("input:checked")?.value ?? "all";
  }

  function changeFilters() {
    const address = resultsAddress(dateSelect.value, selectedShow());
    history.replaceState(null, "", address);
    applyFilters(new URLSearchParams(address.split("?")[1] ?? ""));
  }

  function applyFilters(params) {
    let date = params.get("date") ?? "";
    let show = params.get("show") ?? "all";
    if (!Object.hasOwn(showSeverity, show)) {
      show = "all";
    }
    if (date && !leadDates.has(date)) {
      date = "";
    }
    const address = resultsAddress(date, show);
    if (location.hash !== address) {
      history.replaceState(null, "", address);
    }
    for (const back of document.querySelectorAll('[data-role="back-to-results"]')) {
      back.href = address;
    }
    dateSelect.value = date;
    for (const input of filterLevel.querySelectorAll("input")) {
      input.checked = input.value === show;
    }
    const severity = showSeverity[show];
    const shown = sortedLeads.filter(
      (flag) => (!date || flag.business_date === date) && (!severity || flag.severity === severity),
    );
    renderGroups(shown, Boolean(date || severity));
    const noneAtAll = sortedLeads.length === 0;
    filters.hidden = noneAtAll;
    document.getElementById("leads-heading").hidden = noneAtAll;
    document.getElementById("leads-intro").hidden = noneAtAll;
    leadList.hidden = shown.length === 0;
    noLeads.hidden = !noneAtAll;
    noMatches.hidden = noneAtAll || shown.length > 0;
    const words = { level: severity ? results.labels.severities[severity] : "" };
    words.date = date ? formatDate(date) : "";
    const key = date && severity ? "both" : date ? "date" : severity ? "level" : "all";
    filterStatus.textContent = noneAtAll ? "" : fill(filterStatus.dataset[key], words);
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

  function fillDrawerTable() {
    const table = document.getElementById("drawer-table");
    table.tBodies[0].replaceChildren(
      ...results.shifts.map((item) => {
        const row = element("tr");
        const code = element("th");
        code.scope = "row";
        code.append(link(item.shift.shift_code, drawerAddress(item.shift.shift_code)));
        row.append(
          code,
          element("td", "", formatDate(item.shift.business_date)),
          element("td", "", item.shift.register_id),
          element("td", "", item.shift.cashier_id),
          element("td", "", results.labels.statuses[item.status]),
          amountCell(item.variance_amount),
        );
        return row;
      }),
    );
  }

  const lazyTables = [
    [document.getElementById("day-details"), fillDayTable],
    [document.getElementById("cashier-details"), fillCashierTable],
    [document.getElementById("drawer-list-details"), fillDrawerTable],
  ];

  function showResults(payload) {
    results = payload;
    sortedLeads = sortLeads(payload.flags);
    drawerGroups = groupLeads(sortedLeads.filter(flag => flag.shift_id !== null), "shift_code");
    leadDates = new Set(payload.flags.map((flag) => flag.business_date));
    shiftsByCode = new Map(payload.shifts.map((item) => [item.shift.shift_code, item]));
    shiftsByDate = new Map();
    for (const item of payload.shifts) {
      const codes = shiftsByDate.get(item.shift.business_date) ?? [];
      codes.push(item.shift.shift_code);
      shiftsByDate.set(item.shift.business_date, codes);
    }
    resultsRange.textContent = fill(resultsRange.dataset.template, {
      from: formatDate(payload.from_date),
      to: formatDate(payload.to_date),
    });
    renderSummary();
    buildFilters();
    for (const [details] of lazyTables) {
      details.open = false;
      details.dataset.filled = "";
      details.querySelector("tbody").replaceChildren();
    }
    announce(views.results.dataset.announce);
    navigate("#/results");
  }

  function downloadReport(name) {
    const report = results.reports[name];
    const url = URL.createObjectURL(
      new Blob([report.content], { type: `${report.media_type};charset=utf-8` }),
    );
    const anchor = link("", url);
    anchor.download = report.filename;
    body.append(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  function clockTime(timestamp, businessDate) {
    const time = timestamp.slice(11, 16);
    const day = timestamp.slice(0, 10);
    return day === businessDate ? time : `${formatDate(day)} ${time}`;
  }

  function renderDrawer(item) {
    const { shift } = item;
    const unknown = drawerGrid.dataset.unknown;
    const pos = shift.pos;
    drawerHeading.textContent = fill(drawerHeading.dataset.template, {
      register: shift.register_id, date: formatDate(shift.business_date),
    });
    const about = fill(drawerAbout.dataset.template, {
      code: shift.shift_code,
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
      const row = drawerTape.querySelector(`[data-line="${line}"]`);
      row.querySelector("td").textContent = value;
      row.querySelector(".input-tick")?.toggleAttribute("hidden", value === unknown);
    }
    for (const term of drawerTape.querySelectorAll("details")) {
      term.open = false;
    }
    for (const number of document.querySelectorAll("[data-outcome]")) {
      const value = amounts[number.dataset.outcome];
      number.textContent = value;
      number.className = /^-?\$/.test(value) ? "money" : "";
    }
    const worst = worstSeverity(item.flags);
    for (const panel of [drawerTape, document.getElementById("drawer-outcome")]) {
      panel.querySelector('[data-role="word"]').textContent = results.labels.statuses[item.status];
      const level = panel.querySelector('[data-role="level"]');
      level.hidden = !worst;
      level.className = worst ? `status ${severityClass[worst]}` : "status";
      level.textContent = worst ? results.labels.severities[worst] : "";
    }
    const index = reviewOrder.indexOf(shift.shift_code);
    const next = index < 0 ? null : reviewOrder[index + 1];
    nextDrawer.hidden = !next;
    nextDrawer.href = next ? drawerAddress(next) : "#/results";

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

    const foldZeros = shift.counts.some(count => count.quantity > 0);
    countSheet.tBodies[0].replaceChildren(
      ...shift.counts.map((count, index) => {
        const row = element("tr");
        row.id = `count-row-${index}`;
        row.dataset.zero = count.quantity === 0 ? "yes" : "no";
        row.hidden = count.quantity === 0 && foldZeros;
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
    const zeros = [...countSheet.querySelectorAll('[data-zero="yes"]')];
    countToggle.hidden = !foldZeros || !zeros.length;
    countToggle.ariaExpanded = "false";
    countToggle.setAttribute("aria-controls", zeros.map(row => row.id).join(" ") || "count-rows");
    countToggle.textContent = countToggle.dataset.open;
    document.getElementById("count-total").textContent = item.counted_amount;
    countSheet.closest(".sheet-paper").hidden = shift.counts.length === 0;
    countMissing.hidden = shift.counts.length > 0;
    countMissing.textContent =
      item.status === "open" ? countMissing.dataset.open : countMissing.dataset.none;

    drawerLeads.replaceChildren(
      ...sortLeads(item.flags).map((flag) => leadRow(flag, "drawer")),
    );
    drawerLeads.hidden = item.flags.length === 0;
    drawerNoLeads.hidden = item.flags.length > 0;
    dayLeads.replaceChildren(...sortLeads(item.daily_flags).map((flag) => leadRow(flag, "drawer")));
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

  countToggle.addEventListener("click", () => {
    const expanded = countToggle.ariaExpanded !== "true";
    countToggle.ariaExpanded = String(expanded);
    countToggle.textContent = expanded ? countToggle.dataset.close : countToggle.dataset.open;
    for (const row of countSheet.querySelectorAll('[data-zero="yes"]')) row.hidden = !expanded;
  });

  function depositSentence(item, unknown) {
    // A drawer's deposit share is unknown when its whole day is incomplete.
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

  function setRow(name, state, detail = "") {
    const row = rows.get(name);
    const status = row.querySelector('[data-role="status"]');
    const [label, className] = fileStatus[state];
    status.textContent = label;
    status.className = `status ${className}`;
    row.querySelector("svg").toggleAttribute("hidden", state !== "ready");
    row.querySelector('[data-role="size"]').textContent = state === "ready" ? detail : "";
    const problem = row.querySelector('[data-role="problem"]');
    problem.textContent = state === "problem" ? detail : "";
    problem.hidden = state !== "problem";
    if (state === "problem") {
      problemFiles.add(name);
    } else {
      problemFiles.delete(name);
    }
    const needed = [...rows.keys()].filter((name) => !chosen.has(name));
    filesProgress.textContent = fill(filesProgress.dataset.template, {
      ready: chosen.size - problemFiles.size,
      total: rows.size,
    }) + (needed.length ? ` ${message("needed", { names: needed.join(", ") })}`
      : problemFiles.size ? ` ${message("fix_files")}` : "");
  }

  function hideErrorSummary() {
    errorSummary.hidden = true;
    errorList.replaceChildren();
  }

  function showErrorSummary(problems) {
    errorList.replaceChildren(
      ...problems.map(({ text, target }) => {
        const item = element("li");
        const anchor = link(text, `#${target.id}`);
        anchor.addEventListener("click", (event) => {
          // Move focus without changing the address, which belongs to views.
          event.preventDefault();
          target.focus();
        });
        item.append(anchor);
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
        if (request?.view === "prepare") stopWaiting(request, "changed");
        chosen.set(file.name, file);
        setRow(file.name, "ready", formatSize(file.size));
        continue;
      }
      const expected = names.find((name) => name.toLowerCase() === file.name.toLowerCase());
      chooserNotes.append(
        element(
          "p",
          "",
          expected
            ? message("rename", { name: file.name, expected })
            : message("unknown_name", { name: file.name }),
        ),
      );
    }
  }

  async function checkExample() {
    if (request) {
      return;
    }
    clearRequestError(startError);
    const outcome = await run({
      button: tryExample,
      cancel: startCancel,
      slow: startSlow,
      view: "start",
      url: "/api/demo",
    });
    if (handledStop(outcome, tryExample, startError, checkExample)) {
      return;
    }
    if (outcome.payload) {
      showResults(outcome.payload);
    } else {
      showRequestError(startError, outcome.error.message, checkExample);
    }
  }

  async function checkMyFiles() {
    if (request) {
      return;
    }
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
    clearRequestError(prepareError);
    if (problems.length > 0) {
      showErrorSummary(problems);
      return;
    }
    hideErrorSummary();
    for (const name of [...problemFiles]) {
      setRow(name, "ready", formatSize(chosen.get(name).size));
    }
    const form = new FormData();
    for (const name of rows.keys()) {
      form.append("files", chosen.get(name), name);
    }
    const outcome = await run({
      button: checkFiles,
      cancel: prepareCancel,
      slow: prepareSlow,
      view: "prepare",
      url: "/api/check",
      requestBody: form,
    });
    if (handledStop(outcome, checkFiles, prepareError, checkMyFiles)) {
      return;
    }
    if (outcome.payload) {
      showResults(outcome.payload);
      return;
    }
    const { error, status } = outcome;
    if (status !== 400 && status !== 413) {
      showRequestError(prepareError, error.message, checkMyFiles);
      return;
    }
    const row = error.file_name ? rows.get(error.file_name) : undefined;
    if (row) {
      setRow(error.file_name, "problem", error.message);
    }
    showErrorSummary([{ text: error.message, target: row ?? fileInput }]);
  }

  for (const [details, fillTable] of lazyTables) {
    details.addEventListener("toggle", () => {
      if (details.open && !details.dataset.filled) {
        fillTable();
        details.dataset.filled = "yes";
      }
    });
  }

  for (const cancel of [startCancel, prepareCancel]) {
    cancel.addEventListener("click", () => {
      if (request) {
        stopWaiting(request, "cancel");
      }
    });
  }

  for (const button of document.querySelectorAll("[data-report]")) {
    button.addEventListener("click", () => downloadReport(button.dataset.report));
  }

  document.querySelector('[data-role="clear-filters"]').addEventListener("click", (event) => {
    event.preventDefault();
    history.replaceState(null, "", "#/results");
    applyFilters(new URLSearchParams());
    dateSelect.focus();
  });

  dateSelect.addEventListener("change", changeFilters);
  tryExample.addEventListener("click", checkExample);
  checkFiles.addEventListener("click", checkMyFiles);
  fileInput.addEventListener("change", () => {
    addFiles([...fileInput.files]);
    // Clearing the input lets the same file be chosen again after it is edited.
    fileInput.value = "";
  });
  fileDrop.addEventListener("dragover", (event) => {
    if (event.dataTransfer.types.includes("Files")) {
      event.preventDefault();
      event.dataTransfer.dropEffect = "copy";
    }
  });
  fileDrop.addEventListener("drop", (event) => {
    event.preventDefault();
    addFiles([...event.dataTransfer.files]);
  });
  window.addEventListener("hashchange", () => route());
  route({ initial: true });
})();
