# Profile design maintenance

The visual direction is inspired by dark, illustrated GitHub profiles. The banner is original generated artwork; its fictional character is an illustration, not a portrait of Akash. The copy and linked projects describe Akash's own work.

## Assets and rendering

- `assets/creative-night.png` is the original banner illustration. It contains no text, so the name, roles, and contact links remain accessible in the README.
- `assets/focus-board.svg` is a self-contained vector dashboard. Its indicator pulses twice, then settles. `prefers-reduced-motion: reduce` turns off the animation, and the static composition contains all of the text.
- Both local assets use relative paths. The README uses GitHub-compatible Markdown and HTML, without scripts or page CSS.
- Social and tool badges come from shields.io; GitHub statistics cards come from github-readme-stats.vercel.app. Those third-party images may be unavailable at times. The underlying skills, projects, and link to native GitHub activity remain readable without them.

## Content sources

Identity, design focus, email, LinkedIn, and support information were retained from the previous profile README. NexusCV and Andy-Portfolio descriptions are based on their public READMEs. React, TypeScript, and Tailwind are labeled as technologies used in linked projects, not a claim of expert proficiency. The statistics are generated from public GitHub repositories and can change.

## Review checklist

- Check the README on the main repository and on the rendered GitHub profile at desktop and narrow widths.
- Check that the hero, dashboard, project links, contact links, disclosure, badges, and statistics images load.
- Test the SVG with and without reduced motion. Parse it as XML after edits.
- Keep meaningful copy outside images and avoid unverified outcome or employment claims.
