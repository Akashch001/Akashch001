#!/usr/bin/env python3
"""
Unit test suite for scripts/validate_assets.py
Tests both valid repository assets and invalid defect fixtures.
"""

import os
import sys
import shutil
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from validate_assets import AssetValidator, REQUIRED_SVGS, REQUIRED_LICENSES

class TestProfileAssetValidator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_live_repository_passes_all_checks(self):
        """Verify that the actual repository assets pass all validation checks."""
        validator = AssetValidator(str(REPO_ROOT), verbose=False)
        passed = validator.run_all()
        self.assertTrue(passed, f"Repository assets failed validation: {[str(e) for e in validator.errors]}")
        self.assertEqual(len(validator.errors), 0)

    def test_missing_readme(self):
        """Validator should catch missing README.md."""
        validator = AssetValidator(str(self.temp_path))
        validator.check_readme_references()
        self.assertTrue(any("README.md not found" in e.message for e in validator.errors))

    def test_missing_svg_reference_in_readme(self):
        """Validator should catch if an SVG is missing from README."""
        (self.temp_path / "README.md").write_text("<img src='assets/hero.svg?v=1' />", encoding="utf-8")
        validator = AssetValidator(str(self.temp_path))
        validator.check_readme_references()
        # Should flag missing references for about-life, stack, id-dashboard, connect
        missing_errors = [e for e in validator.errors if "is not referenced in README.md" in e.message]
        self.assertEqual(len(missing_errors), 4)

    def test_invalid_xml_syntax(self):
        """Validator should catch XML syntax errors and report line numbers."""
        invalid_svg = self.temp_path / "broken.svg"
        invalid_svg.write_text("<svg><rect width='10' height='10'>", encoding="utf-8") # unclosed
        validator = AssetValidator(str(self.temp_path))
        tree = validator.check_svg_xml(Path("broken.svg"))
        self.assertIsNone(tree)
        self.assertTrue(any("XML Syntax Error" in e.message for e in validator.errors))

    def test_forbidden_script_tag(self):
        """Validator should catch inline or nested script tags."""
        script_svg = self.temp_path / "script.svg"
        content = "<svg xmlns='http://www.w3.org/2000/svg'><script>alert('xss')</script></svg>"
        script_svg.write_text(content, encoding="utf-8")
        validator = AssetValidator(str(self.temp_path))
        validator.check_svg_security_and_resources(Path("script.svg"), content, None)
        self.assertTrue(any("Forbidden <script>" in e.message for e in validator.errors))

    def test_forbidden_foreign_object(self):
        """Validator should catch foreignObject elements."""
        fo_svg = self.temp_path / "fo.svg"
        content = "<svg xmlns='http://www.w3.org/2000/svg'><foreignObject width='100' height='100'><div>hi</div></foreignObject></svg>"
        fo_svg.write_text(content, encoding="utf-8")
        validator = AssetValidator(str(self.temp_path))
        validator.check_svg_security_and_resources(Path("fo.svg"), content, None)
        self.assertTrue(any("Forbidden <foreignObject>" in e.message for e in validator.errors))

    def test_externally_loaded_image_resource(self):
        """Validator should catch external image URLs loaded during rendering."""
        ext_svg = self.temp_path / "ext.svg"
        content = "<svg xmlns='http://www.w3.org/2000/svg'><image href='https://example.com/external.png' width='10' height='10'/></svg>"
        ext_svg.write_text(content, encoding="utf-8")
        validator = AssetValidator(str(self.temp_path))
        validator.check_svg_security_and_resources(Path("ext.svg"), content, None)
        self.assertTrue(any("Externally loaded image resource detected" in e.message for e in validator.errors))

    def test_allowed_destination_hyperlink(self):
        """Validator should permit ordinary destination hyperlinks (<a href='https://...'>)."""
        link_svg = self.temp_path / "link.svg"
        content = "<svg xmlns='http://www.w3.org/2000/svg'><a href='https://github.com/Akashch001'><text>Profile</text></a></svg>"
        link_svg.write_text(content, encoding="utf-8")
        validator = AssetValidator(str(self.temp_path))
        validator.check_svg_security_and_resources(Path("link.svg"), content, None)
        # Should have 0 errors
        self.assertEqual(len(validator.errors), 0)

    def test_duplicate_ids(self):
        """Validator should catch duplicate IDs within an SVG."""
        dup_svg = self.temp_path / "dup.svg"
        content = "<svg xmlns='http://www.w3.org/2000/svg'><g id='test-item'></g><g id='test-item'></g></svg>"
        dup_svg.write_text(content, encoding="utf-8")
        validator = AssetValidator(str(self.temp_path))
        validator.check_svg_ids_and_references(Path("dup.svg"), content)
        self.assertTrue(any("Duplicate ID(s)" in e.message for e in validator.errors))

    def test_unresolved_internal_reference(self):
        """Validator should catch url(#missing) references."""
        unres_svg = self.temp_path / "unres.svg"
        content = "<svg xmlns='http://www.w3.org/2000/svg'><rect fill='url(#missing-grad)' /></svg>"
        unres_svg.write_text(content, encoding="utf-8")
        validator = AssetValidator(str(self.temp_path))
        validator.check_svg_ids_and_references(Path("unres.svg"), content)
        self.assertTrue(any("Unresolved internal reference(s)" in e.message for e in validator.errors))

    def test_png_without_alpha_channel(self):
        """Validator should reject a PNG that has no alpha channel."""
        opaque_png = self.temp_path / "opaque.png"
        # Minimal 1x1 24-bit RGB PNG (color type 2, no alpha)
        # 8-byte sig + IHDR(13) + IDAT + IEND
        import struct, zlib
        sig = b'\x89PNG\r\n\x1a\n'
        ihdr_data = struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0) # color type 2 = RGB
        def make_chunk(chunk_type, data):
            import binascii
            crc = binascii.crc32(chunk_type + data) & 0xffffffff
            return struct.pack('>I', len(data)) + chunk_type + data + struct.pack('>I', crc)
        
        raw_scanline = b'\x00\xff\x00\x00' # filter 0 + R G B
        idat_data = zlib.compress(raw_scanline)
        png_bytes = sig + make_chunk(b'IHDR', ihdr_data) + make_chunk(b'IDAT', idat_data) + make_chunk(b'IEND', b'')
        opaque_png.write_bytes(png_bytes)

        validator = AssetValidator(str(self.temp_path))
        validator.check_png_alpha_transparency(Path("opaque.png"))
        self.assertTrue(any("lacks alpha channel" in e.message for e in validator.errors))

    def test_missing_license_files(self):
        """Validator should report missing license files."""
        validator = AssetValidator(str(self.temp_path))
        validator.check_embedded_fonts_and_licenses()
        missing_lic_errors = [e for e in validator.errors if "is missing" in e.message]
        self.assertEqual(len(missing_lic_errors), len(REQUIRED_LICENSES))

if __name__ == "__main__":
    unittest.main()
