<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  // Redirect to the transactions page (client-side only)
  onMount(() => {
    goto('/transactions');
  });
</script>

<!-- Redirecting to transactions... -->
