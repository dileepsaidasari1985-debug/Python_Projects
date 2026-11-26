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
    openBtn.addEventListener("click", async () => {
      if (!mq.matches) return;
      if (typeof drawer.showPopover === "function") drawer.showPopover();
      mainShell.inert = true; drawer.setAttribute("aria-modal", "true"); openBtn.setAttribute("aria-expanded", "true");
      scroller.scrollTo({ left: 0, behavior: "auto" });
    });
    const closeDrawer = () => { if (mq.matches) scroller.scrollTo({ left: scroller.offsetWidth, behavior: "auto" }); };
    closeBtn.addEventListener("click", closeDrawer);
    drawer.addEventListener("click", (e) => { if (!sheet.contains(e.target)) closeDrawer(); });
  }
})();
