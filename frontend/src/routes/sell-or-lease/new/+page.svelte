<script>
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';

  // Redirect to the transactions/new page (client-side only)
  onMount(() => {
    goto('/transactions/new');
  });
</script>

<!-- Redirecting to transactions/new... -->
