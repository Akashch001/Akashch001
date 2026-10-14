# Contributing to Pronab Chakraborty's Profile Assets

Thank you for contributing to this profile repository. The assets in this repository power the live GitHub profile for [Pronab Chakraborty (@Akashch001)](https://github.com/Akashch001).

Because these assets are animated SVGs rendered directly by GitHub's markdown parser and cached by GitHub Camo, all contributions must adhere to strict security, performance, and visual fidelity standards.

---

## Quick Reference: Local Commands

Before submitting any pull request, run the test suite and asset validator locally:

```bash
# Run the unit test suite
python3 -m unittest discover -s tests -p "test_*.py" -v

# Run the asset validator against the repository
python3 scripts/validate_assets.py --verbose
```

All CI checks in `.github/workflows/validate-assets.yml` run these exact commands with minimal read-only permissions (`contents: read`).

---

## 1. How to Update Assets

The repository contains five primary animated SVGs and two source portrait PNGs:
- `assets/hero.svg`: Hero banner with portrait, floating role pill badges, and status indicator.
- `assets/about-life.svg`: Story & philosophy dashboard with interactive/visual metrics.
- `assets/stack.svg`: Technical capabilities ecosystem with rotating orbit paths and category pill grids.
- `assets/id-dashboard.svg`: Developer ID card with portrait, credentials, and animated verification ring.
- `assets/connect.svg`: Terminal-themed contact & channels showcase.
- `assets/id.png`: High-resolution source portrait for the ID card.
- `assets/right_pointing.png`: High-resolution source portrait for the hero banner.

### Rules for Modifying SVGs
1. **Self-Containment**: SVGs must be 100% self-contained. All styles, animations, keyframes, and font definitions must reside inside `<style>` tags within each SVG.
2. **Zero External Rendering Dependencies**:
   - Do **NOT** use external stylesheets (`<?xml-stylesheet ...?>` or `<link rel="stylesheet">`).
   - Do **NOT** use CSS `@import url(...)` pointing to external URLs.
   - Do **NOT** load external images via `<image href="https://...">`.
   - Do **NOT** include `<script>` tags or inline JavaScript handlers (`onload`, `onclick`).
   - Do **NOT** include `<foreignObject>` elements (GitHub's SVG sanitizer strips or blocks them).
3. **Internal Reference Integrity**:
   - Element IDs (`id="..."`) must be unique within each SVG file.
   - Gradients, clip paths, masks, and filters (`url(#id)`) must resolve to valid elements within the same file.
4. **Allowed Destination Hyperlinks**:
   - Destination hyperlinks (`<a href="https://..." target="_blank">`) are permitted for user navigation (e.g. clicking a project or social link). The validator distinguishes navigation hyperlinks from resources loaded during rendering.

---

## 2. Preserving Portrait Bytes & Generating Base64

The source portrait PNGs (`assets/id.png` and `assets/right_pointing.png`) are embedded directly into `assets/id-dashboard.svg` and `assets/hero.svg` as base64 data URIs:
```xml
<image href="data:image/png;base64,..." width="..." height="..." />
```

To maintain byte-level fidelity and prevent regression or visual distortion, the validator enforces that the embedded base64 data decodes to the exact SHA-256 hash of the corresponding file in `assets/`.

### Inspecting Portrait Hashes
```bash
shasum -a 256 assets/*.png
```

### Encoding New Portraits to Base64
If the portrait PNGs are legitimately updated with approved artwork:
1. Ensure the new PNG has genuine alpha transparency (see below).
2. Save the new PNG into `assets/` (e.g., `assets/id.png`).
3. Generate the clean base64 string:
   - **macOS**:
     ```bash
     base64 -i assets/id.png | tr -d '\n' > assets/id.base64.txt
     ```
   - **Linux**:
     ```bash
     base64 -w 0 assets/id.png > assets/id.base64.txt
     ```
4. Replace the base64 payload in the respective SVG's `<image href="data:image/png;base64,...">` attribute.
5. Remove any temporary `.base64.txt` files and run `python3 scripts/validate_assets.py`.

### Genuine Alpha Transparency Requirement
All portrait PNGs must contain a true alpha channel (Color Type 6: 8-bit RGBA) with varying transparency levels. Purely opaque images (Color Type 2: RGB, or 100% solid alpha) will look blocky or produce white halos against GitHub's dark/light canvas backgrounds and will be rejected by `validate_assets.py`.

---

## 3. Retaining Licenses and Typography

All typography rendered across the SVGs uses approved open-source typefaces with embedded WOFF2 font subsets:
- **Plus Jakarta Sans**: Primary UI and display font.
- **Outfit**: Headings and brand titles.
- **JetBrains Mono**: Terminal, code blocks, metrics, and monospaced badges.

### Preserving Licenses
- The full license texts must be retained under `licenses/`:
  - `licenses/PLUS_JAKARTA_SANS_OFL.txt` (SIL Open Font License 1.1)
  - `licenses/OUTFIT_OFL.txt` (SIL Open Font License 1.1)
  - `licenses/JETBRAINS_MONO_OFL.txt` (SIL Open Font License 1.1)
  - `licenses/PORTFOLIO_MIT_LICENSE.txt` (MIT License)
- If you add or modify a font family, you must place its corresponding license file into `licenses/` and update `REQUIRED_LICENSES` in `scripts/validate_assets.py`.
- Keep source records in `SOURCES.md` up to date.

---

## 4. Refreshing README Image Version Strings (Camo Cache Busting)

GitHub routes all markdown image references through an internal caching proxy called **Camo** (`camo.githubusercontent.com`).

Whenever you modify any SVG in `assets/`, GitHub Camo will continue serving the old cached version unless the URL query string in `README.md` is changed:

```markdown
<!-- Before update (v=2) -->
<img src="assets/hero.svg?v=2" alt="Pronab Chakraborty Hero Banner" width="100%" />

<!-- After update (bump to v=3) -->
<img src="assets/hero.svg?v=3" alt="Pronab Chakraborty Hero Banner" width="100%" />
```

### Version String Checklist
- [ ] If any SVG file in `assets/` is modified, increment the version query parameter (`?v=3`, `?v=4`, etc.) on all corresponding `<img>` tags in `README.md`.
- [ ] Ensure all 5 SVG references in `README.md` use the updated version string.
- [ ] Run `python3 scripts/validate_assets.py` to confirm that the validator resolves the local files while correctly ignoring the query string.

---

## 5. Concise Visual-Review Checklist

Static validation verifies syntax, security, and bytes, but **visual and animation quality must be verified in a real browser**. Reviewers and contributors must complete this checklist before submitting or merging changes:

### 1. Clipping & Viewport Bounds
- [ ] Verify that outer card borders, drop-shadows, glow filters, and corner radiuses (`rx="16"`) are not clipped by the SVG `viewBox`.
- [ ] Verify that floating badges, tooltips, or orbital icons do not clip at the edges during extreme animation cycles.
- [ ] Ensure text strings fit within their designated pill badges or containers with at least 8px padding on both sides.

### 2. Mobile Readability (375px & 430px)
- [ ] Resize browser down to **375px** (iPhone SE) and **430px** (iPhone 14/15/16 Pro Max).
- [ ] Confirm all typography remains legible without awkward wrapping, overlapping words, or truncation.
- [ ] Verify that multi-column cards (such as the 3 stat cards in `about-life.svg` and the 2 columns in `stack.svg`) scale proportionately down to mobile widths.

### 3. Reduced Motion (`prefers-reduced-motion: reduce`)
- [ ] Enable reduced motion in your operating system or browser DevTools (`Rendering` -> `Emulate CSS media feature prefers-reduced-motion: reduce`).
- [ ] Verify that all continuous animations (rotating orbit rings, moving badge tracks, pulsing indicators) pause immediately.
- [ ] Confirm that when paused, all elements remain visible, fully legible, and properly aligned (no elements frozen halfway off-screen or at zero opacity).

### 4. Animation Fallback & Static Rendering
- [ ] Verify that if CSS animation is not executed (e.g. static raster export, print preview, or non-CSS SVG renderers), each SVG displays an informative, complete default state.
- [ ] Confirm that key information (name, pitch, credentials, stack categories) does not rely solely on animation to be readable.

---

## Pull Request Guidelines

1. Create a descriptive branch from the latest `main` (e.g., `feat/...` or `fix/...`).
2. Run `python3 -m unittest discover -s tests -p "test_*.py"` and `python3 scripts/validate_assets.py`.
3. Verify the visual checklist in Chrome/Firefox/Safari.
4. Open a pull request against `main`. Ensure all CI checks pass.
