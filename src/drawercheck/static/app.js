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
    close: document.getElementById("view-close"),
    review: document.getElementById("view-review"),
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
  const closeForm = document.getElementById("close-form");
  const closeSummary = document.getElementById("close-summary");
  const closeProblems = document.getElementById("close-problems");
  const checkDrawer = document.getElementById("check-drawer");
  const closeCancel = document.getElementById("close-cancel");
  const closeSlow = document.getElementById("close-slow");
  const closeError = document.getElementById("close-error");
  const timesMissing = document.getElementById("times-missing");
  const reportFigures = document.getElementById("report-figures");
  const dropList = document.getElementById("drop-list");
  const dropRows = document.getElementById("drop-rows");
  const addDrop = document.getElementById("add-drop");
  const reviewLeads = document.getElementById("review-leads");
  const reviewTape = document.querySelector('[data-tape="review"]');
  const reviewCount = document.getElementById("review-count");
  const coverageList = document.getElementById("coverage");
  const signoffForm = document.getElementById("signoff-form");
  const checkAgain = document.getElementById("check-again");
  const reviewCancel = document.getElementById("review-cancel");
  const reviewSlow = document.getElementById("review-slow");
  const reviewError = document.getElementById("review-error");
  const recountToggle = document.getElementById("recount-toggle");
  const recountSheet = document.getElementById("recount-sheet");
  const coverageClass = { ran_no_lead: "status-ready", ran_lead: "status-note", not_run: "status-waiting" };
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
  let checked = null;
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
    if (["prepare", "close", "review"].includes(path)) {
      return { view: path };
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
    } else if (address.view === "review") {
      renderReview();
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

  function levelLabel(severity, labels = results.labels) {
    return element("span", `status ${severityClass[severity]}`, labels.severities[severity]);
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

  function leadRow(flag, scope, labels = results.labels) {
    const row = element("li", scope === "drawer" ? "lead-item" : "group-lead");
    const content = element("div", "lead-body");
    content.append(
      element("strong", "lead-title", labels.rules[flag.rule_code] ?? flag.rule_code),
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
    row.append(levelLabel(flag.severity, labels), content);
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

  function clockTime(timestamp, businessDate, labels = results.labels) {
    const time = timestamp.slice(11, 16);
    const day = timestamp.slice(0, 10);
    return day === businessDate ? time : `${labels.dates[day]} ${time}`;
  }

  function fillTape(tape, item, unknown) {
    // Drawer details and Review share one tape; Python supplies every amount.
    const { shift } = item;
    const pos = shift.pos;
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
      const row = tape.querySelector(`[data-line="${line}"]`);
      row.querySelector("td").textContent = value;
      row.querySelector(".input-tick")?.toggleAttribute("hidden", value === unknown);
    }
    for (const term of tape.querySelectorAll("details")) {
      term.open = false;
    }
    return amounts;
  }

  function fillStatus(panels, item, labels) {
    const worst = worstSeverity(item.flags);
    for (const panel of panels) {
      panel.querySelector('[data-role="word"]').textContent = labels.statuses[item.status];
      const level = panel.querySelector('[data-role="level"]');
      level.hidden = !worst;
      level.className = worst ? `status ${severityClass[worst]}` : "status";
      level.textContent = worst ? labels.severities[worst] : "";
    }
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

    const amounts = fillTape(drawerTape, item, unknown);
    for (const number of document.querySelectorAll("[data-outcome]")) {
      const value = amounts[number.dataset.outcome];
      number.textContent = value;
      number.className = /^-?\$/.test(value) ? "money" : "";
    }
    fillStatus([drawerTape, document.getElementById("drawer-outcome")], item, results.labels);
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

  function showErrorSummary(problems, summary = errorSummary, list = errorList) {
    list.replaceChildren(
      ...problems.map(({ text, target, owner }) => {
        const item = element("li");
        if (owner) item.dataset.for = owner.id;
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
    summary.hidden = false;
    summary.focus();
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

  function field(name) {
    return document.querySelector(`[data-field="${name}"]`);
  }

  function choice(name) {
    return closeForm.elements[name].value;
  }

  function renumberDrops() {
    [...dropRows.children].forEach((row, index) => {
      const n = index + 1;
      for (const input of row.querySelectorAll("input")) {
        input.id = `drop-${n}-${input.dataset.part}`;
        input.dataset.field = `safe_drops.${n}.${input.dataset.part}`;
        input.previousElementSibling.htmlFor = input.id;
        input.previousElementSibling.textContent = fill(dropRows.dataset[input.dataset.part === "amount" ? "amount" : "bag"], { n });
      }
      row.querySelector("button").textContent = fill(dropRows.dataset.remove, { n });
    });
    addDrop.hidden = dropRows.children.length >= Number(addDrop.dataset.max);
  }

  function newDrop() {
    const row = element("li", "field-grid");
    for (const part of ["amount", "bag_number"]) {
      const box = element("div", "field");
      const input = element("input");
      input.dataset.part = part;
      input.autocomplete = "off";
      if (part === "amount") {
        input.inputMode = "decimal";
        input.setAttribute("aria-describedby", "money-hint");
      }
      box.append(element("label"), input);
      row.append(box);
    }
    const remove = element("button", "button button-secondary");
    remove.type = "button";
    remove.addEventListener("click", () => {
      const next = row.nextElementSibling ?? row.previousElementSibling;
      // Renumbering changes the ids, so drop messages clear and return on the next check.
      for (const input of dropRows.querySelectorAll('[aria-invalid="true"]')) clearProblem(input);
      row.remove();
      renumberDrops();
      pruneProblems();
      discardCheck();
      (next?.querySelector("input") ?? addDrop).focus();
    });
    row.append(remove);
    dropRows.append(row);
    renumberDrops();
    return row;
  }

  function showChoices() {
    reportFigures.hidden = choice("report") !== "yes";
    dropList.hidden = choice("drops") !== "list";
    if (!dropList.hidden && dropRows.children.length === 0) newDrop();
    for (const input of [field("opened_at"), field("closed_at")]) input.disabled = timesMissing.checked;
  }

  function discardCheck() {
    // Any change makes the last check out of date; a late reply is ignored.
    checked = null;
    if (request?.view === "close") stopWaiting(request, "changed");
  }

  function lines(name) {
    const counts = {};
    for (const input of document.querySelectorAll(`[data-field^="${name}."]`)) {
      counts[input.dataset.field.slice(name.length + 1)] = input.value;
    }
    return counts;
  }

  function drawerPayload() {
    const counts = lines("counts");
    const report = {};
    for (const input of reportFigures.querySelectorAll("input")) {
      report[input.dataset.field.slice("register_report.".length)] = input.value;
    }
    const drops = choice("drops");
    return {
      business_date: field("business_date").value,
      register_id: field("register_id").value,
      cashier_id: field("cashier_id").value,
      opened_at: timesMissing.checked ? null : field("opened_at").value,
      closed_at: timesMissing.checked ? null : field("closed_at").value,
      opening_float: field("opening_float").value,
      counts,
      recount: recountSheet.hidden ? null : lines("recount"),
      register_report: choice("report") === "yes" ? report : null,
      safe_drops: drops === "missing" ? null : drops === "none" ? [] : [...dropRows.children].map((row) => ({
        amount: row.querySelector('[data-part="amount"]').value,
        bag_number: row.querySelector('[data-part="bag_number"]').value,
      })),
      verifier_id: field("verifier_id").value,
      variance_note: field("variance_note").value,
    };
  }

  function clearProblem(owner) {
    owner.removeAttribute("aria-invalid");
    if (owner.dataset.describedby) owner.setAttribute("aria-describedby", owner.dataset.describedby);
    else owner.removeAttribute("aria-describedby");
    for (const note of document.querySelectorAll(`[data-for="${owner.id}"]`)) {
      (note.closest(".error-row") ?? note).remove();
    }
  }

  function clearFieldProblems() {
    for (const owner of document.querySelectorAll('[aria-invalid="true"]')) clearProblem(owner);
    for (const summary of [closeSummary, document.getElementById("review-summary")]) {
      summary.hidden = true;
      summary.querySelector("ul").replaceChildren();
    }
  }

  function pruneProblems(changed) {
    // A choice can hide, disable, or answer a field; its old message no longer applies.
    for (const owner of document.querySelectorAll('[aria-invalid="true"]')) {
      if (owner.closest("[hidden]") || owner.disabled || owner === changed?.closest("fieldset") || owner === changed) {
        clearProblem(owner);
      }
    }
    for (const summary of [closeSummary, document.getElementById("review-summary")]) {
      const list = summary.querySelector("ul");
      for (const item of [...list.children]) {
        const owner = item.dataset.for && document.getElementById(item.dataset.for);
        if (item.dataset.for && owner?.getAttribute("aria-invalid") !== "true") item.remove();
      }
      if (!list.children.length) summary.hidden = true;
    }
  }

  function showRecount(open) {
    recountSheet.hidden = !open;
    recountToggle.ariaExpanded = String(open);
    recountToggle.textContent = open ? recountToggle.dataset.remove : recountToggle.dataset.add;
    if (!open) {
      // Removing the recount drops its entries; the first count is untouched.
      for (const input of recountSheet.querySelectorAll("input")) input.value = "";
      pruneProblems();
    }
  }

  function markStale() {
    // The result no longer matches the recount or sign-off; a late reply is ignored.
    if (request?.view === "review") stopWaiting(request, "changed");
    if (checked && !checked.stale) {
      checked.stale = true;
      renderReview();
    }
  }

  function markField(name, text) {
    let focus = field(name);
    if (!focus) return { target: checkDrawer };
    let owner = focus;
    const note = element("p", "field-error", text);
    note.id = `problem-${name.replace(/\W/g, "-")}`;
    if (focus.disabled) {
      // Unavailable times: the message belongs to the choice that disabled them.
      owner = focus = timesMissing;
      timesMissing.parentElement.after(note);
    } else if (focus.tagName === "FIELDSET") {
      focus.querySelector("legend").after(note);
      focus = focus.querySelector("input");
    } else if (focus.closest(".count-entry")) {
      // A full-width row under the count line keeps the message readable at 320px.
      const cell = element("td");
      cell.colSpan = 2;
      cell.append(note);
      const row = element("tr", "error-row");
      row.append(cell);
      focus.closest("tr").after(row);
    } else {
      focus.after(note);
    }
    note.dataset.for = owner.id;
    owner.dataset.describedby = owner.getAttribute("aria-describedby") ?? "";
    owner.setAttribute("aria-describedby", `${note.id} ${owner.dataset.describedby}`.trim());
    owner.setAttribute("aria-invalid", "true");
    return { target: focus, owner };
  }

  function showFieldProblems(problems) {
    // Unavailable times give the same message twice; list it once.
    const opened = problems.find((problem) => problem.field === "opened_at");
    const unique = problems.filter((problem) =>
      !(problem.field === "closed_at" && problem.message === opened?.message));
    // Sign-off problems belong to Review, where Check again sent them.
    const summary = views.review.contains(field(unique[0].field))
      ? document.getElementById("review-summary") : closeSummary;
    showErrorSummary(
      unique.map(({ field: name, message: text }) => ({ text, ...markField(name, text) })),
      summary,
      summary.querySelector("ul"),
    );
  }

  function choiceProblems() {
    const problems = [];
    if (!choice("report")) problems.push({ field: "register_report", message: message("drawer_report") });
    if (!choice("drops")) problems.push({ field: "safe_drops", message: message("drawer_drops") });
    if (choice("drops") === "list" && dropRows.children.length === 0) {
      problems.push({ field: "safe_drops", message: message("drawer_add_drop") });
    }
    return problems;
  }

  function finishCheck(outcome, button, box, retry) {
    if (handledStop(outcome, button, box, retry)) {
      return;
    }
    if (outcome.payload) {
      checked = outcome.payload;
      announce(views.review.dataset.announce);
      navigate("#/review");
    } else if (outcome.status === 400 && outcome.error.fields) {
      showFieldProblems(outcome.error.fields);
    } else {
      showRequestError(box, outcome.error.message, retry);
    }
  }

  function drawerRequest(button, cancel, slow, view) {
    return run({
      button,
      cancel,
      slow,
      view,
      url: "/api/drawer",
      requestBody: new Blob([JSON.stringify(drawerPayload())], { type: "application/json" }),
    });
  }

  async function checkTheDrawer(event) {
    event?.preventDefault();
    if (request) {
      return;
    }
    clearFieldProblems();
    clearRequestError(closeError);
    const problems = choiceProblems();
    if (problems.length) {
      showFieldProblems(problems);
      return;
    }
    // A new check starts a new review: a recount and sign-off applied to the old figures.
    signoffForm.reset();
    showRecount(false);
    finishCheck(await drawerRequest(checkDrawer, closeCancel, closeSlow, "close"), checkDrawer, closeError, checkTheDrawer);
  }

  async function checkSignoff(event) {
    event?.preventDefault();
    if (request || !checked) {
      return;
    }
    clearFieldProblems();
    clearRequestError(reviewError);
    finishCheck(await drawerRequest(checkAgain, reviewCancel, reviewSlow, "review"), checkAgain, reviewError, checkSignoff);
  }

  function countRow(count) {
    const row = element("tr");
    const denomination = element("th", "money", count.denomination);
    denomination.scope = "row";
    row.append(denomination, element("td", "number", count.quantity.toLocaleString("en-US")),
      amountCell(count.line_total_amount));
    return row;
  }

  function renderReview() {
    document.getElementById("review-empty").hidden = Boolean(checked);
    document.getElementById("review-body").hidden = !checked;
    if (!checked) return;
    const { drawer: item, labels } = checked;
    const { shift } = item;
    document.getElementById("review-stale").hidden = !checked.stale;
    document.getElementById("review-result").hidden = Boolean(checked.stale);
    const about = document.getElementById("review-about");
    about.textContent = fill(about.dataset.template, {
      register: shift.register_id,
      date: labels.dates[shift.business_date],
      cashier: shift.cashier_id,
      opened: clockTime(shift.opened_at, shift.business_date, labels),
      closed: clockTime(shift.closed_at, shift.business_date, labels),
    });
    const amounts = fillTape(reviewTape, item, "unknown");
    for (const number of views.review.querySelectorAll("[data-review]")) {
      number.textContent = amounts[number.dataset.review];
      number.className = /^-?\$/.test(number.textContent) ? "money" : "";
    }
    fillStatus([reviewTape, document.getElementById("review-outcome")], item, labels);
    document.getElementById("review-no-report").hidden = Boolean(shift.pos);
    reviewCount.tBodies[0].replaceChildren(...shift.counts.map(countRow));
    document.getElementById("review-count-total").textContent = item.counted_amount;
    const first = checked.initial_count;
    const countHeading = document.getElementById("review-count-heading");
    countHeading.textContent = first ? countHeading.dataset.recount : countHeading.dataset.first;
    document.getElementById("recount-compare").hidden = !first;
    document.getElementById("first-count-details").hidden = !first;
    if (first) {
      const figures = {
        "first-counted": first.counted_amount, "first-difference": first.variance_amount,
        "first-status": labels.statuses[first.status], "recount-counted": item.counted_amount,
        "recount-difference": item.variance_amount, "recount-status": labels.statuses[item.status],
      };
      for (const cell of views.review.querySelectorAll("[data-compare]")) cell.textContent = figures[cell.dataset.compare];
      document.getElementById("first-count").tBodies[0].replaceChildren(...first.counts.map(countRow));
    }
    reviewLeads.replaceChildren(...sortLeads(item.flags).map((flag) => leadRow(flag, "drawer", labels)));
    reviewLeads.hidden = item.flags.length === 0;
    document.getElementById("review-no-leads").hidden = item.flags.length > 0;
    coverageList.replaceChildren(
      ...checked.coverage.map((entry) => {
        const row = element("li", "lead-item");
        const content = element("div", "lead-body");
        content.append(element("strong", "lead-title", entry.label), element("p", "lead-message", entry.detail));
        if (entry.partial) {
          for (const key of ["checked", "unavailable"]) {
            const list = element("ul", "coverage-parts");
            list.append(...entry[key].map((text) => element("li", "", text)));
            content.append(element("p", "lead-meta", coverageList.dataset[key]), list);
          }
        }
        row.append(element("span", `status ${coverageClass[entry.state]}`, coverageList.dataset[entry.state]), content);
        return row;
      }),
    );
  }

  closeForm.addEventListener("submit", checkTheDrawer);
  signoffForm.addEventListener("submit", checkSignoff);
  signoffForm.addEventListener("input", markStale);
  recountToggle.addEventListener("click", () => {
    const open = recountSheet.hidden;
    showRecount(open);
    markStale();
    if (open) recountSheet.querySelector("input").focus();
  });
  closeForm.addEventListener("input", discardCheck);
  closeForm.addEventListener("change", (event) => {
    showChoices();
    if (event.target.type === "radio" || event.target === timesMissing) pruneProblems(event.target);
  });
  addDrop.addEventListener("click", () => {
    newDrop().querySelector("input").focus();
    discardCheck();
  });

  for (const cancel of [startCancel, prepareCancel, closeCancel, reviewCancel]) {
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
