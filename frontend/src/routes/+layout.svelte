<script>
  import { onMount } from 'svelte';
  import { browser } from '$app/environment';
  import { goto } from '$app/navigation';
  import favicon from '$lib/assets/favicon.svg';

  let { children } = $props();

  onMount(() => {
    if (!browser) return;

    const token = localStorage.getItem('token');

    // Purge demo token if present
    if (token === 'demo-token-12345') {
      console.log('Purging demo token...');
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.reload();
      return;
    }

    // If no token, redirect to login for protected routes
    if (!token) {
      // Root should NOT be public — it redirects to dashboard; force login for unauthenticated users
      const publicPaths = ['/login', '/register', '/marketplace', '/listings', '/certificates', '/public-map'];
      const path = window.location.pathname || '/';

      // If user is at root, send them to login when not authenticated
      if (path === '/') {
        try {
          goto('/login');
        } catch (e) {
          window.location.replace('/login');
        }
        return;
      }

      const isPublic = publicPaths.some(p => path === p || path.startsWith(p + '/'));
      if (!isPublic) {
        // Use goto which keeps SPA navigation; fallback to location replace
        try {
          goto('/login');
        } catch (e) {
          window.location.replace('/login');
        }
      }
    }
  });
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

{@render children()}
