# Export contract and runtime

## Setup

Use Python 3.10+ and Node 22+. Install the pinned raster renderer inside this skill, not in an unrelated client website:

```sh
npm ci --prefix /absolute/path/to/draft2brand/scripts
```

Copy `assets/brand.example.json` into the company's workspace and replace the synthetic values. Create the real role-labelled `mark.svg` there; set `source` relative to the JSON file. Inspect `assets/mark.example.svg` for the paint-role convention.

```sh
python3 /absolute/path/to/draft2brand/scripts/build_kit.py \
  /absolute/path/to/company/brand.json \
  --out /absolute/path/to/company/brand-v1
```

Serve the output with `python3 -m http.server 8000 --bind 127.0.0.1 --directory /absolute/path/to/company/brand-v1` and open `http://127.0.0.1:8000/review.html` to test downloads. Stop that preview server after review. Some browsers open file:// SVG links instead of downloading them.

An existing output folder is rejected. Use `brand-v2` for a new iteration. If a build fails after creating its output directory, treat that folder as incomplete; inspect the error and use a new output location. The helper never edits the input image or master.

## Configuration

- `brand`: exact company name; `slug`: lowercase letters/digits/hyphens, beginning with a letter; `version`: `v1`, `v2`, etc.
- `business`: short supplied context; `status`: `draft`, `selected` or `approved`. These are author-provided decisions, not automatic certifications.
- `selection`: record the real geometry and palette approval or delegation. Keep proposals marked as proposals.
- `source`: path to the role-labelled SVG, relative to this config. Preserve the source draft separately; it is not automatically copied into a shareable client kit.
- `colors`: six-digit hex values by semantic name. `ink` and `paper` are required. `colorRoles` explains intended use.
- `variants`: explicit IDs, names, role-to-color-token `paint` maps, a brand-color `background` for review, and a literal `profileBackground`. Include `light`, `dark`, `mono-dark`, `mono-light`; add soft/dual variants only when meaningful. The helper does not redesign the mark or choose palettes.
- `coreGroup`: optional ID of a top-level, self-contained group for an isolated-symbol SVG. Omit when no independent symbol version is appropriate. `coreViewBox` optionally supplies its four-number crop without changing the paths.
- `actions`: color-token references for `fill`, `hover`, `active`, `ink`, `focusOnLight`, `focusOnDark`.
- `profileSizes`: default `[1024, 512, 256, 128, 64]`; include 256 for the review thumbnails. Allowed range 16–4096.
- `notes`: company-specific usage limits and decisions; do not invent business claims.

For a mark with just the `ink` role, all paint maps can contain only `ink`; remove irrelevant soft/dual variants and `coreGroup`. For stroke artwork, follow `data-brand-paint` in the vector workflow. Preserve any geometry the owner has already approved.

## Outputs

| File | Purpose |
| --- | --- |
| `<slug>-master.svg` | Editable monochrome full master |
| `<slug>-<variant>.svg` | Transparent variants from identical geometry |
| `<slug>-core.svg` | Optional isolated symbol |
| `png/<slug>-<variant>-<size>.png` | Opaque RGB square icons/profile images |
| `palette-comparison.png/.svg` | Light/dark marks and color sheet |
| `profile-previews.png/.svg` | Circular-crop overview |
| `mark-preview.png/.svg` | Main mark preview |
| `review.html`, `tokens.css`, `palettes.json` | Portable review and semantic palette roles |
| `REVIEW.txt` | Decisions, usage notes and rebuild command |
| `audit.json`, `raster-audit.json`, `manifest.json` | Geometry fingerprint, ratios, dimensions, backgrounds, hashes |
| `brand.json`, `source/mark.svg` | Rebuild inputs |
| `build_kit.py`, `render.mjs`, `package.json`, `package-lock.json` | Standalone rebuild tools and pinned dependency |
| `<slug>-<version>-pngs.zip` | Profile PNG archive |
| `<slug>-<version>-brand-kit.zip` | Complete kit, including rebuild sources |

The full example uses seven colorways × five sizes, plus master and isolated symbol: nine logo SVGs and 35 profile PNGs. Preview SVGs and the source master are additional supporting files. No dependency on a private repository, earlier brand version, external font or remote asset is required.

To reproduce an exported kit, run `npm ci` in its folder, then `python3 build_kit.py brand.json --out ../rebuilt-kit`. Logo geometry, color mappings and ZIP metadata are deterministic. Preview text uses host sans-serif fonts, so its raster appearance can vary across operating systems. The source mark cannot depend on fonts.

Numerical checks are necessary, not sufficient. Inspect source fidelity, transparent SVG behavior, small marks, circular crops, review downloads and responsive keyboard interaction before describing a kit as delivered. RGB digital assets are not CMYK/Pantone print separations; add those only as a scoped print deliverable.
