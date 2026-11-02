#!/usr/bin/env python3
"""Observable export/rebuild checks using synthetic artwork in temporary folders."""
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'draft2brand'
BUILD = SKILL / 'scripts' / 'build_kit.py'

class Exporter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='draft2brand-test-')
        cls.base = Path(cls.temp.name)
        cls.full = cls.base / 'full'
        cls.run_build(SKILL / 'assets' / 'brand.example.json', cls.full)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    @staticmethod
    def run_build(config, output, script=BUILD, success=True):
        result = subprocess.run([sys.executable, str(script), str(config), '--out', str(output)], capture_output=True, text=True)
        if success and result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        return result

    def make_input(self, name, change=None, svg=None):
        folder = self.base / name
        folder.mkdir()
        cfg = json.loads((SKILL / 'assets' / 'brand.example.json').read_text())
        cfg['source'] = 'mark.svg'
        if change:
            change(cfg)
        (folder / 'brand.json').write_text(json.dumps(cfg))
        (folder / 'mark.svg').write_text(svg or (SKILL / 'assets' / 'mark.example.svg').read_text())
        return folder / 'brand.json'

    def test_complete_deliverables(self):
        self.assertEqual(len(list(self.full.glob('example-studio-*.svg'))), 9)
        pngs = list((self.full / 'png').glob('*.png'))
        self.assertEqual(len(pngs), 35)
        for file in pngs:
            data = file.read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            width, height, depth, kind = struct.unpack('>IIBB', data[16:26])
            self.assertEqual((width, height), (int(file.stem.split('-')[-1]),) * 2)
            self.assertEqual((depth, kind), (8, 2), 'Profiles must be opaque RGB PNGs')
        with zipfile.ZipFile(self.full / 'example-studio-v1-pngs.zip') as z:
            self.assertEqual(len(z.namelist()), 35)
            self.assertTrue(all(n.startswith('png/') and n.endswith('.png') for n in z.namelist()))
        with zipfile.ZipFile(self.full / 'example-studio-v1-brand-kit.zip') as z:
            self.assertTrue({'brand.json','source/mark.svg','build_kit.py','render.mjs','package-lock.json','review.html','audit.json'} <= set(z.namelist()))
            self.assertTrue(all(not n.startswith('/') and '..' not in Path(n).parts and 'node_modules' not in n for n in z.namelist()))
        manifest = json.loads((self.full / 'manifest.json').read_text())
        for file, expected in manifest.items():
            self.assertEqual(hashlib.sha256((self.full/file).read_bytes()).hexdigest(), expected)
        self.assertEqual((self.full/'source/mark.svg').read_bytes(), (SKILL/'assets/mark.example.svg').read_bytes())

    def test_geometry_survives_every_colorway(self):
        source = ET.parse(SKILL/'assets/mark.example.svg').getroot()
        expected = [(n.tag, {k:v for k,v in n.attrib.items() if k not in {'fill','stroke'}}) for n in source.iter() if n.tag.rsplit('}',1)[-1] in {'path','rect','circle'}]
        for file in self.full.glob('example-studio-*.svg'):
            if file.stem.endswith('-core'):
                continue
            root = ET.parse(file).getroot()
            actual = [(n.tag,{k:v for k,v in n.attrib.items() if k not in {'fill','stroke'}}) for n in root.iter() if n.tag.rsplit('}',1)[-1] in {'path','rect','circle'}]
            self.assertEqual(actual, expected)
            self.assertEqual(root.get('viewBox'), source.get('viewBox'))
        for preview in self.full.glob('*preview*.svg'):
            ids = [n.get('id') for n in ET.parse(preview).getroot().iter() if n.get('id')]
            self.assertEqual(len(ids), len(set(ids)))

    def test_rebuild_from_exported_sources(self):
        install = subprocess.run(['npm','ci','--no-audit','--no-fund'], cwd=self.full, capture_output=True, text=True)
        self.assertEqual(install.returncode, 0, install.stdout + install.stderr)
        rebuilt = self.base/'rebuilt'
        self.run_build(self.full/'brand.json', rebuilt, script=self.full/'build_kit.py')
        files = list(self.full.glob('example-studio-*.svg')) + list((self.full/'png').glob('*.png'))
        for file in files:
            self.assertEqual(file.read_bytes(), (rebuilt/file.relative_to(self.full)).read_bytes())

    def test_wide_single_part_symbol_fits(self):
        def change(c):
            c.pop('coreGroup')
            c['colors'] = {'ink':'#172A32', 'paper':'#F6F4EE'}
            c['actions'] = {'fill':'paper','hover':'paper','active':'paper','ink':'ink','focusOnLight':'ink','focusOnDark':'paper'}
            c['variants'] = [v for v in c['variants'] if v['id'] in {'light','dark','mono-dark','mono-light'}]
            for v in c['variants']:
                v['paint'] = {'ink':'paper' if v['id'] in {'dark','mono-light'} else 'ink'}
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 100"><rect data-brand-role="ink" fill="#172A32" x="5" y="5" width="990" height="90" rx="20"/></svg>'
        config = self.make_input('wide-input', change, svg)
        output = self.base/'wide'
        self.run_build(config, output)
        self.assertEqual(len(list(output.glob('example-studio-*.svg'))), 5)
        self.assertEqual(len(list((output/'png').glob('*.png'))), 20)
        for row in json.loads((output/'raster-audit.json').read_text()):
            self.assertTrue(row['circularCropFits'])
            self.assertLessEqual(row['markWidth'], row['width']*.72+1)
            self.assertGreaterEqual(row['markWidth']/row['markHeight'], 9)

    def test_existing_output_is_preserved(self):
        before = {p.name: p.read_bytes() for p in self.full.glob('*.svg')}
        result = self.run_build(SKILL/'assets/brand.example.json', self.full, success=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Output already exists', result.stderr)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.full.glob('*.svg')})

    def test_bad_contrast_fails_before_output(self):
        config = self.make_input('contrast-input', lambda c: c['colors'].update({'ink':'#FFFFFF','paper':'#FFFFFF'}))
        output = self.base/'bad-contrast'
        result = self.run_build(config, output, success=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('fails contrast', result.stderr)
        self.assertFalse(output.exists())

    def test_embedded_or_external_svg_is_rejected(self):
        svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><image href="https://example.invalid/logo.png"/></svg>'
        config = self.make_input('unsafe-input', svg=svg)
        output = self.base/'unsafe'
        result = self.run_build(config, output, success=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Unsupported SVG element', result.stderr)
        self.assertFalse(output.exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
