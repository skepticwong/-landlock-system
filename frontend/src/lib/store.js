// src/lib/store.js
import { writable } from 'svelte/store';

export const plots = writable([]);

export const status = writable('Ready');

export const currentUser = writable(null);

// Helper to reset status after delay
export function setStatus(msg, duration = 3000) {
	status.set(msg);
	setTimeout(() => status.update(s => s.startsWith(msg) ? '' : s), duration);
}