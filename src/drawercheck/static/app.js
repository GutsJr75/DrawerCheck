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
  const resultsReady = document.getElementById("results-ready");
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

  function showResults(payload) {
    resultsReady.textContent = fill(resultsReady.dataset.template, {
      drawers: payload.summary.drawers_checked,
      from: payload.from_date,
      to: payload.to_date,
    });
    showView("results");
    announce(resultsReady.textContent);
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
