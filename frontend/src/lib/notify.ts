// src/lib/notify.ts
// System-styled notifications (toasts, confirm and prompt dialogs)
// that replace the browser's native alert()/confirm()/prompt() dialogs.
import { writable } from "svelte/store";

export type ToastType = "success" | "error" | "info";

export interface ToastAction {
  label: string;
  onClick: () => void;
}

export interface Toast {
  id: number;
  type: ToastType;
  message: string;
  duration: number;
  action: ToastAction | null;
}

export type DialogInputType = "text" | "password" | "number";

export interface DialogState {
  type: "confirm" | "prompt";
  title: string;
  message?: string;
  confirmText: string;
  cancelText: string;
  danger?: boolean;
  value: string;
  inputType?: DialogInputType;
  placeholder?: string;
  resolve: (result: unknown) => void;
}

const MAX_TOASTS = 5;

export const toasts = writable<Toast[]>([]);

let toastSeq = 0;
// id -> timeout handle (live timers only; paused toasts are removed)
const timers = new Map<number, ReturnType<typeof setTimeout>>();

function armTimer(id: number, duration: number) {
  if (duration <= 0) return; // duration 0 = persistent
  const handle = timers.get(id);
  if (handle) clearTimeout(handle);
  timers.set(
    id,
    setTimeout(() => {
      timers.delete(id);
      dismissToast(id);
    }, duration),
  );
}

/**
 * Show a system-styled toast notification.
 * @param type 'success' | 'error' | 'info'
 * @param message text to display
 * @param duration ms before auto-dismiss; 0 keeps it until dismissed
 * @param action optional action button (e.g. "Undo", "View")
 * @returns toast id (pass to dismissToast / updateToast)
 */
export function showToast(
  type: ToastType,
  message: string,
  duration = 4000,
  action: ToastAction | null = null,
): number {
  const id = ++toastSeq;
  toasts.update((list) => {
    const next: Toast[] = [...list, { id, type, message, duration, action }];
    // Cap the stack — drop oldest toasts beyond the limit
    return next.length > MAX_TOASTS
      ? next.slice(next.length - MAX_TOASTS)
      : next;
  });
  armTimer(id, duration);
  return id;
}

export function dismissToast(id: number) {
  const handle = timers.get(id);
  if (handle) clearTimeout(handle);
  timers.delete(id);
  toasts.update((list) => list.filter((t) => t.id !== id));
}

/** Update the message (or everything) of an existing toast in place. */
export function updateToast(id: number, changes: Partial<Toast>) {
  toasts.update((list) =>
    list.map((t) => (t.id === id ? { ...t, ...changes } : t)),
  );
}

/** Dismiss every toast immediately (useful on route change). */
export function dismissAllToasts() {
  for (const handle of timers.values()) clearTimeout(handle);
  timers.clear();
  toasts.set([]);
}

/** Internal: pause a toast's auto-dismiss timer (called on mouseenter). */
export function _pauseToast(id: number) {
  const handle = timers.get(id);
  if (handle) clearTimeout(handle);
  timers.delete(id);
}

/** Internal: restart a toast's auto-dismiss timer (called on mouseleave). */
export function _resumeToast(id: number) {
  let current: Toast[] = [];
  const unsub = toasts.subscribe((v) => (current = v));
  unsub();
  const toast = current.find((t) => t.id === id);
  if (toast) armTimer(id, toast.duration || 4000);
}

// ── Dialog state (confirm / prompt) ─────────────────────────────
export const dialog = writable<DialogState | null>(null);

export interface ConfirmOptions {
  title?: string;
  confirmText?: string;
  cancelText?: string;
  danger?: boolean;
}

/**
 * System-styled confirm dialog. Resolves true/false like confirm().
 */
export function confirmDialog(
  message: string,
  {
    title = "Please confirm",
    confirmText = "Confirm",
    cancelText = "Cancel",
    danger = false,
  }: ConfirmOptions = {},
): Promise<boolean> {
  return new Promise((resolve) => {
    dialog.set({
      type: "confirm",
      title,
      message,
      confirmText,
      cancelText,
      danger,
      value: "",
      resolve: resolve as (result: unknown) => void,
    });
  });
}

export interface PromptOptions {
  title?: string;
  confirmText?: string;
  cancelText?: string;
  value?: string;
  placeholder?: string;
  /** input type for masked/numeric entry (PINs, amounts) */
  inputType?: DialogInputType;
}

/**
 * System-styled prompt dialog. Resolves the entered string or null like prompt().
 */
export function promptDialog(
  message: string,
  {
    title = "Input required",
    confirmText = "OK",
    cancelText = "Cancel",
    value = "",
    placeholder = "",
    inputType = "text",
  }: PromptOptions = {},
): Promise<string | null> {
  return new Promise((resolve) => {
    dialog.set({
      type: "prompt",
      title,
      message,
      confirmText,
      cancelText,
      value,
      placeholder,
      inputType,
      resolve: resolve as (result: unknown) => void,
    });
  });
}

/** Internal: close the active dialog with a result. */
export function _resolveDialog(result: unknown) {
  dialog.update((d) => {
    if (d) d.resolve(result);
    return null;
  });
}
