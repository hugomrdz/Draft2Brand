# Draft reconstruction and geometry preservation

The useful sequence from Klipos was draft → geometric reconstruction → reviewed silhouette → palette studies → selected color roles → systematic exports. Later palettes reused the same approved paths. Keep that dependency direction for other companies.

1. Read the image, including negative space. Separate a symbol from a wordmark, background, annotation and screenshot chrome. Identify which components belong together. A photographic crop or pen wobble is not automatically intended geometry.
2. Record a short interpretation: main form, detached accents, grid/radii if apparent, and uncertain features. Preserve exact letters and brand spelling. For a tiny or ambiguous draft, request a better reference or ask about the ambiguous feature.
3. Build a small-node SVG. Prefer paths, rounded rectangles and circles when they reproduce the image. Preserve distinctive asymmetry where intended. Use a tight, stable viewBox with room for strokes. Simplify only with visual justification.
4. Render beside the original at equal visual height. Check large silhouette, counters, apparent weight and 64 px recognition. Present a meaningful revision if needed; don't manufacture alternatives when the user asked for faithful cleanup.
5. Freeze the approved geometry. Use named groups for meaningful parts and color roles, not client-specific hardcoded IDs. Change fills/strokes only for palette variants. Keep a geometry fingerprint and source SVG in the handoff.

## Helper paint contract

Use the SVG namespace and a four-number viewBox. Every explicit non-`none` fill/stroke must belong to a node with `data-brand-role="ink"`, `"accent"`, or `"accent-alt"`. Child nodes may inherit that paint. For strokes add `data-brand-paint="stroke"`; the default is `fill`. Use `fill stroke` when both should recolor. All geometry attributes remain unchanged.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
  <g id="symbol-core" data-brand-role="ink" fill="#172A32">
    <path d="..."/>
  </g>
  <circle data-brand-role="accent" fill="#146B5B" cx="..." cy="..." r="..."/>
</svg>
```

This is a schema illustration, not finished artwork. The working synthetic fixture is in `assets/mark.example.svg`.

The helper accepts flat paths/primitives/groups and internal clip paths. It rejects scripts, embedded rasters, external resources, CSS styling, live text and unsupported SVG elements. If a wordmark is included, outline its approved lettering and keep editable text/source font information separately. Do not change a brand to satisfy tool restrictions; use another exporter when genuinely needed.

An optional `coreGroup` may identify a top-level, self-contained group for an isolated-symbol export. Excluding accents is appropriate only when that version makes sense for the brand. Do not extract an arbitrary path simply to match Klipos's isolated K export.
