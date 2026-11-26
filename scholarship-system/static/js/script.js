/**
 * University Scholarship Allocation System - Frontend Interactions
 * Handles:
 * 1. Mobile navigation drawer (<dialog> with IntersectionObserver + fallbacks)
 * 2. Delete confirmation modal (<dialog>)
 * 3. Accessible form validation feedback (:user-invalid sync + live preview)
 * 4. Rules weight-sum checker and print button
 */

document.addEventListener("DOMContentLoaded", () => {
  initMobileDrawer();
  initDeleteDialog();
  initAccessibleFormValidation();
  initApplicationLivePreview();
  initRulesWeightMonitor();
  initFlashDismissAndPrint();
});

function initMobileDrawer() {
  const drawer = document.getElementById("mobile-drawer");
  const openBtn = document.getElementById("drawer-open");
  const closeBtn = document.getElementById("drawer-close");
  if (!drawer || !openBtn || !closeBtn) return;

  const scroller = drawer.querySelector(".Drawer-scroller");
  const sheet = drawer.querySelector(".Drawer-sheet");
  if (!scroller || !sheet) return;

  if (!CSS.supports("animation-timeline: scroll()")) {
    scroller.addEventListener("scroll", () => {
      const width = sheet.offsetWidth || 1;
      const ratio = Math.max(0, Math.min(1, 1 - scroller.scrollLeft / width));
      drawer.style.setProperty("--drawer-backdrop", String(ratio));
    });
  }

  async function openDrawer() {
    drawer.showModal();
    if (!CSS.supports("scroll-initial-target", "nearest")) {
      scroller.scrollTo({ left: scroller.offsetWidth, behavior: "instant" });
      await new Promise((resolve) =>
        requestAnimationFrame(() => requestAnimationFrame(resolve))
      );
    }
    scroller.scrollTo({ left: 0, behavior: "auto" });
  }

  function closeDrawer() {
    scroller.scrollTo({ left: scroller.offsetWidth, behavior: "auto" });
  }

  const visibleThreshold = 1 / Math.max(window.innerWidth, 320);
  const observer = new IntersectionObserver(
    (entries) => {
      const entry = entries[entries.length - 1];
      if (!entry) return;
      if (entry.intersectionRatio < visibleThreshold && drawer.open) {
        drawer.close();
        openBtn.setAttribute("aria-expanded", "false");
      } else if (entry.intersectionRatio >= 0.99) {
        openBtn.setAttribute("aria-expanded", "true");
      }
    },
    { root: drawer, threshold: [visibleThreshold, 1] }
  );
  observer.observe(sheet);

  openBtn.addEventListener("click", openDrawer);
  closeBtn.addEventListener("click", closeDrawer);

  drawer.addEventListener("click", (event) => {
    if (!sheet.contains(event.target)) {
      closeDrawer();
    }
  });

  drawer.addEventListener("cancel", (event) => {
    if (event.cancelable) {
      event.preventDefault();
      closeDrawer();
    }
  });

  const desktopMedia = window.matchMedia("(min-width: 960px)");
  desktopMedia.addEventListener("change", (event) => {
    if (event.matches && drawer.open) {
      drawer.close();
      openBtn.setAttribute("aria-expanded", "false");
    }
  });
}

function initDeleteDialog() {
  const dialog = document.getElementById("confirm-delete-dialog");
  const form = document.getElementById("delete-confirm-form");
  const msg = document.getElementById("delete-dialog-message");
  const cancelBtn = document.getElementById("delete-cancel-btn");
  if (!dialog || !form || !msg || !cancelBtn) return;

  document.querySelectorAll(".js-delete-trigger").forEach((btn) => {
    btn.addEventListener("click", () => {
      const url = btn.dataset.deleteUrl || "";
      const name = btn.dataset.studentName || "this student";
      const sid = btn.dataset.studentId || "";
      form.action = url;
      msg.textContent = `Are you sure you want to delete ${name} (${sid})? This will permanently remove the record from SQLite and update all rankings.`;
      dialog.showModal();
    });
  });

  cancelBtn.addEventListener("click", () => {
    dialog.close("cancel");
  });

  dialog.addEventListener("close", () => {
    dialog.returnValue = "";
  });

  // Backdrop click light-dismiss
  let pressedOutside = false;
  const isOutside = (e) => {
    const r = dialog.getBoundingClientRect();
    return e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom;
  };
  dialog.addEventListener("pointerdown", (e) => {
    pressedOutside = isOutside(e);
  });
  dialog.addEventListener("pointerup", (e) => {
    if (pressedOutside && isOutside(e)) dialog.close("cancel");
  });
}

function initAccessibleFormValidation() {
  const linkError = (el, shown) => {
    const errorId = el.dataset.error;
    if (!errorId) return;
    const ids = (el.getAttribute("aria-describedby") || "")
      .split(/\s+/)
      .filter((id) => id && id !== errorId);
    if (shown) ids.push(errorId);
    if (ids.length) el.setAttribute("aria-describedby", ids.join(" "));
    else el.removeAttribute("aria-describedby");
  };

  const supportsUserInvalid = CSS.supports("selector(:user-invalid)");
  const dirtyState = new WeakMap();

  const announcer = document.createElement("div");
  announcer.setAttribute("aria-live", "polite");
  announcer.classList.add("visually-hidden");
  document.body.append(announcer);
  let announceTimer;

  const syncControl = (el, shouldAnnounce = false) => {
    if (!el.matches?.("input, select, textarea")) return;
    let invalid = false;

    if (supportsUserInvalid) {
      invalid = el.matches(":user-invalid");
    } else {
      const state = dirtyState.get(el);
      invalid = Boolean(state?.hasBlurred && !el.validity.valid);
      el.classList.toggle("user-invalid-fallback", invalid);
      el.classList.toggle("user-valid-fallback", Boolean(state?.hasBlurred && el.validity.valid));
    }

    el.setAttribute("aria-invalid", invalid ? "true" : "false");
    linkError(el, invalid);

    if (invalid && shouldAnnounce && el.dataset.error) {
      const errNode = document.getElementById(el.dataset.error);
      if (errNode) {
        clearTimeout(announceTimer);
        announceTimer = setTimeout(() => {
          announcer.textContent = errNode.textContent.trim();
        }, 400);
      }
    }
  };

  document.querySelectorAll("input, select, textarea").forEach((el) => {
    el.setAttribute("aria-invalid", "false");
  });

  document.addEventListener(
    "blur",
    (e) => {
      const el = e.target;
      if (!el.matches?.("input, select, textarea")) return;
      const state = dirtyState.get(el) || { hasBlurred: false };
      state.hasBlurred = true;
      dirtyState.set(el, state);
      syncControl(el, true);
    },
    true
  );

  document.addEventListener("input", (e) => {
    if (e.target.hasAttribute("aria-invalid")) {
      syncControl(e.target, false);
    }
  });

  document.addEventListener(
    "invalid",
    (e) => {
      const el = e.target;
      dirtyState.set(el, { hasBlurred: true });
      syncControl(el, false);
    },
    true
  );
}

function initApplicationLivePreview() {
  const form = document.getElementById("student-application-form");
  if (!form) return;

  const totalEl = document.getElementById("preview-total");
  const aggEl = document.getElementById("preview-aggregate");
  const incMeritEl = document.getElementById("preview-income-merit");
  const scoreEl = document.getElementById("preview-score");
  const eligEl = document.getElementById("preview-eligibility");
  const reasonsBox = document.getElementById("preview-reasons-box");
  const reasonsList = document.getElementById("preview-reasons-list");

  const minAgg = parseFloat(form.dataset.minAgg || "75");
  const minSub = parseFloat(form.dataset.minSub || "50");
  const minAtt = parseFloat(form.dataset.minAtt || "75");
  const maxInc = parseFloat(form.dataset.maxInc || "250000");
  const certReq = form.dataset.certReq === "1";

  const wAgg = parseFloat(form.dataset.wAgg || "0.7");
  const wAtt = parseFloat(form.dataset.wAtt || "0.2");
  const wInc = parseFloat(form.dataset.wInc || "0.1");

  const slabs = [
    [parseFloat(form.dataset.s1Lim), parseFloat(form.dataset.s1Pts)],
    [parseFloat(form.dataset.s2Lim), parseFloat(form.dataset.s2Pts)],
    [parseFloat(form.dataset.s3Lim), parseFloat(form.dataset.s3Pts)],
    [parseFloat(form.dataset.s4Lim), parseFloat(form.dataset.s4Pts)],
  ];
  const abovePts = parseFloat(form.dataset.sAbove || "0");

  function computePreview() {
    const markInputs = Array.from(form.querySelectorAll(".mark-input"));
    const marks = markInputs.map((inp) => parseFloat(inp.value));
    const haveAllMarks = marks.every((v) => !Number.isNaN(v));

    if (!haveAllMarks) {
      totalEl.textContent = "0.00 / 500";
      aggEl.textContent = "0.00%";
      incMeritEl.textContent = "—";
      scoreEl.textContent = "—";
      eligEl.innerHTML = '<span class="badge badge-neutral">Enter all 5 subject marks</span>';
      reasonsBox.hidden = true;
      return;
    }

    const total = marks.reduce((acc, v) => acc + v, 0);
    const agg = total / marks.length;
    totalEl.textContent = `${total.toFixed(2)} / 500`;
    aggEl.textContent = `${agg.toFixed(2)}%`;

    const attVal = parseFloat(document.getElementById("attendance_percentage")?.value || "NaN");
    const incVal = parseFloat(document.getElementById("annual_income")?.value || "NaN");
    const certVal = document.getElementById("income_certificate_status")?.value || "Available";

    if (Number.isNaN(attVal) || Number.isNaN(incVal)) {
      incMeritEl.textContent = "—";
      scoreEl.textContent = "—";
      eligEl.innerHTML = '<span class="badge badge-neutral">Enter attendance &amp; income</span>';
      reasonsBox.hidden = true;
      return;
    }

    let incMerit = abovePts;
    for (const [lim, pts] of slabs) {
      if (incVal <= lim) {
        incMerit = pts;
        break;
      }
    }
    incMeritEl.textContent = `${incMerit.toFixed(0)} pts`;

    const reasons = [];
    if (agg < minAgg) reasons.push(`Aggregate ${agg.toFixed(2)}% < ${minAgg.toFixed(2)}%`);
    marks.forEach((m, idx) => {
      if (m < minSub) {
        const label = markInputs[idx].closest(".field")?.querySelector("label")?.textContent?.replace("*", "").trim() || "Subject";
        reasons.push(`${label} (${m}) < ${minSub}`);
      }
    });
    if (attVal < minAtt) reasons.push(`Attendance ${attVal.toFixed(1)}% < ${minAtt.toFixed(1)}%`);
    if (incVal > maxInc) reasons.push(`Family income exceeds ₹${maxInc.toLocaleString("en-IN")}`);
    if (certReq && certVal !== "Available") reasons.push("Income certificate missing");

    if (reasons.length === 0) {
      const score = agg * wAgg + attVal * wAtt + incMerit * wInc;
      scoreEl.textContent = score.toFixed(2);
      eligEl.innerHTML = '<span class="badge badge-success">Eligible</span>';
      reasonsBox.hidden = true;
    } else {
      scoreEl.textContent = "0.00";
      eligEl.innerHTML = '<span class="badge badge-danger">Not Eligible</span>';
      reasonsList.innerHTML = reasons.map((r) => `<li>${r}</li>`).join("");
      reasonsBox.hidden = false;
    }
  }

  form.querySelectorAll(".calc-input").forEach((el) => {
    el.addEventListener("input", computePreview);
    el.addEventListener("change", computePreview);
  });

  computePreview();
}

function initRulesWeightMonitor() {
  const sumDisplay = document.getElementById("weight-sum-display");
  const weightInputs = document.querySelectorAll(".weight-input");
  if (!sumDisplay || weightInputs.length === 0) return;

  function updateWeightSum() {
    let total = 0;
    weightInputs.forEach((inp) => {
      const val = parseFloat(inp.value);
      if (!Number.isNaN(val)) total += val;
    });
    sumDisplay.textContent = total.toFixed(2);
    sumDisplay.style.color = Math.abs(total - 1.0) <= 0.001 ? "var(--success-text)" : "var(--danger-text)";
  }

  weightInputs.forEach((inp) => inp.addEventListener("input", updateWeightSum));
  updateWeightSum();
}

function initFlashDismissAndPrint() {
  document.querySelectorAll(".alert-close").forEach((btn) => {
    btn.addEventListener("click", () => {
      btn.closest(".alert")?.remove();
    });
  });

  const printBtn = document.getElementById("print-report-btn");
  if (printBtn) {
    printBtn.addEventListener("click", () => window.print());
  }
}
