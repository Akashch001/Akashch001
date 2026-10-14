# Profile Asset Validator

A lightweight, zero-dependency validation suite designed to protect and verify the integrity, security, and rendering safety of animated GitHub profile README assets in this repository.

---

## 🎯 Purpose & Scope

Animated SVG assets on GitHub profiles operate under strict proxy and browser constraints. This tool provides automated static analysis to catch syntax regressions, security violations, and broken references before changes are merged or pushed to `main`.

---

## 🔍 What the Validator Enforces

| Validation Check | Description | Rule Details |
| :--- | :--- | :--- |
| **README Asset Resolution** | Ensures all 5 profile SVGs are referenced. | Strips cache-busting query strings (`?v=2`) and verifies relative paths point to existing local files on disk. |
| **XML Well-Formedness** | Validates SVG syntax tree. | Reports line and column numbers for unclosed tags, malformed entities, or invalid XML syntax. |
| **GitHub Security & Sanitization** | Prevents proxy blocking. | Strictly disallows `<script>` tags, `<foreignObject>` containers, and external stylesheets (`xml-stylesheet`, `@import`, `<link rel="stylesheet">`). |
| **Zero External Resources** | Prevents network calls during render. | Forbids externally loaded images (`<image href="https://...">`) and external font URLs (`@font-face { src: url('http...') }`). |
| **Destination Hyperlinks** | Allows ordinary navigation links. | Distinguishes navigation links (`<a href="https://...">`) from rendering resources, allowing user hyperlinks. |
| **ID Uniqueness & References** | Prevents rendering conflicts. | Verifies all `id` attributes are unique within each SVG and confirms all `url(#...)` and `href="#..."` fragments resolve. |
| **Embedded PNG Integrity** | Protects source artwork provenance. | Decodes inline Base64 data URIs and checks that SHA-256 hashes match source PNGs (`assets/id.png`, `assets/right_pointing.png`). |
| **Genuine Alpha Transparency** | Verifies portrait cutouts. | Decompresses PNG `IDAT` scanlines and confirms genuine non-255 alpha values exist. |
| **Fonts & License Records** | Legal redistribution compliance. | Verifies embedded Base64 WOFF2 font declarations and confirms required license files exist in `licenses/`. |

---

## 🚀 Usage

### Run Validation Locally
```bash
# Run validator against repository root
./scripts/validate_assets.py

# Run in verbose mode for detailed step-by-step reporting
./scripts/validate_assets.py -v
```

### Run Unit Tests
```bash
# Execute unit tests covering valid assets and negative defect fixtures
python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## ⚠️ What Static Validation Cannot Prove (Required Visual Browser Review)

While static analysis guarantees XML compliance, security adherence, and byte preservation, **it cannot simulate how browser layout engines and GitHub's Camo CDN visually composite the assets**.

The following visual and motion properties **require human/browser review** and must not be assumed verified by the script alone:

1. **Animation Physics & Smoothness**:
   - The damped pendulum settling (0s–3.8s) and continuous sinusoidal swing (±1.7°) of `id-dashboard.svg`.
   - The 12-second repeat cycle and cross-fade opacity transitions of `about-life.svg`.
   - The smooth continuous progress bar fills across the 3 carousel slides.
2. **Text Metrics & Visual Clipping**:
   - Font rendering differences across client operating systems (macOS, Windows, Linux, iOS, Android).
   - Label counter-rotation along tilted elliptical orbits in `stack.svg` to guarantee labels stay upright and never invert or clip.
   - Text reveal mask bounds in `hero.svg` to ensure no character stems are clipped.
3. **Mobile & Viewport Responsiveness**:
   - Proportional SVG scaling at typical GitHub Desktop widths (880px–1012px).
   - Legibility on narrow mobile viewports (375px and 430px) without horizontal scrolling.
4. **Reduced-Motion Fallbacks**:
   - Visual verification under `@media (prefers-reduced-motion: reduce)` to ensure carousel slides stack without overlap and the lanyard ID card rests vertically.
5. **Live GitHub CDN (Camo Proxy) Ingestion**:
   - Cache-busting query strings (`?v=N`) must be incremented whenever SVG assets are modified to instruct GitHub's caching proxy (`camo.githubusercontent.com`) to fetch fresh assets.

---

## 📖 Contributor Guide & Visual Checklist

For complete step-by-step instructions on updating assets, encoding portraits, updating licenses, bumping version strings, and the 4-point visual-review checklist, see [CONTRIBUTING.md](../CONTRIBUTING.md).

For the automated CI workflow that runs this validator on every push and pull request, see [.github/workflows/validate-assets.yml](../.github/workflows/validate-assets.yml).
