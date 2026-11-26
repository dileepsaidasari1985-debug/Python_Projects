(() => {
  "use strict";
  const drawer = document.getElementById("drawer");
  const openBtn = document.getElementById("drawer-open");
  const closeBtn = document.getElementById("drawer-close");
  const mainShell = document.getElementById("main-shell");
  if (drawer && openBtn && closeBtn && mainShell) {
    const scroller = drawer.querySelector(".Drawer-scroller");
    const sheet = drawer.querySelector(".Drawer-sheet");
    const mq = window.matchMedia("(max-width: 960px)");
    const sync = (mob) => {
      if (mob) { drawer.setAttribute("popover", "manual"); drawer.setAttribute("role", "dialog"); }
      else {
        if (drawer.matches(":popover-open")) { try { drawer.hidePopover(); } catch (_) {} }
        mainShell.inert = false; drawer.removeAttribute("aria-modal"); drawer.removeAttribute("popover"); drawer.removeAttribute("role");
        openBtn.setAttribute("aria-expanded", "false");
      }
    };
    sync(mq.matches); mq.addEventListener("change", (e) => sync(e.matches));
    const openDrawer = async () => {
      if (!mq.matches) return;
      if (typeof drawer.showPopover === "function") drawer.showPopover();
      mainShell.inert = true; drawer.setAttribute("aria-modal", "true"); openBtn.setAttribute("aria-expanded", "true");
      if (!CSS.supports("scroll-initial-target", "nearest")) {
        scroller.scrollTo({ left: scroller.offsetWidth, behavior: "instant" });
        await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
      }
      scroller.scrollTo({ left: 0, behavior: "auto" });
    };
    const closeDrawer = () => { if (mq.matches) scroller.scrollTo({ left: scroller.offsetWidth, behavior: "auto" }); };
    const onClosed = () => {
      if (!drawer.hasAttribute("aria-modal")) return;
      if (typeof drawer.hidePopover === "function") { try { drawer.hidePopover(); } catch (_) {} }
      mainShell.inert = false; drawer.removeAttribute("aria-modal"); openBtn.setAttribute("aria-expanded", "false"); openBtn.focus();
    };
    const threshold = 1 / Math.max(window.innerWidth, 320);
    new IntersectionObserver((entries) => {
      if (!mq.matches) return;
      const last = entries[entries.length - 1];
      if (last.intersectionRatio < threshold) onClosed();
      if (last.intersectionRatio === 1) openBtn.setAttribute("aria-expanded", "true");
    }, { root: drawer, threshold: [threshold, 1] }).observe(sheet);
    openBtn.addEventListener("click", openDrawer);
    closeBtn.addEventListener("click", closeDrawer);
    drawer.addEventListener("click", (e) => { if (!sheet.contains(e.target)) closeDrawer(); });
    document.addEventListener("keydown", (e) => { if (e.key === "Escape" && drawer.hasAttribute("aria-modal")) closeDrawer(); });
  }
  document.querySelectorAll("input, select, textarea").forEach((el) => el.setAttribute("aria-invalid", "false"));
  document.addEventListener("blur", (e) => {
    if (e.target.matches?.("input, select, textarea")) e.target.setAttribute("aria-invalid", e.target.matches(":user-invalid") ? "true" : "false");
  }, true);
})();
