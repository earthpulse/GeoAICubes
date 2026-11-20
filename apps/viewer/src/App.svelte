<script>
  import { onMount } from 'svelte'

  const apiBase = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(
    /\/$/,
    '',
  )

  let health = $state(null)
  let error = $state(null)
  let loading = $state(true)

  onMount(async () => {
    try {
      const res = await fetch(`${apiBase}/health`)
      if (!res.ok) {
        throw new Error(`${res.status} ${res.statusText}`)
      }
      health = await res.json()
    } catch (e) {
      error = e instanceof Error ? e.message : String(e)
    } finally {
      loading = false
    }
  })
</script>

<div class="shell">
  <header class="header">
    <h1>GeoAICubes Viewer</h1>
    <p class="tagline">EarthPulse demo — map layers via API only</p>
  </header>

  <main class="main">
    <div class="map-placeholder" aria-label="Map placeholder">
      <p>Map placeholder</p>
      <span class="hint">Layer tiles and controls land in D2.1</span>
    </div>

    <aside class="panel" aria-labelledby="api-status-heading">
      <h2 id="api-status-heading">API health</h2>
      <p class="api-url">
        <span class="label">Base URL</span>
        <code>{apiBase}</code>
      </p>
      {#if loading}
        <p class="status">Loading…</p>
      {:else if error}
        <p class="status error">Request failed: {error}</p>
      {:else}
        <pre class="json">{JSON.stringify(health, null, 2)}</pre>
      {/if}
    </aside>
  </main>
</div>