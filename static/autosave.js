// static/autosave.js
(() => {
  'use strict';

  const SAVE_DELAY = 600; // ms
  const timers = new WeakMap();   // form -> timeout id
  const lastSent = new WeakMap(); // form -> serialized snapshot
  const inflight = new WeakMap(); // form -> Promise

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function serialize(form) {
    const fd = new FormData(form);
    // Ensure autosave marker (if present) doesn't affect snapshots
    fd.delete('autosave');
    const pairs = [];
    for (const [k, v] of fd) pairs.push([k, typeof v === 'string' ? v : '']);
    return new URLSearchParams(pairs).toString();
  }

  function hasChanges(form) {
    return serialize(form) !== lastSent.get(form);
  }

  function setIndicator(form, text, state = '') {
    const el = $('.saved-indicator', form);
    if (!el) return;
    el.hidden = false;
    el.textContent = text;
    el.dataset.state = state;
    if (state === 'done') setTimeout(() => { el.hidden = true; }, 900);
  }

  async function doSave(form, { beacon = false } = {}) {
    if (!form.matches('[data-autosave]')) return;
    clearTimeout(timers.get(form));

    // No changes but maybe an earlier save is still running
    if (!hasChanges(form)) return inflight.get(form);

    const snap = serialize(form);

    // Try sendBeacon for last-chance flushes
    if (beacon && navigator.sendBeacon) {
      try {
        const fd = new FormData(form);
        fd.set('autosave', '1');
        const params = new URLSearchParams();
        for (const [k, v] of fd) params.append(k, v);
        const blob = new Blob([params.toString()], {
          type: 'application/x-www-form-urlencoded;charset=UTF-8'
        });
        const ok = navigator.sendBeacon(form.action || '/update', blob);
        if (ok) {
          lastSent.set(form, snap); // optimistic
        }
        return;
      } catch { /* fallback to fetch below if beacon fails */ }
    }

    setIndicator(form, 'Saving…', 'saving');

    const p = fetch(form.action || '/update', {
      method: form.method || 'POST',
      body: (() => { const fd = new FormData(form); fd.set('autosave', '1'); return fd; })(),
      headers: { 'X-Autosave': '1' },
      keepalive: true
    })
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      lastSent.set(form, snap);
      setIndicator(form, 'Saved ✓', 'done');
    })
    .catch(err => {
      console.error('Autosave error:', err);
      setIndicator(form, 'Save failed', 'error');
    })
    .finally(() => {
      inflight.delete(form);
    });

    inflight.set(form, p);
    return p;
  }

  function scheduleSave(form) {
    if (!form.matches('[data-autosave]')) return;
    clearTimeout(timers.get(form));
    const t = setTimeout(() => { void doSave(form); }, SAVE_DELAY);
    timers.set(form, t);
  }

  async function flushAll({ beacon = false } = {}) {
    const forms = $$('form[data-autosave]');
    const saves = [];
    for (const form of forms) {
      if (hasChanges(form)) {
        saves.push(doSave(form, { beacon }));
      } else if (inflight.get(form)) {
        saves.push(inflight.get(form));
      }
    }
    await Promise.allSettled(saves);
  }

  function init() {
    $$('form[data-autosave]').forEach(form => {
      lastSent.set(form, serialize(form));
    });

    // Debounced save while typing
    document.addEventListener('input', (e) => {
      const form = e.target.closest('form[data-autosave]');
      if (form) scheduleSave(form);
    });

    // Immediate save on blur
    document.addEventListener('blur', (e) => {
      const form = e.target.closest('form[data-autosave]');
      if (form) void doSave(form);
    }, true);

    // Flush before navigating via links
    document.addEventListener('click', (e) => {
      const a = e.target.closest('a[href]');
      if (!a) return;

      const modifiedClick =
        e.metaKey || e.ctrlKey || e.shiftKey || e.altKey ||
        e.button !== 0 || (a.target && a.target !== '' && a.target !== '_self');

      if (modifiedClick) {
        // New tab/window: fire-and-forget flush so the new page sees latest data
        void flushAll();
        return; // don't block default behavior
      }

      e.preventDefault();
      // Block navigation until pending saves finish
      flushAll().then(() => { window.location.href = a.href; });
    }, true);

    // Flush before submitting non-autosave forms (move/delete/add)
    document.addEventListener('submit', (e) => {
      const form = e.target;
      if (form.matches('form[data-autosave]')) return; // their submit is fine
      e.preventDefault();
      flushAll().then(() => form.submit());
    }, true);

    // Last-chance flush on page hide (close tab, navigate away, back/forward cache)
    window.addEventListener('pagehide', () => {
      void flushAll({ beacon: true });
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();