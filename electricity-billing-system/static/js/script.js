/**
 * VoltGrid Smart Utility Billing Portal - Frontend Interactions
 * Handles:
 *  1. Accessible mobile navigation drawer (<dialog> + scroll-snap + IntersectionObserver)
 *  2. Native <dialog> confirmation modal for destructive actions
 *  3. Accessible form validation timing (blur -> input -> submit focus) & double-submit guard
 *  4. Print triggers (without inline onclick attributes)
 *  5. Responsive HTML5 Canvas charts for monthly consumption & bill totals
 */

(function () {
  "use strict";

  // ------------------------------------------------------------------------
  // 1. Mobile Navigation Drawer
  // ------------------------------------------------------------------------
  function initNavigationDrawer() {
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
        drawer.style.setProperty("--drawer-backdrop", ratio.toFixed(3));
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

    const visibleThreshold = Math.min(0.05, 1 / Math.max(window.innerWidth, 1));
    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[entries.length - 1];
        if (!entry) return;
        if (entry.intersectionRatio < visibleThreshold && drawer.open) {
          drawer.close();
          openBtn.setAttribute("aria-expanded", "false");
        }
        if (entry.intersectionRatio >= 0.99 && drawer.open) {
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
  }

  // ------------------------------------------------------------------------
  // 2. Native <dialog> Confirmation Modal
  // ------------------------------------------------------------------------
  function initConfirmDialog() {
    const dialog = document.getElementById("confirm-dialog");
    const titleEl = document.getElementById("confirm-dialog-title");
    const msgEl = document.getElementById("confirm-dialog-message");
    const formEl = document.getElementById("confirm-dialog-form");
    const cancelBtn = document.getElementById("confirm-dialog-cancel");
    const submitBtn = document.getElementById("confirm-dialog-submit");
    if (!dialog || !formEl || !cancelBtn) return;

    document.querySelectorAll("[data-confirm-action]").forEach((trigger) => {
      trigger.addEventListener("click", () => {
        formEl.action = trigger.getAttribute("data-confirm-action") || "";
        titleEl.textContent = trigger.getAttribute("data-confirm-title") || "Confirm Action";
        msgEl.textContent = trigger.getAttribute("data-confirm-message") || "Are you sure?";
        submitBtn.textContent = trigger.getAttribute("data-confirm-label") || "Confirm";
        dialog.showModal();
      });
    });

    cancelBtn.addEventListener("click", () => {
      dialog.close("cancel");
    });

    dialog.addEventListener("close", () => {
      dialog.returnValue = "";
    });
  }

  // ------------------------------------------------------------------------
  // 3. Accessible Form Validation Timing & Print Triggers
  // ------------------------------------------------------------------------
  function initFormsAndPrint() {
    document.querySelectorAll("[data-print-btn]").forEach((btn) => {
      btn.addEventListener("click", () => window.print());
    });

    document.querySelectorAll("form[data-validate-form]").forEach((form) => {
      const controls = form.querySelectorAll("input, select, textarea");

      controls.forEach((ctrl) => {
        let touched = false;
        ctrl.addEventListener("blur", () => {
          touched = true;
          if (!ctrl.checkValidity()) {
            ctrl.setAttribute("aria-invalid", "true");
          } else {
            ctrl.removeAttribute("aria-invalid");
          }
        });

        ctrl.addEventListener("input", () => {
          if (touched && ctrl.checkValidity()) {
            ctrl.removeAttribute("aria-invalid");
          }
        });
      });

      form.addEventListener("submit", (event) => {
        if (!form.checkValidity()) {
          event.preventDefault();
          const firstInvalid = form.querySelector(":invalid");
          if (firstInvalid) {
            firstInvalid.setAttribute("aria-invalid", "true");
            firstInvalid.focus();
            firstInvalid.reportValidity();
          }
          return;
        }
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
          submitBtn.disabled = true;
        }
      });
    });
  }

  // ------------------------------------------------------------------------
  // 4. Pure Canvas Charts (Zero external CDN dependency)
  // ------------------------------------------------------------------------
  function prepareCanvas(canvasId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const width = Math.max(rect.width || 480, 280);
    const height = Math.max(rect.height || 260, 220);
    canvas.width = Math.round(width * dpr);
    canvas.height = Math.round(height * dpr);
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    return { ctx, width, height };
  }

  function drawEmptyChart(ctx, width, height, message) {
    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = "#64748b";
    ctx.font = "500 14px Inter, Segoe UI, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(message || "No billing records available", width / 2, height / 2);
  }

  function drawBarChart(canvasId, labels, values, options) {
    const setup = prepareCanvas(canvasId);
    if (!setup) return;
    const { ctx, width, height } = setup;
    if (!labels || labels.length === 0) {
      drawEmptyChart(ctx, width, height, "No monthly data available");
      return;
    }

    const opts = Object.assign(
      { barColor: "#1d6fe8", highlightColor: "#0b192c", unitSuffix: "" },
      options || {}
    );
    const pad = { top: 28, right: 20, bottom: 42, left: 58 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;
    const maxVal = Math.max(...values, 10) * 1.15;
    const peakVal = Math.max(...values);

    ctx.clearRect(0, 0, width, height);

    // Horizontal grid lines
    const steps = 4;
    ctx.font = "500 11px Inter, Segoe UI, sans-serif";
    for (let i = 0; i <= steps; i++) {
      const y = pad.top + (plotH / steps) * i;
      const tickVal = Math.round(maxVal - (maxVal / steps) * i);
      ctx.strokeStyle = "#e2e8f0";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(width - pad.right, y);
      ctx.stroke();

      ctx.fillStyle = "#64748b";
      ctx.textAlign = "right";
      ctx.fillText(String(tickVal), pad.left - 8, y + 4);
    }

    const slotW = plotW / labels.length;
    const barW = Math.min(44, Math.max(16, slotW * 0.54));

    labels.forEach((lbl, idx) => {
      const val = Number(values[idx] || 0);
      const barH = (val / maxVal) * plotH;
      const x = pad.left + slotW * idx + (slotW - barW) / 2;
      const y = pad.top + plotH - barH;

      ctx.fillStyle = val === peakVal && peakVal > 0 ? opts.highlightColor : opts.barColor;
      ctx.beginPath();
      ctx.roundRect(x, y, barW, barH, [6, 6, 0, 0]);
      ctx.fill();

      // Value label above bar
      ctx.fillStyle = "#0f172a";
      ctx.font = "600 11px Inter, Segoe UI, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`${Math.round(val)}`, x + barW / 2, Math.max(14, y - 6));

      // X-axis label
      ctx.fillStyle = "#475569";
      ctx.font = "500 11px Inter, Segoe UI, sans-serif";
      ctx.fillText(lbl, x + barW / 2, height - 16);
    });
  }

  function drawLineChart(canvasId, labels, values, options) {
    const setup = prepareCanvas(canvasId);
    if (!setup) return;
    const { ctx, width, height } = setup;
    if (!labels || labels.length === 0) {
      drawEmptyChart(ctx, width, height, "No monthly billing data available");
      return;
    }

    const opts = Object.assign(
      { lineColor: "#0ea5e9", fillColor: "rgba(29, 111, 232, 0.14)", prefix: "" },
      options || {}
    );
    const pad = { top: 28, right: 24, bottom: 42, left: 66 };
    const plotW = width - pad.left - pad.right;
    const plotH = height - pad.top - pad.bottom;
    const maxVal = Math.max(...values, 100) * 1.15;

    ctx.clearRect(0, 0, width, height);

    const steps = 4;
    ctx.font = "500 11px Inter, Segoe UI, sans-serif";
    for (let i = 0; i <= steps; i++) {
      const y = pad.top + (plotH / steps) * i;
      const tickVal = Math.round(maxVal - (maxVal / steps) * i);
      ctx.strokeStyle = "#e2e8f0";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(width - pad.right, y);
      ctx.stroke();

      ctx.fillStyle = "#64748b";
      ctx.textAlign = "right";
      ctx.fillText(`${opts.prefix}${tickVal.toLocaleString("en-IN")}`, pad.left - 8, y + 4);
    }

    const points = labels.map((lbl, idx) => {
      const val = Number(values[idx] || 0);
      const x =
        labels.length === 1
          ? pad.left + plotW / 2
          : pad.left + (plotW / (labels.length - 1)) * idx;
      const y = pad.top + plotH - (val / maxVal) * plotH;
      return { x, y, val, lbl };
    });

    // Area fill
    if (points.length > 1) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, pad.top + plotH);
      points.forEach((pt) => ctx.lineTo(pt.x, pt.y));
      ctx.lineTo(points[points.length - 1].x, pad.top + plotH);
      ctx.closePath();
      ctx.fillStyle = opts.fillColor;
      ctx.fill();
    }

    // Line stroke
    ctx.beginPath();
    points.forEach((pt, idx) => {
      if (idx === 0) ctx.moveTo(pt.x, pt.y);
      else ctx.lineTo(pt.x, pt.y);
    });
    ctx.strokeStyle = opts.lineColor;
    ctx.lineWidth = 3;
    ctx.stroke();

    // Points + labels
    points.forEach((pt) => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 5, 0, Math.PI * 2);
      ctx.fillStyle = "#ffffff";
      ctx.fill();
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = opts.lineColor;
      ctx.stroke();

      ctx.fillStyle = "#0f172a";
      ctx.font = "600 11px Inter, Segoe UI, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`${opts.prefix}${Math.round(pt.val).toLocaleString("en-IN")}`, pt.x, Math.max(14, pt.y - 10));

      ctx.fillStyle = "#475569";
      ctx.font = "500 11px Inter, Segoe UI, sans-serif";
      ctx.fillText(pt.lbl, pt.x, height - 16);
    });
  }

  window.VoltGridCharts = { drawBarChart, drawLineChart };

  document.addEventListener("DOMContentLoaded", () => {
    initNavigationDrawer();
    initConfirmDialog();
    initFormsAndPrint();
  });
})();
