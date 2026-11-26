(() => {
  "use strict";

  // 1. Responsive Navigation Drawer
  const drawer = document.getElementById("drawer");
  const openBtn = document.getElementById("drawer-open");
  const closeBtn = document.getElementById("drawer-close");
  const mainShell = document.getElementById("main-shell");

  if (drawer && openBtn && closeBtn && mainShell) {
    const scroller = drawer.querySelector(".Drawer-scroller");
    const sheet = drawer.querySelector(".Drawer-sheet");
    const mobileQuery = window.matchMedia("(max-width: 960px)");

    const syncMode = (isMobile) => {
      if (isMobile) {
        drawer.setAttribute("popover", "manual");
        drawer.setAttribute("role", "dialog");
      } else {
        if (drawer.matches(":popover-open")) {
          try { drawer.hidePopover(); } catch (_) {}
        }
        mainShell.inert = false;
        drawer.removeAttribute("aria-modal");
        drawer.removeAttribute("popover");
        drawer.removeAttribute("role");
        openBtn.setAttribute("aria-expanded", "false");
      }
    };
    syncMode(mobileQuery.matches);
    mobileQuery.addEventListener("change", (e) => syncMode(e.matches));

    const openDrawer = async () => {
      if (!mobileQuery.matches) return;
      if (typeof drawer.showPopover === "function") drawer.showPopover();
      mainShell.inert = true;
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

    const onClosed = () => {
      if (!drawer.hasAttribute("aria-modal")) return;
      if (typeof drawer.hidePopover === "function") {
        try { drawer.hidePopover(); } catch (_) {}
      }
      mainShell.inert = false;
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

    const threshold = 1 / Math.max(window.innerWidth, 320);
    const obs = new IntersectionObserver((entries) => {
      if (!mobileQuery.matches) return;
      const last = entries[entries.length - 1];
      if (last.intersectionRatio < threshold) onClosed();
      if (last.intersectionRatio === 1) openBtn.setAttribute("aria-expanded", "true");
    }, { root: drawer, threshold: [threshold, 1] });
    obs.observe(sheet);

    openBtn.addEventListener("click", openDrawer);
    closeBtn.addEventListener("click", closeDrawer);
    drawer.addEventListener("click", (e) => { if (!sheet.contains(e.target)) closeDrawer(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && drawer.hasAttribute("aria-modal")) closeDrawer(); });
  }

  // 2. Responsive table label injection
  document.querySelectorAll("table.responsive-stack").forEach((tbl) => {
    const headers = [...tbl.querySelectorAll("thead th")].map((th) => th.textContent.trim());
    headers.forEach((txt, idx) => {
      tbl.style.setProperty(`--label-${idx + 1}`, JSON.stringify(txt));
    });
  });

  // 3. Accessible form validation error announcement
  const announcer = document.createElement("div");
  announcer.setAttribute("aria-live", "polite");
  announcer.className = "visually-hidden";
  document.body.append(announcer);
  let announceTimer;

  const linkError = (el, shown) => {
    const errorId = el.dataset.error;
    if (!errorId) return;
    const ids = (el.getAttribute("aria-describedby") || "").split(/\s+/).filter((id) => id && id !== errorId);
    if (shown) ids.push(errorId);
    if (ids.length) el.setAttribute("aria-describedby", ids.join(" "));
    else el.removeAttribute("aria-describedby");
  };

  const syncAria = (el, announce = false) => {
    if (!el.matches?.("input, select, textarea")) return;
    const invalid = el.matches(":user-invalid");
    if (invalid) {
      el.setAttribute("aria-invalid", "true");
      linkError(el, true);
      if (announce && el.dataset.error) {
        const msg = document.getElementById(el.dataset.error)?.textContent?.trim();
        if (msg) {
          clearTimeout(announceTimer);
          announceTimer = setTimeout(() => { announcer.textContent = msg; }, 500);
        }
      }
    } else {
      el.setAttribute("aria-invalid", "false");
      linkError(el, false);
    }
  };

  document.querySelectorAll("input, select, textarea").forEach((el) => syncAria(el));
  document.addEventListener("blur", (e) => syncAria(e.target, true), true);
  document.addEventListener("input", (e) => { if (e.target.hasAttribute("aria-invalid")) syncAria(e.target); });
  document.addEventListener("change", (e) => syncAria(e.target, true), true);
  document.addEventListener("invalid", (e) => syncAria(e.target), true);

  // 4. Native confirmation dialog
  const confirmDialog = document.getElementById("confirm-dialog");
  let pendingForm = null;
  if (confirmDialog) {
    document.querySelectorAll("[data-confirm-form]").forEach((btn) => {
      btn.addEventListener("click", () => {
        pendingForm = btn.closest("form");
        const msgEl = document.getElementById("confirm-dialog-msg");
        if (msgEl) msgEl.textContent = btn.dataset.confirmMsg || "Are you sure you want to proceed?";
        confirmDialog.showModal();
      });
    });
    confirmDialog.addEventListener("close", () => {
      const choice = confirmDialog.returnValue;
      confirmDialog.returnValue = "";
      if (choice === "confirm" && pendingForm) pendingForm.submit();
      pendingForm = null;
    });
  }
})();
