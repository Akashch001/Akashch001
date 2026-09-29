# Profile design maintenance

The profile uses a Windows-inspired desktop illustration and ordinary GitHub Markdown. The visual theme does not imply operating-system or software-engineering experience.

## Assets and motion

- `assets/akash-os.svg` is self-contained: vector shapes, system fonts, and CSS animation inside an SVG image. No scripts, external fonts, remote images, tracking pixels, scheduled workflows, or third-party badge/stat services are required.
- The accent line draws once in 2.4 seconds; activity indicators settle after 2.8 seconds. There is no endless animation or flashing. `prefers-reduced-motion: reduce` disables motion.
- The base SVG is the complete static composition. If animation is unavailable, every label remains visible. The README repeats all essential identity, skills, and contact information as accessible text.
- Keep the image embedded with a relative path and descriptive alt text. Do not paste inline SVG, JavaScript, or page-level CSS into the README.
- Colors are fixed within the illustration for a consistent result on either GitHub theme. The body uses GitHub's native theme and responsive Markdown.

## Content

The identity, skills, current interests, email, LinkedIn, PayPal, and USDT address come from the previous README. No client outcomes, seniority, employment history, or completed case studies have been invented. Add featured projects only when their destinations and descriptions can be verified.

## Review checklist

- Open the rendered README on GitHub at desktop and narrow widths.
- Check the header image, contact links, repository link, and support disclosure.
- Confirm the short animation settles and reduced-motion mode stays static.
- Keep text readable when the image cannot load.
- Parse the SVG as XML after edits; preserve its viewBox and avoid external references.

GitHub formatting reference: https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax
