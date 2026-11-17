// src/lib/notify.js
// System-styled notifications (toasts, confirm and prompt dialogs)
// that replace the browser's native alert()/confirm()/prompt() dialogs.
import { writable } from "svelte/store";

export const toasts = writable([]);

let toastSeq = 0;

/**
 * Show a system-styled toast notification.
 * @param {'success'|'error'|'info'} type
 * @param {string} message
 * @param {number} duration ms before auto-dismiss
 */
export function showToast(type, message, duration = 4000) {
  const id = ++toastSeq;
  toasts.update((list) => [...list, { id, type, message }]);
  setTimeout(() => dismissToast(id), duration);
  return id;
}

export function dismissToast(id) {
  toasts.update((list) => list.filter((t) => t.id !== id));
}

// ── Dialog state (confirm / prompt) ─────────────────────────────
export const dialog = writable(null); // { type: 'confirm'|'prompt', title, message, confirmText, cancelText, danger, value, resolve }

/**
 * System-styled confirm dialog. Resolves true/false like confirm().
 */
export function confirmDialog(
  message,
  {
    title = "Please confirm",
    confirmText = "Confirm",
    cancelText = "Cancel",
    danger = false,
  } = {},
) {
  return new Promise((resolve) => {
    dialog.set({
      type: "confirm",
      title,
      message,
      confirmText,
      cancelText,
      danger,
      value: "",
      resolve,
    });
  });
}

/**
 * System-styled prompt dialog. Resolves the entered string or null like prompt().
 */
export function promptDialog(
  message,
  {
    title = "Input required",
    confirmText = "OK",
    cancelText = "Cancel",
    value = "",
    placeholder = "",
  } = {},
) {
  return new Promise((resolve) => {
    dialog.set({
      type: "prompt",
      title,
      message,
      confirmText,
      cancelText,
      value,
      placeholder,
      resolve,
    });
  });
}

/** Internal: close the active dialog with a result. */
export function _resolveDialog(result) {
  dialog.update((d) => {
    if (d) d.resolve(result);
    return null;
  });
}
