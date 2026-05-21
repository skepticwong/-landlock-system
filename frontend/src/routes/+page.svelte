<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';

	onMount(() => {
		if (browser) {
			goto('/dashboard');
		}
	});
</script>
