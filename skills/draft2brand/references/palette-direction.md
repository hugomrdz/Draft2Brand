# Palette selection from the business brief

Start with the company's real audience, offer, market and intended character. A hospital, children's learning studio, premium workshop and accounting tool can share a color; their contexts and applications should explain the choice. Ask about existing equity, competitors to avoid resembling, regional associations and production constraints when they matter. Browse current competitor identities only when research is requested or needed, and distinguish observed facts from your design judgment.

Offer roughly three clearly different directions when the user wants a choice. Show each on the same draft-derived mark. A useful comparison includes:
- A restrained dark neutral and a light surface.
- A primary brand accent and, when useful, a stronger action/dark-ground accent.
- A supporting tone for quieter fills, with a distinct role rather than a second competing identity.
- Actual dark/light mark panels, small icons and action states. Swatches alone hide common failures.
- A short rationale tied to the brief and one practical tradeoff. Never promise that a color will increase trust, conversions or revenue.

The Klipos five-role pattern is a useful starting point, not a mandatory five-color palette. A one-color craft mark may need fewer colors; a broad product family may need more. Exact colors are company-specific.

For each direction record color name, hex and role. Prefer semantic tokens (`ink`, `paper`, `action-fill`, `action-ink`, `focus-on-dark`) so the set can be reused consistently. Keep literal white/black export backgrounds separate from a brand's chosen light/dark neutrals. Default profile exports may use pure white/black as in v6; state that choice and honor different requested backgrounds.

## Contrast and state decisions

Calculate sRGB relative luminance and contrast, do not judge by eye alone. Use at least 4.5:1 for ordinary body text and action labels; 3:1 is the large-text threshold under the relevant WCAG definitions, not a general exemption for a small button label. Test focus against its adjacent surface (default helper target 3:1). Logo artwork and decorative accent swatches are not functional UI contrast claims.

If a chosen brand green cannot carry small white text, keep the green as artwork and select a readable neutral for that text. Show the issue and proposed role adjustment; don't silently replace the selected color. A pale accent on a light background may work in approved logo artwork but should not become the only visible state indicator. Hover and pressed states must keep label contrast; a soft tint does not automatically mean disabled. Include focus on both dark and light surfaces, and remove unnecessary transitions under reduced motion.

The helper emits exact ratios and fails export on insufficient configured text/action/focus pairings. Its report is a color-pair check, not a full WCAG assessment.

Reference definitions: [W3C text contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) and [W3C non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html). Compare unrounded ratios to the threshold; a rounded 4.50 display does not make 4.499 a pass.
