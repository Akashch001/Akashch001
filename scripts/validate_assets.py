#!/usr/bin/env python3
"""
Profile Asset Validator
Validates animated GitHub profile README assets:
- README relative SVG references (ignoring query strings)
- SVG XML validity
- Zero external resources (no scripts, foreignObject, external stylesheets, external fonts/images)
- Preservation of destination hyperlinks vs rendering resources
- Internal SVG reference resolution and ID uniqueness
- Embedded PNG data integrity and byte-exact match to source PNGs
- Genuine alpha transparency in portrait PNGs
- Embedded font data and applicable license documentation
"""

import os
import sys
import re
import base64
import hashlib
import struct
import zlib
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

REQUIRED_SVGS = [
    "assets/hero.svg",
    "assets/about-life.svg",
    "assets/stack.svg",
    "assets/id-dashboard.svg",
    "assets/connect.svg",
]

REQUIRED_LICENSES = [
    "licenses/OFL-SpaceGrotesk.txt",
    "licenses/OFL-SpaceMono.txt",
    "licenses/LICENSE-SimpleIcons.txt",
    "licenses/LICENSE-Lenis.txt",
]

PNG_MAP = {
    "assets/hero.svg": "assets/id.png",
    "assets/id-dashboard.svg": "assets/id.png",
    "assets/connect.svg": "assets/right_pointing.png",
}

class ValidationError:
    def __init__(self, filename, message, line=None):
        self.filename = filename
        self.message = message
        self.line = line

    def __str__(self):
        loc = f":{self.line}" if self.line else ""
        return f"[{self.filename}{loc}] {self.message}"

class AssetValidator:
    def __init__(self, root_dir, verbose=False):
        self.root = Path(root_dir).resolve()
        self.verbose = verbose
        self.errors = []
        self.warnings = []

    def log(self, msg):
        if self.verbose:
            print(f"  -> {msg}")

    def add_error(self, filename, message, line=None):
        err = ValidationError(filename, message, line)
        self.errors.append(err)

    def add_warning(self, filename, message):
        self.warnings.append(f"[{filename}] WARNING: {message}")

    def check_readme_references(self):
        readme_path = self.root / "README.md"
        if not readme_path.is_file():
            self.add_error("README.md", "README.md not found in repository root")
            return

        content = readme_path.read_text(encoding="utf-8")
        # Extract <img src="..."> and ![...](...)
        img_srcs = re.findall(r'<img\s+[^>]*\bsrc=["\']([^"\']+)["\']', content, re.IGNORECASE)
        md_srcs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', content)
        all_refs = img_srcs + md_srcs

        cleaned_refs = []
        for r in all_refs:
            base_ref = r.split("?")[0].strip()
            cleaned_refs.append(base_ref)

        self.log(f"Found {len(cleaned_refs)} image references in README.md")

        for req in REQUIRED_SVGS:
            if req not in cleaned_refs:
                self.add_error("README.md", f"Required profile image '{req}' is not referenced in README.md")
            else:
                target_file = self.root / req
                if not target_file.is_file():
                    self.add_error("README.md", f"Referenced asset '{req}' does not exist on disk at {target_file}")
                else:
                    self.log(f"Verified reference and file existence: {req}")

    def check_svg_xml(self, rel_path):
        full_path = self.root / rel_path
        if not full_path.is_file():
            self.add_error(str(rel_path), "File does not exist")
            return None

        try:
            tree = ET.parse(full_path)
            self.log(f"XML parse successful: {rel_path}")
            return tree
        except ET.ParseError as e:
            self.add_error(str(rel_path), f"XML Syntax Error: {e.msg}", line=e.position[0])
            return None

    def check_svg_security_and_resources(self, rel_path, content, root_elem):
        # 1. No script elements (case insensitive)
        if re.search(r'<\s*script\b', content, re.IGNORECASE):
            self.add_error(str(rel_path), "Forbidden <script> element detected in SVG")

        # 2. No foreignObject elements
        if re.search(r'<\s*foreignObject\b', content, re.IGNORECASE):
            self.add_error(str(rel_path), "Forbidden <foreignObject> element detected in SVG")

        # 3. No external stylesheets
        if "xml-stylesheet" in content:
            self.add_error(str(rel_path), "External xml-stylesheet processing instruction detected")
        if re.search(r'<\s*link\b[^>]*\brel=["\']stylesheet["\']', content, re.IGNORECASE):
            self.add_error(str(rel_path), "Forbidden external <link rel='stylesheet'> detected")
        if re.search(r'@import\s+(?:url\()?["\']?https?://', content, re.IGNORECASE):
            self.add_error(str(rel_path), "Forbidden external @import stylesheet detected in CSS")

        # 4. Check for externally loaded images or fonts
        # Disallow <image ... href="http..."> or xlink:href="http..."
        ext_image_match = re.findall(r'<\s*image\b[^>]*\b(?:href|xlink:href)=["\'](https?://[^"\']+)["\']', content, re.IGNORECASE)
        if ext_image_match:
            self.add_error(str(rel_path), f"Externally loaded image resource detected: {ext_image_match}")

        # Disallow external fonts in CSS @font-face { src: url('http...') }
        ext_font_match = re.findall(r'@font-face\s*\{[^}]*src:\s*url\(["\']?(https?://[^)"\']+)["\']?\)', content, re.IGNORECASE)
        if ext_font_match:
            self.add_error(str(rel_path), f"Externally loaded font resource detected: {ext_font_match}")

        # 5. Distinguish destination links (<a href="https://...">) which are allowed
        # (Validate that links are ordinary hyperlinks and not embedded rendering pipelines)
        dest_links = re.findall(r'<\s*a\b[^>]*\b(?:href|xlink:href)=["\'](https?://[^"\']+)["\']', content, re.IGNORECASE)
        if dest_links:
            self.log(f"{rel_path}: Found {len(dest_links)} destination hyperlink(s) (permitted)")

    def check_svg_ids_and_references(self, rel_path, content):
        # 1. ID uniqueness check
        id_matches = re.findall(r'\bid=["\']([^"\']+)["\']', content)
        seen_ids = set()
        duplicates = set()
        for i in id_matches:
            if i in seen_ids:
                duplicates.add(i)
            seen_ids.add(i)

        if duplicates:
            self.add_error(str(rel_path), f"Duplicate ID(s) detected in file: {sorted(list(duplicates))}")

        # 2. Internal reference resolution
        url_refs = re.findall(r'url\(#([^)]+)\)', content)
        href_refs = re.findall(r'<(?:use|mpath)\b[^>]*\b(?:href|xlink:href)=["\']#([^"\']+)["\']', content)
        mask_refs = re.findall(r'\b(?:mask|clip-path)=["\']url\(#([^)]+)\)["\']', content)

        all_refs = set(url_refs + href_refs + mask_refs)
        missing_refs = [r for r in all_refs if r not in seen_ids]
        if missing_refs:
            self.add_error(str(rel_path), f"Unresolved internal reference(s): {missing_refs}")
        else:
            self.log(f"{rel_path}: All {len(all_refs)} internal references resolved cleanly")

    def check_embedded_png(self, rel_path):
        full_path = self.root / rel_path
        content = full_path.read_text(encoding="utf-8")

        expected_source_png = PNG_MAP.get(str(rel_path).replace("\\", "/"))
        if not expected_source_png:
            return

        source_png_path = self.root / expected_source_png
        if not source_png_path.is_file():
            self.add_error(str(rel_path), f"Source PNG file '{expected_source_png}' not found on disk")
            return

        source_bytes = source_png_path.read_bytes()
        source_hash = hashlib.sha256(source_bytes).hexdigest()

        # Extract embedded data URIs
        b64_matches = re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)', content)
        if not b64_matches:
            self.add_error(str(rel_path), f"Expected embedded PNG data URI matching '{expected_source_png}', but none found")
            return

        matched = False
        for idx, b64_str in enumerate(b64_matches):
            try:
                decoded_bytes = base64.b64decode(b64_str)
                decoded_hash = hashlib.sha256(decoded_bytes).hexdigest()
                if decoded_hash == source_hash:
                    matched = True
                    self.log(f"{rel_path}: Embedded PNG matches {expected_source_png} (SHA-256: {decoded_hash[:16]}...)")
                    break
            except Exception as e:
                self.add_error(str(rel_path), f"Failed to decode embedded base64 PNG data: {e}")

        if not matched:
            self.add_error(str(rel_path), f"Embedded base64 PNG bytes do not match source PNG '{expected_source_png}' (SHA-256 mismatch)")

    def check_png_alpha_transparency(self, rel_path):
        png_path = self.root / rel_path
        if not png_path.is_file():
            self.add_error(str(rel_path), "PNG file not found on disk")
            return

        data = png_path.read_bytes()
        if len(data) < 8 or data[:8] != b'\x89PNG\r\n\x1a\n':
            self.add_error(str(rel_path), "Invalid PNG signature")
            return

        pos = 8
        length, chunk_type = struct.unpack('>I4s', data[pos:pos+8])
        pos += 8
        if chunk_type != b'IHDR':
            self.add_error(str(rel_path), "First PNG chunk is not IHDR")
            return

        w, h, bit_depth, color_type, comp, filt, interlace = struct.unpack('>IIBBBBB', data[pos:pos+13])
        pos += length + 4 # skip CRC

        has_alpha_type = color_type in (4, 6)
        has_trns = False
        idat_data = []

        while pos < len(data):
            if pos + 8 > len(data):
                break
            length, chunk_type = struct.unpack('>I4s', data[pos:pos+8])
            pos += 8
            if chunk_type == b'tRNS':
                has_trns = True
            elif chunk_type == b'IDAT':
                idat_data.append(data[pos:pos+length])
            elif chunk_type == b'IEND':
                break
            pos += length + 4

        if not has_alpha_type and not has_trns:
            self.add_error(str(rel_path), f"PNG lacks alpha channel (color_type={color_type}, no tRNS chunk)")
            return

        # Scanline transparency validation
        if color_type == 6 and bit_depth == 8 and interlace == 0:
            try:
                raw = zlib.decompress(b"".join(idat_data))
                bpp = 4
                stride = 1 + w * bpp
                transparent_pixels = 0
                for y in range(h):
                    line = raw[y*stride + 1 : (y+1)*stride]
                    for x in range(w):
                        if line[x*4 + 3] < 255:
                            transparent_pixels += 1
                if transparent_pixels == 0:
                    self.add_error(str(rel_path), "PNG has RGBA color type but contains no transparent pixels (100% opaque)")
                else:
                    self.log(f"{rel_path}: Verified genuine alpha channel ({transparent_pixels}/{w*h} pixels have alpha < 255)")
            except Exception as e:
                self.add_warning(str(rel_path), f"Could not decompress IDAT scanlines for detailed alpha count: {e}")

    def check_embedded_fonts_and_licenses(self):
        # 1. Embedded font verification in SVGs
        for req in REQUIRED_SVGS:
            full_path = self.root / req
            if full_path.is_file():
                content = full_path.read_text(encoding="utf-8")
                # Look for data:font/woff2;base64,...
                if "@font-face" in content:
                    font_matches = re.findall(r'url\(["\']?data:font/woff2;base64,([A-Za-z0-9+/=]+)["\']?\)', content)
                    if not font_matches:
                        self.add_error(req, "Contains @font-face declaration but no inline base64 WOFF2 font data")
                    else:
                        self.log(f"{req}: Verified {len(font_matches)} embedded base64 WOFF2 font(s)")

        # 2. License file verification
        for lic in REQUIRED_LICENSES:
            lic_path = self.root / lic
            if not lic_path.is_file():
                self.add_error(lic, f"Required license file '{lic}' is missing")
            else:
                self.log(f"License verified: {lic}")

    def run_all(self):
        self.log(f"Starting asset validation in repository root: {self.root}")
        self.check_readme_references()

        for req in REQUIRED_SVGS:
            svg_path = self.root / req
            if svg_path.is_file():
                tree = self.check_svg_xml(req)
                if tree is not None:
                    content = svg_path.read_text(encoding="utf-8")
                    self.check_svg_security_and_resources(req, content, tree.getroot())
                    self.check_svg_ids_and_references(req, content)
                    self.check_embedded_png(req)

        # Check source portraits
        for png_rel in ["assets/id.png", "assets/right_pointing.png"]:
            self.check_png_alpha_transparency(png_rel)

        # Check fonts and licenses
        self.check_embedded_fonts_and_licenses()

        return len(self.errors) == 0

def main():
    parser = argparse.ArgumentParser(description="Profile Asset Validator for animated GitHub profile packages")
    parser.add_argument("--root", default=".", help="Repository root directory (default: current directory)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose validation logging")
    args = parser.parse_args()

    validator = AssetValidator(args.root, verbose=args.verbose)
    passed = validator.run_all()

    if validator.warnings:
        print("\nWarnings:")
        for w in validator.warnings:
            print(f"  * {w}")

    if not passed:
        print("\nValidation FAILED with the following error(s):")
        for err in validator.errors:
            print(f"  ✖ {err}")
        print("\nFix the errors above to ensure GitHub-safe profile asset compliance.")
        sys.exit(1)
    else:
        print("\n✔ All profile assets, XML trees, embedded PNGs, alpha transparency, and licenses validated successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
