// Renders the resume preview (editor + preview pages) and drives the editor UI.
(function () {
  const data = window.RESUME_CONTENT || {};
  const previewEl = document.getElementById("resume-preview");

  const SCHEMAS = {
    education: [["degree", "Degree / course"], ["date", "Date (e.g. Expected 2027)"], ["institution", "Institution"],
                ["detail", "CGPA / Percentage"], ["location", "Location"]],
    skills:    [["label", "Category"], ["value", "Items (one per line or comma-separated)", true]],
    projects:  [["name", "Project name"], ["description", "Description", true]],
  };

  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const bullets = (t) => {
    const lines = String(t || "").split("\n").map((l) => l.replace(/^[-•*\s]+/, "").trim()).filter(Boolean);
    return lines.length ? "<ul>" + lines.map((l) => `<li>${esc(l)}</li>`).join("") + "</ul>" : "";
  };

  const link = (url, label) => {
    url = String(url || "").trim();
    if (!url) return "";
    if (!/^https?:\/\//i.test(url)) url = "https://" + url;
    return `<a href="${esc(url)}" target="_blank" rel="noopener">${label}</a>`;
  };
  const multiline = (t) => String(t || "").split("\n").map((l) => esc(l.trim())).filter(Boolean).join("<br>");

  function render() {
    const d = data;
    const contact = [esc(d.phone), esc(d.email), link(d.linkedin, "LinkedIn"), link(d.github, "GitHub")]
      .filter(Boolean).join(" &nbsp;&mdash;&nbsp; ");
    let h = `<h1>${esc(d.name) || "YOUR NAME"}</h1>`;
    if (contact) h += `<div class="r-contact">${contact}</div>`;
    if (d.objective) h += `<h2>Objective</h2><p class="r-just">${esc(d.objective)}</p>`;
    if ((d.education || []).length) {
      h += "<h2>Education</h2>";
      d.education.forEach((e) => {
        h += `<div class="r-row"><b>${esc(e.degree)}</b><span>${esc(e.date)}</span></div>`;
        if (e.institution) h += `<div>${esc(e.institution)}</div>`;
        if (e.detail || e.location) h += `<div class="r-row"><span>${esc(e.detail)}</span><span>${esc(e.location)}</span></div>`;
        h += `<div class="r-gap"></div>`;
      });
    }
    const skills = (d.skills || []).filter((s) => s.label || s.value);
    if (skills.length) {
      h += "<h2>Skills</h2><div class=\"r-skills\">";
      skills.forEach((s) => { h += `<b>${esc(s.label)}</b><div>${multiline(s.value)}</div>`; });
      h += "</div>";
    }
    if (d.experience && bullets(d.experience)) h += `<h2>Project Experience</h2>${bullets(d.experience)}`;
    const projects = (d.projects || []).filter((p) => p.name || p.description);
    if (projects.length) {
      h += "<h2>Projects</h2>";
      projects.forEach((p) => {
        h += `<div><b>${esc(p.name)}</b></div>`;
        if (p.description) h += `<p class="r-just r-indent">${esc(p.description)}</p>`;
      });
    }
    if (d.declaration) h += `<h2>Declaration</h2><ul><li class="r-just">${esc(d.declaration)}</li></ul>`;
    previewEl.innerHTML = h;
  }

  render();

  // Everything below only applies to the editor page
  if (!window.RESUME_ID) return;

  const statusEl = document.getElementById("save-status");
  const titleEl = document.getElementById("resume-title");
  let dirty = false, timer = null;

  function markDirty() {
    dirty = true;
    statusEl.textContent = "Unsaved changes…";
    clearTimeout(timer);
    timer = setTimeout(save, 1500); // autosave
  }

  async function save() {
    clearTimeout(timer);
    statusEl.textContent = "Saving…";
    try {
      const res = await fetch(`/api/resume/${window.RESUME_ID}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: titleEl.value, content: data }),
      });
      if (!res.ok) throw new Error();
      dirty = false;
      statusEl.textContent = "Saved";
    } catch (e) {
      statusEl.textContent = "Save failed";
    }
  }

  // simple fields
  document.querySelectorAll("[data-field]").forEach((el) => {
    el.value = data[el.dataset.field] || "";
    el.addEventListener("input", () => { data[el.dataset.field] = el.value; render(); markDirty(); });
  });
  titleEl.addEventListener("input", markDirty);

  // list sections
  function renderList(key) {
    const box = document.getElementById("list-" + key);
    box.innerHTML = "";
    (data[key] = data[key] || []).forEach((item, idx) => {
      const wrap = document.createElement("div");
      wrap.className = "item";
      SCHEMAS[key].forEach(([field, label, multi]) => {
        const l = document.createElement("label");
        l.textContent = label;
        const input = document.createElement(multi ? "textarea" : "input");
        if (multi) input.rows = 3;
        input.value = item[field] || "";
        input.addEventListener("input", () => { item[field] = input.value; render(); markDirty(); });
        l.appendChild(input);
        wrap.appendChild(l);
      });
      const actions = document.createElement("div");
      actions.className = "item-actions";
      const rm = document.createElement("button");
      rm.className = "btn btn-sm btn-danger";
      rm.type = "button";
      rm.textContent = "Remove";
      rm.addEventListener("click", () => { data[key].splice(idx, 1); renderList(key); render(); markDirty(); });
      actions.appendChild(rm);
      wrap.appendChild(actions);
      box.appendChild(wrap);
    });
  }
  Object.keys(SCHEMAS).forEach(renderList);

  document.querySelectorAll("[data-add]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const key = btn.dataset.add;
      (data[key] = data[key] || []).push({});
      renderList(key);
      markDirty();
    });
  });

  document.getElementById("btn-save").addEventListener("click", save);

  document.getElementById("btn-pdf").addEventListener("click", async () => {
    statusEl.textContent = "Generating PDF…";
    try {
      const res = await fetch(`/api/resume/${window.RESUME_ID}/pdf`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: data }),
      });
      if (!res.ok) throw new Error();
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = (titleEl.value || "resume").replace(/[^\w-]+/g, "_") + ".pdf";
      a.click();
      URL.revokeObjectURL(a.href);
      statusEl.textContent = dirty ? "Unsaved changes…" : "Saved";
    } catch (e) {
      statusEl.textContent = "PDF failed";
    }
  });

  window.addEventListener("beforeunload", (e) => { if (dirty) { e.preventDefault(); e.returnValue = ""; } });
})();
