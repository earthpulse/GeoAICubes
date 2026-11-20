<script lang="ts">
  import type {
    LayerRenderState,
    MapLayer,
    RenderCapability,
    RenderMode,
    ZarrStoreInventory,
  } from './types/inventory.ts'

  /**
   * @type {{
   *   store: ZarrStoreInventory | null,
   *   layers: MapLayer[],
   *   onRenderChange: (layerId: string, state: LayerRenderState) => void,
   * }}
   */
  let { store, layers, onRenderChange } = $props()

  const activeLayer = $derived.by(() => {
    if (!store) {
      return null
    }
    const renderable = layers.filter(
      (l) => l.storeId === store.id && l.variable && l.status === 'ok',
    )
    const visible = renderable.find((l) => l.visible)
    if (visible) {
      return visible
    }
    const primaryVar = Object.entries(store.render_capabilities ?? {}).find(
      ([, c]) => c.primary,
    )?.[0]
    return (
      renderable.find((l) => l.variable === primaryVar) ?? renderable[0] ?? null
    )
  })

  const capability = $derived.by((): RenderCapability | null => {
    if (!activeLayer) {
      return null
    }
    return store?.render_capabilities?.[activeLayer.variable] ?? null
  })

  const bandDim = $derived(
    capability?.extra_dims.find((d) => ['band', 'bands', 'wavelength'].includes(d.name)),
  )

  function setMode(mode) {
    if (!activeLayer || !capability) {
      return
    }
    const labels = bandDim?.labels ?? []
    let bandSelection = activeLayer.renderState.bandSelection
    if (mode === 'rgb' && bandDim) {
      const fromDefaults = capability.defaults.sel[bandDim.name]
      bandSelection = fromDefaults?.length
        ? fromDefaults.slice(0, 3)
        : labels.slice(0, Math.min(3, labels.length))
    } else if (mode === 'single' && bandDim) {
      bandSelection = [bandSelection[0] ?? labels[0]].filter(Boolean)
    }
    onRenderChange(activeLayer.layerId, {
      ...activeLayer.renderState,
      mode,
      bandSelection,
    })
  }

  function toggleBand(label) {
    if (!activeLayer || !capability || !bandDim) {
      return
    }
    const mode = activeLayer.renderState.mode
  let next = [...activeLayer.renderState.bandSelection]
    if (mode === 'single') {
      next = [label]
    } else if (mode === 'rgb') {
      if (next.includes(label)) {
        next = next.filter((b) => b !== label)
      } else if (next.length < 3) {
        next.push(label)
      } else {
        next = [next[1], next[2], label]
      }
      if (next.length < 3) {
        return
      }
    }
    onRenderChange(activeLayer.layerId, {
      ...activeLayer.renderState,
      bandSelection: next,
    })
  }
</script>

{#if store && capability && activeLayer}
  <section class="viz-panel">
    <h2>Visualization</h2>
    <p class="hint">
      {activeLayer.variable}
      {#if bandDim}
        · {bandDim.name} ({bandDim.labels.length} values)
      {/if}
    </p>

    <fieldset class="modes">
      <legend>Mode</legend>
      {#each capability.modes as mode (mode)}
        <label class="radio">
          <input
            type="radio"
            name="render-mode"
            value={mode}
            checked={activeLayer.renderState.mode === mode}
            onchange={() => setMode(/** @type {RenderMode} */ (mode))}
          />
          {mode}
        </label>
      {/each}
    </fieldset>

    {#if bandDim && activeLayer.renderState.mode !== 'categorical'}
      <div class="bands">
        <p class="subhead">Bands {#if activeLayer.renderState.mode === 'rgb'}(pick 3){:else}(one){/if}</p>
        <div class="band-grid">
          {#each bandDim.labels as label (label)}
            <button
              type="button"
              class="band-chip"
              class:selected={activeLayer.renderState.bandSelection.includes(label)}
              onclick={() => toggleBand(label)}
            >
              {label}
            </button>
          {/each}
        </div>
      </div>
    {/if}

    {#if capability.legend.length > 0 && activeLayer.renderState.mode === 'categorical'}
      <div class="legend">
        <p class="subhead">Legend (class values)</p>
        <ul>
          {#each capability.legend as entry (entry.value)}
            <li>
              <span class="swatch" style="background: {entry.color}"></span>
              <span class="lbl">{entry.label}</span>
            </li>
          {/each}
        </ul>
        <p class="note">Class names can be added later via demo config when metadata provides them.</p>
      </div>
    {/if}
  </section>
{/if}

<style>
  .viz-panel {
    margin-top: 1rem;
    padding: 0.75rem;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--panel-bg, #fff);
  }

  h2 {
    margin: 0 0 0.35rem;
    font-size: 0.95rem;
  }

  .hint,
  .note {
    margin: 0 0 0.5rem;
    font-size: 0.8rem;
    color: var(--muted, #666);
  }

  .modes {
    border: none;
    padding: 0;
    margin: 0 0 0.75rem;
  }

  .modes legend {
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.35rem;
  }

  .radio {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    margin-right: 0.75rem;
    font-size: 0.85rem;
  }

  .subhead {
    margin: 0 0 0.35rem;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .band-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    margin-bottom: 0.75rem;
  }

  .band-chip {
    font-size: 0.75rem;
    padding: 0.2rem 0.45rem;
    border-radius: 4px;
    border: 1px solid var(--border);
    background: var(--chip-bg, #f4f4f5);
    cursor: pointer;
  }

  .band-chip.selected {
    border-color: var(--accent, #2563eb);
    background: color-mix(in srgb, var(--accent, #2563eb) 12%, white);
  }

  .legend ul {
    list-style: none;
    padding: 0;
    margin: 0;
    max-height: 160px;
    overflow: auto;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.25rem 0.5rem;
  }

  .legend li {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.75rem;
  }

  .swatch {
    width: 12px;
    height: 12px;
    border-radius: 2px;
    border: 1px solid #ccc;
    flex-shrink: 0;
  }
</style>