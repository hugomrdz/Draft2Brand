---
name: draft2brand
description: Turn a supplied logo sketch, draft image, or existing mark into an editable vector brand asset kit, with business-informed palette selection, consistent light/dark and monochrome variants, profile PNGs, design tokens, previews, and a reproducible handoff. Use for draft-to-brand identity production; a full brand strategy, website, or stationery project needs its own scope.
---

# Draft2Brand

Build a company-specific identity kit from a visual draft. Preserve the draft's distinguishing idea, select colors deliberately, then generate every export from one approved geometric master. This workflow generalizes the Klipos v6 process; it does not reuse its K, colors, typefaces, wording, or business claims.

## Begin with the image and brief

Inspect the supplied image at useful resolution before drawing. For a local image, use the available image viewer. If no image is attached or accessible, ask for it in conversation; do not substitute an invented reference. An SVG or vector PDF is also a valid starting point.

Use existing context first. Collect only missing essentials together: company name and exact spelling, business/offer, audience/market, desired character, must-keep shapes, and palette preference. The palette path is either **use supplied colors**, **compare suggested palettes**, or **choose for me**. Do not make the user approve choices they have already made or delegated. Ask whether ambiguous features in a rough draft are intentional before making an irreversible design assumption; meanwhile work on clear portions.

Create a dedicated company workspace. Preserve the original draft and earlier iterations. Record the brief, selected direction and approval/delegation status in `brand.json`; never label a proposal owner-approved. Default outputs are a logo/palette asset kit comparable to v6, not a claim that naming, positioning, stationery or packaging has been completed.

## Resolve the geometry

Read [references/vector-workflow.md](references/vector-workflow.md). Compare the silhouette, negative space, proportions, corners, independent accents and optical alignment with the draft. Reconstruct simple geometric marks as clean SVG paths and primitives. Explain any refinement that changes the drawing; present the reconstructed mark beside the draft when it needs a decision. Existing approved vectors keep their geometry.

Use actual vector geometry as the master. Keep paint roles separately editable. Do not place the draft bitmap inside an SVG and call it vector artwork. For complex hand-drawn artwork, use an appropriate tracing/vector tool and inspect its nodes and silhouette. If optional raster concept exploration or editing is requested, use the environment's image-generation/editing tool; its output is a reference for the vector stage, not an automatically approved master. If a needed capability is unavailable, explain the specific limitation.

## Choose a palette in context

Read [references/palette-direction.md](references/palette-direction.md). Use supplied colors as constraints, or propose a small comparison (normally three directions) on the SAME reconstructed mark, light/dark surfaces and real action states. Include exact hex colors, usage roles, a business-specific rationale and calculated contrast. Palette suggestions are design hypotheses, not claims that an industry has universal color psychology.

If the user wants to select, show the comparison and wait for that selection before calling a palette final. Continue geometry/asset preparation while waiting. If selection was delegated, choose a direction, record why, and proceed. Separate palette selection from geometry changes. Once geometry is accepted, recoloring must not change paths, viewBox, radii, transforms or stroke widths.

## Generate the kit

Read [references/export-contract.md](references/export-contract.md) for the schema, command and deliverables. Use `scripts/build_kit.py` with a role-labelled SVG and `brand.json` for flat vector marks. The helper generates SVG variants, square profile PNGs, three preview sheets, a responsive local review page, tokens, numerical contrast results, notes, hashes, rebuild sources and ZIPs. Its runtime is Python 3.10+ and Node 22+ with the pinned Sharp package installed in `scripts/`.

The example files in `assets/` are synthetic tooling examples, not a design to reuse for a real client. Replace their geometry, company metadata and palette. Variant counts follow the mark: the full two-accent setup produces nine SVG exports and 35 PNGs, while a one-part symbol may need fewer distinct variants. Do not add meaningless accent shapes to reach a count.

Use a new version folder for each accepted iteration. The helper refuses to overwrite an existing output directory. It preserves the master geometry across full-mark variants and fits wide and tall marks within the profile canvas and circular crop. Projects needing gradients, textures, complex masks or special print separations should use a project-specific exporter with the same handoff contract; do not silently simplify approved artwork to fit the helper.

## Inspect and hand off

Inspect the actual generated images at large size and at 64/128 px, plus a circular crop. Open `review.html` in a real browser when available; check desktop and phone layouts, light/dark visibility, keyboard focus, hover/pressed states and downloads. Respect reduced motion. The generated audit verifies files, geometry, PNG dimensions/backgrounds and numerical color pairs; it does not certify the entire brand or website as accessible.

Check all generated deliverables and links, reproduce the kit from its copied build sources, and report any unavailable visual/browser check honestly. Offer typography or wordmark lockups only when requested or included in the brief; use legitimate font sources/licenses and outline production logo lettering where appropriate.

Deliver the review page, full-kit ZIP and concise usage notes, with selected colors, decisions and any remaining draft choices. Keep client inputs and earlier studies outside a public skill/plugin distribution. Local kit generation does not publish the skill, deploy a website or update a company's production brand assets.
