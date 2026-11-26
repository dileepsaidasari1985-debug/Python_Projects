/**
 * Smart ATM Transaction & Banking Simulation System - Client Interactions
 * Follows modern web guidance for:
 * - Responsive navigation drawer (popover="manual" on mobile, sidebar on desktop)
 * - Accessible form validation (:user-invalid + aria-invalid sync + live announcer)
 * - Native modal <dialog> fallback & returnValue cleanup
 * - Responsive stacked table label CSS variables (--label-N)
 * - Interactive Transaction Sequence row builder
 */

(() => {
  "use strict";

  // -------------------------------------------------------------------------
  // 1. Responsive Navigation Drawer / Sidebar
  // -------------------------------------------------------------------------
  const drawer = document.getElementById("drawer");
  const openBtn = document.getElementById("drawer-open");
  const closeBtn = document.getElementById("drawer-close");
  const mainContent = document.getElementById("main-content");

  if (drawer && openBtn && closeBtn && mainContent) {
    const scroller = drawer.querySelector(".Drawer-scroller");
    const sheet = drawer.querySelector(".Drawer-sheet");
    const mobileQuery = window.matchMedia("(max-width: 960px)");

    const syncSidebarMode = (isMobile) => {
      if (isMobile) {
        drawer.setAttribute("popover", "manual");
        drawer.setAttribute("role", "dialog");
      } else {
        if (drawer.matches(":popover-open") || drawer.classList.contains(":popover-open")) {
          try {
            drawer.hidePopover();
          } catch (_) {}
        }
        mainContent.inert = false;
        drawer.removeAttribute("aria-modal");
        drawer.removeAttribute("popover");
        drawer.removeAttribute("role");
        openBtn.setAttribute("aria-expanded", "false");
      }
    };

    syncSidebarMode(mobileQuery.matches);
    mobileQuery.addEventListener("change", (e) => syncSidebarMode(e.matches));

    const openDrawer = async () => {
      if (!mobileQuery.matches) return;
      if (typeof drawer.showPopover === "function") {
        drawer.showPopover();
      }
      mainContent.inert = true;
      drawer.setAttribute("aria-modal", "true");
      openBtn.setAttribute("aria-expanded", "true");

      if (!CSS.supports("scroll-initial-target", "nearest")) {
        scroller.scrollTo({ left: scroller.offsetWidth, behavior: "instant" });
        await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      }
      scroller.scrollTo({ left: 0, behavior: "auto" });
    };

    const closeDrawer = () => {
      if (!mobileQuery.matches) return;
      scroller.scrollTo({ left: scroller.offsetWidth, behavior: "auto" });
    };

    const onDrawerClosed = () => {
      if (!drawer.hasAttribute("aria-modal")) return;
      if (typeof drawer.hidePopover === "function") {
        try {
          drawer.hidePopover();
        } catch (_) {}
      }
      mainContent.inert = false;
      drawer.removeAttribute("aria-modal");
      openBtn.setAttribute("aria-expanded", "false");
      openBtn.focus();
    };

    if (!CSS.supports("animation-timeline: scroll()")) {
      scroller.addEventListener("scroll", () => {
        if (!mobileQuery.matches || !sheet.offsetWidth) return;
        const ratio = Math.max(0, Math.min(1, 1 - scroller.scrollLeft / sheet.offsetWidth));
        drawer.style.setProperty("--drawer-backdrop", ratio.toFixed(3));
      });
    }

    const visibleThreshold = 1 / Math.max(window.innerWidth, 320);
    const observer = new IntersectionObserver(
      (entries) => {
        if (!mobileQuery.matches) return;
        const entry = entries[entries.length - 1];
        if (entry.intersectionRatio < visibleThreshold) onDrawerClosed();
        if (entry.intersectionRatio === 1) openBtn.setAttribute("aria-expanded", "true");
      },
      { root: drawer, threshold: [visibleThreshold, 1] }
    );
    observer.observe(sheet);

    openBtn.addEventListener("click", openDrawer);
    closeBtn.addEventListener("click", closeDrawer);
    drawer.addEventListener("click", (event) => {
      if (mobileQuery.matches && !sheet.contains(event.target)) {
        closeDrawer();
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && drawer.hasAttribute("aria-modal")) {
        closeDrawer();
      }
    });
  }

  // -------------------------------------------------------------------------
  // 2. Responsive Table Label Variables (--label-N for mobile cards)
  // -------------------------------------------------------------------------
  document.querySelectorAll(".data-table").forEach((table) => {
    const headers = table.querySelectorAll("thead th");
    headers.forEach((th, idx) => {
      const colNumber = idx + 1;
      const safeLabel = th.textContent.trim().replace(/"/g, '\\"');
      table.style.setProperty(`--label-${colNumber}`, `"${safeLabel}"`);
    });
  });

  // -------------------------------------------------------------------------
  // 3. Accessible Form Validation (:user-invalid + WeakMap Fallback + ARIA)
  // -------------------------------------------------------------------------
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

  const announcer = document.createElement("div");
  announcer.setAttribute("aria-live", "polite");
  announcer.classList.add("visually-hidden");
  document.body.append(announcer);
  let announceTimer;
  let announcedField;

  const spokenText = (node) => {
    const copy = node.cloneNode(true);
    copy.querySelectorAll('[aria-hidden="true"]').forEach((n) => n.remove());
    copy.querySelectorAll('[role="img"][aria-label]').forEach((n) =>
      n.replaceWith(`${n.getAttribute("aria-label")}: `)
    );
    return copy.textContent.replace(/\s+/g, " ").trim();
  };

  const announceError = (el) => {
    const error = document.getElementById(el.dataset.error);
    if (!error) return;
    const label = el.labels?.[0] ? `${spokenText(el.labels[0])}: ` : "";
    clearTimeout(announceTimer);
    announcer.textContent = "";
    announcedField = el;
    announceTimer = setTimeout(() => {
      announcer.textContent = label + spokenText(error);
    }, 500);
  };

  if (CSS.supports("selector(:user-invalid)")) {
    const flagged = new WeakSet();
    const announced = new WeakSet();
    const syncAria = (el, announce = false) => {
      if (!el.matches?.("input, select, textarea")) return;
      const invalid = el.matches(":user-invalid");
      if (invalid) {
        if (announce && !announced.has(el)) {
          announceError(el);
          announced.add(el);
        }
        el.setAttribute("aria-invalid", "true");
        linkError(el, true);
        flagged.add(el);
      } else if (flagged.has(el) || el.getAttribute("aria-invalid") !== "true") {
        el.setAttribute("aria-invalid", "false");
        linkError(el, false);
        flagged.delete(el);
        announced.delete(el);
        if (announcedField === el) {
          clearTimeout(announceTimer);
          announcer.textContent = "";
        }
      }
    };

    document.querySelectorAll("input, select, textarea").forEach((el) => syncAria(el));
    document.addEventListener("blur", (e) => syncAria(e.target, true), true);
    document.addEventListener("input", (e) => {
      if (e.target.hasAttribute("aria-invalid")) syncAria(e.target);
    });
    document.addEventListener("change", (e) => syncAria(e.target, true), true);
    document.addEventListener(
      "invalid",
      (e) => {
        announced.add(e.target);
        syncAria(e.target);
      },
      true
    );
  } else {
    // WeakMap fallback for browsers lacking :user-invalid
    const dirtyState = new WeakMap();
    const updateFallback = (input) => {
      const isValid = input.validity.valid;
      input.classList.toggle("user-invalid-fallback", !isValid);
      input.classList.toggle("user-valid-fallback", isValid);
      input.setAttribute("aria-invalid", isValid ? "false" : "true");
      linkError(input, !isValid);
    };
    document.querySelectorAll("input, select, textarea").forEach((el) => {
      if (!el.hasAttribute("aria-invalid")) el.setAttribute("aria-invalid", "false");
    });
    document.addEventListener(
      "blur",
      (e) => {
        const input = e.target;
        if (!input.checkValidity) return;
        const st = dirtyState.get(input) || { hasInteracted: false, hasBlurred: false };
        st.hasBlurred = true;
        dirtyState.set(input, st);
        if (st.hasInteracted) updateFallback(input);
      },
      true
    );
    document.addEventListener("input", (e) => {
      const input = e.target;
      if (!input.checkValidity) return;
      const st = dirtyState.get(input) || { hasInteracted: false, hasBlurred: false };
      st.hasInteracted = true;
      dirtyState.set(input, st);
      if (st.hasBlurred) updateFallback(input);
    });
    document.addEventListener(
      "invalid",
      (e) => {
        dirtyState.set(e.target, { hasInteracted: true, hasBlurred: true });
        updateFallback(e.target);
      },
      true
    );
  }

  // Prevent invalid native submission & move focus to first invalid field
  document.querySelectorAll("form.atm-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        const firstInvalid = form.querySelector(":invalid");
        if (firstInvalid) firstInvalid.focus();
      }
    });
  });

  // -------------------------------------------------------------------------
  // 4. Quick Amount Chips & Print Buttons
  // -------------------------------------------------------------------------
  document.querySelectorAll("[data-fill-target]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = document.getElementById(btn.dataset.fillTarget);
      if (!target) return;
      target.value = btn.dataset.fillValue;
      target.dispatchEvent(new Event("input", { bubbles: true }));
      target.focus();
    });
  });

  document.querySelectorAll("[data-print-btn]").forEach((btn) => {
    btn.addEventListener("click", () => window.print());
  });

  // -------------------------------------------------------------------------
  // 5. Native Modal <dialog> Invoker Fallback & returnValue Reset
  // -------------------------------------------------------------------------
  const resetDialog = document.getElementById("reset-dialog");
  const openResetBtn = document.getElementById("open-reset-dialog");
  if (resetDialog) {
    resetDialog.addEventListener("close", () => {
      resetDialog.returnValue = "";
    });
    if (openResetBtn && !("commandForElement" in HTMLButtonElement.prototype)) {
      openResetBtn.addEventListener("click", () => resetDialog.showModal());
    }
  }

  // -------------------------------------------------------------------------
  // 6. Transaction Sequence Builder & Mode Switcher
  // -------------------------------------------------------------------------
  const seqContainer = document.getElementById("seq-rows-container");
  const addRowBtn = document.getElementById("add-seq-row");
  const loadExampleBtn = document.getElementById("load-example-seq");
  const builderPanel = document.getElementById("builder-panel");
  const textPanel = document.getElementById("text-panel");
  const inputModeField = document.getElementById("input_mode");
  const sequenceTextarea = document.getElementById("sequence_text");
  const modeTabs = document.querySelectorAll("[data-seq-mode]");

  const renumberSequenceRows = () => {
    if (!seqContainer) return;
    seqContainer.querySelectorAll(".seq-row").forEach((row, index) => {
      const num = index + 1;
      const badge = row.querySelector(".seq-step-badge");
      if (badge) badge.textContent = `#${num}`;
      const sel = row.querySelector("select");
      if (sel) sel.setAttribute("aria-label", `Transaction Type for step ${num}`);
      const amt = row.querySelector('input[name="amount[]"]');
      if (amt) amt.setAttribute("aria-label", `Amount for step ${num}`);
      const desc = row.querySelector('input[name="description[]"]');
      if (desc) desc.setAttribute("aria-label", `Description for step ${num}`);
      const rem = row.querySelector("[data-remove-row]");
      if (rem) rem.setAttribute("aria-label", `Remove step ${num}`);
    });
  };

  const createSequenceRow = (type = "DEPOSIT", amount = "", description = "") => {
    const row = document.createElement("div");
    row.className = "seq-row";
    row.innerHTML = `
      <span class="seq-step-badge">#1</span>
      <div class="seq-field">
        <select name="txn_type[]">
          <option value="DEPOSIT">DEPOSIT</option>
          <option value="WITHDRAWAL">WITHDRAWAL</option>
        </select>
      </div>
      <div class="seq-field">
        <input type="text" name="amount[]" inputmode="decimal" placeholder="Amount (₹)" required>
      </div>
      <div class="seq-field seq-field-desc">
        <input type="text" name="description[]" placeholder="Optional description">
      </div>
      <button type="button" class="btn-icon-remove" data-remove-row title="Remove step">&times;</button>
    `;
    row.querySelector("select").value = type;
    row.querySelector('input[name="amount[]"]').value = amount;
    row.querySelector('input[name="description[]"]').value = description;
    return row;
  };

  if (seqContainer) {
    seqContainer.addEventListener("click", (e) => {
      const removeBtn = e.target.closest("[data-remove-row]");
      if (!removeBtn) return;
      const rows = seqContainer.querySelectorAll(".seq-row");
      if (rows.length <= 1) return;
      removeBtn.closest(".seq-row").remove();
      renumberSequenceRows();
    });
  }

  if (addRowBtn && seqContainer) {
    addRowBtn.addEventListener("click", () => {
      seqContainer.appendChild(createSequenceRow("DEPOSIT", "", ""));
      renumberSequenceRows();
    });
  }

  if (loadExampleBtn && seqContainer) {
    loadExampleBtn.addEventListener("click", () => {
      const exampleSteps = [
        ["DEPOSIT", "2000", "Allowance Deposit"],
        ["WITHDRAWAL", "500", "ATM Cash Withdrawal"],
        ["DEPOSIT", "1000", "Refund Credit"],
        ["WITHDRAWAL", "3000", "Bookstore Cash"],
        ["WITHDRAWAL", "15000", "High-Value Attempt (Exceeds Limit)"],
      ];
      seqContainer.innerHTML = "";
      exampleSteps.forEach(([t, a, d]) => {
        seqContainer.appendChild(createSequenceRow(t, a, d));
      });
      renumberSequenceRows();
      if (sequenceTextarea) {
        sequenceTextarea.value = exampleSteps
          .map(([t, a, d]) => `${t} ${a} | ${d}`)
          .join("\n");
      }
    });
  }

  if (modeTabs.length && builderPanel && textPanel && inputModeField) {
    modeTabs.forEach((tab) => {
      tab.addEventListener("click", () => {
        const mode = tab.dataset.seqMode;
        inputModeField.value = mode;
        modeTabs.forEach((t) => {
          const active = t === tab;
          t.classList.toggle("is-active", active);
          t.setAttribute("aria-selected", active ? "true" : "false");
        });
        builderPanel.classList.toggle("is-hidden", mode !== "builder");
        textPanel.classList.toggle("is-hidden", mode !== "text");
      });
    });
  }
})();
