<script>
  // System-styled notification host: renders all toasts and the
  // global confirm/prompt dialog. Mounted once in the root layout.
  import { fly } from "svelte/transition";
  import { toasts, dismissToast, dialog, _resolveDialog } from "$lib/notify.js";
  import { tick } from "svelte";

  function closeDialog(result) {
    _resolveDialog(result);
  }

  async function submitPrompt() {
    const d = $dialog;
    if (!d) return;
    const value = (d.value ?? "").trim();
    if (!value) return;
    _resolveDialog(value);
  }

  function onDialogKeydown(e) {
    if (!$dialog) return;
    if (e.key === "Escape") {
      e.preventDefault();
      closeDialog(null);
    } else if (e.key === "Enter" && $dialog.type === "prompt") {
      e.preventDefault();
      submitPrompt();
    }
  }

  $: if ($dialog && $dialog.type === "prompt") {
    (async () => {
      await tick();
      const el = document.getElementById("system-dialog-input");
      if (el) {
        el.focus();
        el.select();
      }
    })();
  }
</script>

<!-- ── Toasts ── -->
<div class="sys-toast-region" aria-live="polite">
  {#each $toasts as t (t.id)}
    <div
      class="sys-toast {t.type}"
      role="status"
      transition:fly={{ y: -12, duration: 180 }}
    >
      <div class="sys-toast-icon">
        {#if t.type === "success"}✓{:else if t.type === "error"}!{:else}i{/if}
      </div>
      <span class="sys-toast-msg">{t.message}</span>
      <button
        class="sys-toast-close"
        aria-label="Dismiss notification"
        on:click={() => dismissToast(t.id)}>×</button
      >
    </div>
  {/each}
</div>

<!-- ── Confirm / Prompt dialog ── -->
<svelte:window on:keydown={onDialogKeydown} />

{#if $dialog}
  <div class="sys-dialog-overlay" role="presentation">
    <div
      class="sys-dialog"
      role="dialog"
      aria-modal="true"
      aria-labelledby="sys-dialog-title"
    >
      <h3 id="sys-dialog-title">{$dialog.title}</h3>
      {#if $dialog.message}
        <p class="sys-dialog-msg">{$dialog.message}</p>
      {/if}

      {#if $dialog.type === "prompt"}
        <input
          id="system-dialog-input"
          class="sys-dialog-input"
          type="text"
          bind:value={$dialog.value}
          placeholder={$dialog.placeholder}
        />
      {/if}

      <div class="sys-dialog-actions">
        <button
          class="sys-dialog-btn cancel"
          on:click={() => closeDialog($dialog.type === "prompt" ? null : false)}
        >
          {$dialog.cancelText}
        </button>
        <button
          class="sys-dialog-btn confirm"
          class:danger={$dialog.danger}
          on:click={() =>
            closeDialog(
              $dialog.type === "prompt"
                ? ($dialog.value ?? "").trim() || null
                : true,
            )}
        >
          {$dialog.confirmText}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* ── Toast region ── */
  .sys-toast-region {
    position: fixed;
    top: 1.25rem;
    right: 1.5rem;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    pointer-events: none;
  }

  .sys-toast {
    pointer-events: auto;
    display: flex;
    align-items: center;
    gap: 0.75rem;
    max-width: min(420px, calc(100vw - 3rem));
    padding: 0.875rem 1rem;
    border-radius: 12px;
    border: 1px solid #bbf7d0;
    background: #ffffff;
    color: #14532d;
    box-shadow: 0 12px 32px rgba(15, 23, 42, 0.18);
    font-size: 0.875rem;
    font-weight: 600;
    font-family: inherit;
  }

  .sys-toast.error {
    border-color: #fecaca;
    color: #991b1b;
  }

  .sys-toast.info {
    border-color: #bfdbfe;
    color: #1e3a8a;
  }

  .sys-toast-icon {
    width: 1.5rem;
    height: 1.5rem;
    flex: 0 0 1.5rem;
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: #007a3d;
    color: #ffffff;
    font-size: 0.8rem;
  }

  .sys-toast.error .sys-toast-icon {
    background: #dc2626;
  }

  .sys-toast.info .sys-toast-icon {
    background: #2563eb;
  }

  .sys-toast-msg {
    flex: 1;
  }

  .sys-toast-close {
    margin-left: auto;
    border: 0;
    background: transparent;
    color: inherit;
    cursor: pointer;
    font-size: 1.25rem;
    line-height: 1;
    padding: 0 0.15rem;
  }

  /* ── Dialog ── */
  .sys-dialog-overlay {
    position: fixed;
    inset: 0;
    z-index: 10001;
    display: grid;
    place-items: center;
    background: rgba(15, 23, 42, 0.45);
    backdrop-filter: blur(2px);
  }

  .sys-dialog {
    width: min(400px, calc(100vw - 2.5rem));
    background: #ffffff;
    border-radius: 14px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 24px 64px rgba(15, 23, 42, 0.28);
    padding: 1.35rem 1.4rem 1.2rem;
  }

  .sys-dialog h3 {
    margin: 0 0 0.5rem;
    font-size: 1.05rem;
    color: #0f172a;
  }

  .sys-dialog-msg {
    margin: 0 0 0.75rem;
    font-size: 0.875rem;
    color: #475569;
    line-height: 1.5;
    white-space: pre-line;
  }

  .sys-dialog-input {
    width: 100%;
    box-sizing: border-box;
    padding: 0.6rem 0.75rem;
    margin-bottom: 0.9rem;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-size: 0.9rem;
    font-family: inherit;
    color: #0f172a;
  }

  .sys-dialog-input:focus {
    outline: none;
    border-color: #007a3d;
    box-shadow: 0 0 0 3px rgba(0, 122, 61, 0.15);
  }

  .sys-dialog-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.6rem;
  }

  .sys-dialog-btn {
    padding: 0.55rem 1.05rem;
    border-radius: 8px;
    border: 1px solid #cbd5e1;
    background: #ffffff;
    color: #334155;
    font-size: 0.85rem;
    font-weight: 600;
    font-family: inherit;
    cursor: pointer;
  }

  .sys-dialog-btn.cancel:hover {
    background: #f1f5f9;
  }

  .sys-dialog-btn.confirm {
    border-color: #007a3d;
    background: #007a3d;
    color: #ffffff;
  }

  .sys-dialog-btn.confirm:hover {
    background: #006531;
  }

  .sys-dialog-btn.confirm.danger {
    border-color: #dc2626;
    background: #dc2626;
  }

  .sys-dialog-btn.confirm.danger:hover {
    background: #b91c1c;
  }
</style>
