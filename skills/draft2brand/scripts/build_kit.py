#!/usr/bin/env python3
"""Build a versioned flat-vector identity kit from one role-labelled master."""
import argparse
import copy
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

SVG = 'http://www.w3.org/2000/svg'
ET.register_namespace('', SVG)
ROLES = {'ink', 'accent', 'accent-alt'}
TAGS = {'svg', 'g', 'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 'defs', 'clipPath', 'title', 'desc'}
HEX = re.compile(r'^#[0-9A-Fa-f]{6}$')
IDENT = re.compile(r'^[a-z][a-z0-9-]*$')
HERE = Path(__file__).resolve().parent

def require(ok, message):
    if not ok:
        raise ValueError(message)

def local(tag):
    return tag.split('}')[-1]

def text(value):
    return html.escape(str(value), quote=True)

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def luminance(color):
    values = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in values]
    return sum(a * b for a, b in zip(linear, (.2126, .7152, .0722)))

def contrast(a, b):
    lo, hi = sorted((luminance(a), luminance(b)))
    return (hi + .05) / (lo + .05)

def validate_svg(raw):
    require('<!DOCTYPE' not in raw.upper() and '<!ENTITY' not in raw.upper(), 'SVG declarations/entities are unsupported')
    root = ET.fromstring(raw)
    require(root.tag == f'{{{SVG}}}svg', 'Master must be an SVG with the SVG namespace')
    box = [float(v) for v in re.split(r'[ ,]+', root.get('viewBox', '').strip())]
    require(len(box) == 4 and all(math.isfinite(x) for x in box) and box[2] > 0 and box[3] > 0, 'A finite positive viewBox is required')
    roles, ids = set(), set()
    for node in root.iter():
        require(node.tag.startswith('{' + SVG + '}') and local(node.tag) in TAGS, f'Unsupported SVG element: {node.tag}')
        role = node.get('data-brand-role')
        paint = node.get('data-brand-paint', 'fill').split()
        if role:
            require(role in ROLES and paint and set(paint) <= {'fill', 'stroke'}, 'Invalid paint role or attribute')
            roles.add(role)
        if node.get('id'):
            require(node.get('id') not in ids, 'Duplicate SVG id')
            ids.add(node.get('id'))
        for key, value in node.attrib.items():
            attr = local(key).lower()
            require(not attr.startswith('on') and attr not in {'style', 'href', 'filter'}, f'Unsupported SVG attribute: {key}')
            if 'url(' in value:
                require(attr == 'clip-path' and re.fullmatch(r'url\(#[A-Za-z_][\w.-]*\)', value), 'Only internal clip-path references are supported')
            if attr in {'fill', 'stroke'} and value != 'none':
                require(role and attr in paint and HEX.fullmatch(value), 'All non-none paint needs a role, paint attribute, and six-digit hex color')
    def inherited(node, active=False):
        active = active or bool(node.get('data-brand-role'))
        if local(node.tag) in {'path', 'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon'}:
            require(active, 'Every painted shape must have or inherit a paint role')
        for child in node:
            inherited(child, active)
    inherited(root)
    require('ink' in roles, 'Master needs an ink role')
    return root, box, roles

def geometry(node):
    return [local(node.tag), sorted((k, v) for k, v in node.attrib.items() if k not in {'fill', 'stroke', 'aria-labelledby', 'role'}),
            [geometry(c) for c in node if local(c.tag) not in {'title', 'desc'}]]

def colored(root, paints, title):
    result = copy.deepcopy(root)
    for child in list(result):
        if local(child.tag) in {'title', 'desc'}:
            result.remove(child)
    result.set('role', 'img')
    result.set('aria-labelledby', 'brand-title')
    title_node = ET.Element(f'{{{SVG}}}title', {'id': 'brand-title'})
    title_node.text = title
    result.insert(0, title_node)
    for node in result.iter():
        role = node.get('data-brand-role')
        if role:
            for attr in node.get('data-brand-paint', 'fill').split():
                node.set(attr, paints[role])
    return result

def svg_bytes(root):
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)

def archive(path, files, root):
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        for file in sorted(files):
            # Stable ZIP metadata; no host paths, user metadata or filesystem timestamps.
            info = zipfile.ZipInfo(file.relative_to(root).as_posix(), (2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, file.read_bytes())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    config = args.config.resolve()
    cfg = json.loads(config.read_text())
    slug, version = cfg['slug'], cfg['version']
    require(IDENT.fullmatch(slug) and re.fullmatch(r'v[1-9][0-9]*', version), 'Use a lowercase slug and version v1, v2, ...')
    require(isinstance(cfg.get('brand'), str) and cfg['brand'].strip(), 'Company name is required')
    require(cfg.get('status') in {'draft', 'selected', 'approved'}, 'Status must be draft, selected or approved')
    require(isinstance(cfg.get('selection'), dict) and cfg['selection'].get('geometry') and cfg['selection'].get('palette'), 'Record geometry and palette decision provenance')
    colors = cfg['colors']
    require({'ink', 'paper'} <= colors.keys() and all(IDENT.fullmatch(k) and HEX.fullmatch(v) for k, v in colors.items()), 'Colors need valid token names, hex values, ink and paper')
    source = (config.parent / cfg['source']).resolve()
    raw = source.read_text()
    root, box, roles = validate_svg(raw)
    geo = geometry(root)
    geometry_sha = digest(json.dumps(geo, sort_keys=True).encode())
    variants = cfg['variants']
    require(variants and len({v['id'] for v in variants}) == len(variants), 'Variant IDs must be unique')
    require({'light', 'dark', 'mono-dark', 'mono-light'} <= {v['id'] for v in variants}, 'Provide light, dark and both monochrome variants')
    for v in variants:
        require(IDENT.fullmatch(v['id']) and v['id'] not in {'master', 'core'}, 'Invalid or reserved variant ID')
        require(roles <= v['paint'].keys() and set(v['paint']) <= ROLES and all(k in colors for k in v['paint'].values()), 'Each variant must map every used paint role to a color token')
        require(v['background'] in colors and HEX.fullmatch(v['profileBackground']), 'Invalid variant backgrounds')
    for id_ in ('mono-dark', 'mono-light'):
        v = next(v for v in variants if v['id'] == id_)
        require(len({colors[v['paint'][r]] for r in roles}) == 1, f'{id_} must be monochrome')
    sizes = cfg.get('profileSizes', [1024, 512, 256, 128, 64])
    require(sizes and len(set(sizes)) == len(sizes) and all(type(s) is int and 16 <= s <= 4096 for s in sizes), 'Invalid PNG sizes')
    require(256 in sizes, 'Include 256 px for the review thumbnails')
    actions = cfg['actions']
    require({'fill', 'hover', 'active', 'ink', 'focusOnLight', 'focusOnDark'} <= actions.keys() and all(v in colors for v in actions.values()), 'Invalid action tokens')
    pairs = [('Reading on light', 'ink', 'paper', 4.5), ('Reading on dark', 'paper', 'ink', 4.5)]
    pairs += [(f'Action {state}', actions['ink'], actions[state], 4.5) for state in ('fill', 'hover', 'active')]
    pairs += [('Focus on light', actions['focusOnLight'], 'paper', 3), ('Focus on dark', actions['focusOnDark'], 'ink', 3)]
    ratios = [{'role': label, 'foreground': colors[fg], 'background': colors[bg], 'ratio': contrast(colors[fg], colors[bg]), 'minimum': minimum} for label, fg, bg, minimum in pairs]
    require(all(p['ratio'] >= p['minimum'] for p in ratios), 'A configured text/action/focus pairing fails contrast; revise role assignments before export')
    core = None
    if cfg.get('coreGroup'):
        matches = [c for c in root if local(c.tag) == 'g' and c.get('id') == cfg['coreGroup']]
        require(len(matches) == 1, 'coreGroup must identify one top-level self-contained group')
        crop = cfg.get('coreViewBox', box)
        require(len(crop) == 4 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in crop) and crop[2] > 0 and crop[3] > 0, 'Invalid coreViewBox')
        core = ET.Element(root.tag, {'viewBox': ' '.join(map(str, crop))})
        core.append(copy.deepcopy(matches[0]))
        require(not any('url(' in v for n in core.iter() for v in n.attrib.values()), 'Core export cannot depend on external groups/defs')
    subprocess.run(['node', str(HERE / 'render.mjs'), '--check'], check=True, capture_output=True)
    out = args.out.resolve()
    require(not out.exists(), f'Output already exists; choose a new version: {out}')
    out.mkdir(parents=True)
    (out / 'png').mkdir()
    (out / 'source').mkdir()
    (out / 'source' / 'mark.svg').write_text(raw)
    cfg['source'] = 'source/mark.svg'
    write_json(out / 'brand.json', cfg)
    for filename in ('build_kit.py', 'render.mjs', 'package.json', 'package-lock.json'):
        shutil.copy2(HERE / filename, out / filename)
    exported = []
    monochrome = {r: colors['ink'] for r in ROLES}
    all_marks = [('master', colored(root, monochrome, f"{cfg['brand']} — editable master"))]
    all_marks += [(v['id'], colored(root, {r: colors[k] for r, k in v['paint'].items()}, f"{cfg['brand']} — {v['name']}")) for v in variants]
    if core is not None:
        all_marks.append(('core', colored(core, monochrome, f"{cfg['brand']} — isolated symbol")))
    for id_, mark in all_marks:
        if id_ != 'core':
            require(geometry(mark) == geo, f'Geometry changed in {id_}')
        file = f'{slug}-{id_}.svg'
        (out / file).write_bytes(svg_bytes(mark))
        exported.append(file)
    css = ':root {\n' + ''.join(f'  --brand-{k}: {v};\n' for k, v in colors.items())
    css += ''.join(f'  --brand-action-{re.sub(r"([A-Z])", lambda m: "-" + m[0].lower(), k)}: var(--brand-{v});\n' for k, v in actions.items()) + '}\n'
    (out / 'tokens.css').write_text(css)
    write_json(out / 'palettes.json', {k: cfg[k] for k in ('brand', 'version', 'status', 'selection', 'colors', 'variants', 'actions')} | {'roles': cfg.get('colorRoles', {}), 'textPairs': ratios})
    plan = {'slug': slug, 'viewBox': box, 'sizes': sizes, 'profiles': [{'id': v['id'], 'source': f'{slug}-{v["id"]}.svg', 'background': v['profileBackground']} for v in variants]}
    write_json(out / 'render-plan.json', plan)
    build_previews(out, cfg, all_marks, box)
    build_review(out, cfg, exported, ratios)
    subprocess.run(['node', str(HERE / 'render.mjs'), str(out)], check=True)
    audit = {'geometrySha256': geometry_sha, 'masterSourceSha256': digest(raw.encode()), 'svgExports': exported,
             'pngCount': len(variants) * len(sizes), 'contrast': ratios,
             'scope': 'Geometry and file/color checks only. Visual fidelity and browser review require human/agent inspection.'}
    write_json(out / 'audit.json', audit)
    notes = [f"{cfg['brand']} — {version}", f"Status: {cfg['status']}", '', 'DECISIONS', json.dumps(cfg['selection'], ensure_ascii=False), '', 'USAGE',
             'SVG exports are transparent. Recommended backgrounds are in palettes.json.',
             'For working download controls, run: python3 -m http.server 8000 --bind 127.0.0.1 (inside this folder), then open http://127.0.0.1:8000/review.html. Stop the preview server after review.',
             'Profile PNGs use each configured solid background, independent of brand surface neutrals.',
             'Placement fits both canvas axes and a circular crop; inspect small-size optical balance.',
             'Use neutral reading colors and configured action/focus roles. Logo accent visibility does not establish UI accessibility.', '', 'DELIVERABLES',
             f'{len(exported)} SVGs; {len(variants) * len(sizes)} profile PNGs; 3 PNG/SVG preview sheets; review.html; tokens.css; palettes.json; audit.json; raster-audit.json.',
             '', 'REBUILD', 'npm ci', 'python3 build_kit.py brand.json --out ../rebuilt-kit',
             'Python 3.10+, Node 22+, pinned Sharp. Use a new output directory; original versions are never overwritten.', '', 'NOTES'] + cfg.get('notes', [])
    (out / 'REVIEW.txt').write_text('\n'.join(notes) + '\n')
    archive(out / f'{slug}-{version}-pngs.zip', list((out / 'png').glob('*.png')), out)
    files = [p for p in out.rglob('*') if p.is_file()]
    write_json(out / 'manifest.json', {p.relative_to(out).as_posix(): digest(p.read_bytes()) for p in sorted(files)})
    archive(out / f'{slug}-{version}-brand-kit.zip', [p for p in out.rglob('*') if p.is_file()], out)
    print(f'Created {out}: {len(exported)} SVGs, {audit["pngCount"]} PNGs, review, tokens, previews, rebuild sources and ZIPs.')

def embedded(mark, x, y, w, h):
    node = copy.deepcopy(mark)
    suffix = f'-preview-{x}-{y}'.replace('.', '-')
    ids = {n.get('id'): n.get('id') + suffix for n in node.iter() if n.get('id')}
    for n in node.iter():
        if n.get('id'):
            n.set('id', ids[n.get('id')])
        for key, value in list(n.attrib.items()):
            for old, new in ids.items():
                value = value.replace(f'url(#{old})', f'url(#{new})')
            if key == 'aria-labelledby':
                value = ' '.join(ids.get(part, part) for part in value.split())
            n.set(key, value)
    node.set('x', str(x)); node.set('y', str(y)); node.set('width', str(w)); node.set('height', str(h))
    node.set('preserveAspectRatio', 'xMidYMid meet')
    return ET.tostring(node, encoding='unicode')

def build_previews(out, cfg, marks, box):
    colors = cfg['colors']; variants = cfg['variants']; by_id = dict(marks)
    ink, paper = colors['ink'], colors['paper']
    def label(x, y, content, size=18, fill=ink):
        return f'<text x="{x}" y="{y}" fill="{fill}" font-family="sans-serif" font-size="{size}">{text(content)}</text>'
    def sheet(file, width, height, items):
        (out / file).write_text(f'<svg xmlns="{SVG}" width="{width}" height="{height}" viewBox="0 0 {width} {height}"><rect width="100%" height="100%" fill="{paper}"/>'+''.join(items)+'</svg>')
    parts = [label(40, 54, f"{cfg['brand']} / {cfg['version']} / {cfg['status']}", 26)]
    for index, id_ in enumerate(('light', 'dark')):
        v = next(v for v in variants if v['id'] == id_)
        x = 40 + index * 570; bg = colors[v['background']]
        fg = ink if contrast(ink, bg) >= contrast(paper, bg) else paper
        parts += [f'<rect x="{x}" y="88" width="550" height="360" fill="{bg}"/>', embedded(by_id[id_], x + 160, 120, 230, 240), label(x + 24, 420, v['name'], fill=fg)]
    step = 1120 / len(colors)
    for index, (name, color) in enumerate(colors.items()):
        x = 40 + index * step
        parts += [f'<rect x="{x}" y="488" width="{step-16}" height="70" fill="{color}" stroke="{ink}" stroke-width=".5"/>', label(x, 588, name), label(x, 616, color, 15)]
    sheet('palette-comparison.svg', 1200, 660, parts)
    parts = [label(32, 48, 'Profile variants / circular crop check', 26)]
    rows = math.ceil(len(variants) / 4)
    for i, v in enumerate(variants):
        x, y = 32 + (i % 4) * 290, 88 + (i // 4) * 310
        clip = f'profile-{i}'
        parts += [f'<defs><clipPath id="{clip}"><circle cx="{x+120}" cy="{y+120}" r="120"/></clipPath></defs>', f'<g clip-path="url(#{clip})"><rect x="{x}" y="{y}" width="240" height="240" fill="{v["profileBackground"]}"/>']
        scale = min(240 * .72 / box[2], 240 * .72 / box[3], 240 * .9 / math.hypot(box[2], box[3]))
        w, h = box[2] * scale, box[3] * scale
        parts += [embedded(by_id[v['id']], x + (240-w)/2, y+(240-h)/2, w, h), '</g>', label(x, y+274, v['name'], 16)]
    sheet('profile-previews.svg', 1200, 88 + rows * 310, parts)
    sheet('mark-preview.svg', 640, 640, [embedded(by_id['light'], 100, 100, 440, 440)])

def build_review(out, cfg, exports, ratios):
    slug = cfg['slug']; colors = cfg['colors']; sizes = cfg.get('profileSizes', [1024,512,256,128,64])
    panels = ''.join(f'<figure style="background:{colors[v["background"]]}"><img src="{slug}-{v["id"]}.svg" alt="{text(cfg["brand"])}: {text(v["name"])}"><figcaption><a href="{slug}-{v["id"]}.svg" download>{text(v["name"])} SVG</a></figcaption></figure>' for v in cfg['variants'])
    swatches = ''.join(f'<article><div class="swatch" style="background:{color}"></div><strong>{text(name)}</strong><p>{color}</p><p>{text(cfg.get("colorRoles",{}).get(name,""))}</p></article>' for name,color in colors.items())
    profiles = ''.join(f'<article><img class="profile" src="png/{slug}-{v["id"]}-256.png" alt="{text(v["name"])} profile"><h3>{text(v["name"])}</h3><div class="sizes">'+''.join(f'<a download href="png/{slug}-{v["id"]}-{size}.png">{size}</a>' for size in sizes)+'</div></article>' for v in cfg['variants'])
    rows = ''.join(f'<tr><th scope="row">{text(p["role"])}</th><td>{p["ratio"]:.2f}:1</td><td>{p["minimum"]}:1</td></tr>' for p in ratios)
    links = ''.join(f'<a href="{text(f)}" download>{text(f)}</a>' for f in exports + ['tokens.css','palettes.json','REVIEW.txt','audit.json',f'{slug}-{cfg["version"]}-pngs.zip',f'{slug}-{cfg["version"]}-brand-kit.zip'])
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>__TITLE__</title><link rel="stylesheet" href="tokens.css"><style>
*{box-sizing:border-box}body{margin:0;background:var(--brand-paper);color:var(--brand-ink);font:16px/1.5 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:32px 24px}h1{font-size:clamp(32px,6vw,56px);letter-spacing:-.04em;line-height:1.1}h2{margin:0 0 24px;font-size:28px}h3,p{margin:8px 0}section{margin-top:48px}.panels,.profiles,.swatches{display:grid;gap:24px;grid-template-columns:repeat(auto-fit,minmax(min(100%,240px),1fr))}figure{margin:0;padding:24px;display:grid;gap:24px}figure img{display:block;margin:auto;width:100%;height:220px;object-fit:contain}figcaption{background:var(--brand-paper);color:var(--brand-ink);padding:8px 16px}a{color:inherit;text-underline-offset:4px;display:inline-flex;align-items:center;min-height:44px}a:focus-visible{outline:3px solid currentColor;outline-offset:4px}.swatch{height:72px;border:1px solid var(--brand-ink);margin-bottom:12px}.profile{max-width:200px;width:100%;height:auto;border-radius:50%}.sizes,.downloads{display:flex;flex-wrap:wrap;gap:8px 24px}.sizes a{min-width:44px}.samples{display:grid;grid-template-columns:1fr 1fr;gap:24px}.sample{padding:24px;--ring:var(--brand-action-focus-on-light)}.sample.dark{background:var(--brand-ink);color:var(--brand-paper);--ring:var(--brand-action-focus-on-dark)}.action{background:var(--brand-action-fill);color:var(--brand-action-ink);padding:12px 20px;text-decoration:none;border-radius:6px;transition:background-color 140ms ease}.action:hover{background:var(--brand-action-hover)}.action:active{background:var(--brand-action-active)}.action:focus-visible{outline:3px solid var(--ring);outline-offset:4px}table{border-collapse:collapse;width:100%;max-width:680px}th,td{text-align:left;padding:12px;border-bottom:1px solid currentColor}footer{margin-top:48px}code{overflow-wrap:anywhere}@media(max-width:500px){.samples{grid-template-columns:1fr}main{padding:24px 16px}}@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body><main><header><p>__STATUS__ / __VERSION__</p><h1>__BRAND__</h1><p>Vector geometry, palette roles and export review.</p></header><section aria-label="Logo variants" class="panels">__PANELS__</section><section><h2>Palette and roles</h2><div class="swatches">__SWATCHES__</div></section><section><h2>Action states</h2><p>Hover, press or use Tab. These links download the logo.</p><div class="samples"><div class="sample"><a class="action" href="__SLUG__-light.svg" download>Download light SVG</a></div><div class="sample dark"><a class="action" href="__SLUG__-dark.svg" download>Download dark SVG</a></div></div></section><section><h2>Profile exports</h2><div class="profiles">__PROFILES__</div></section><section><h2>Color-pair checks</h2><p>Numerical checks for the specified roles; visual and browser review remain necessary.</p><table><thead><tr><th scope="col">Pair</th><th scope="col">Ratio</th><th scope="col">Minimum</th></tr></thead><tbody>__ROWS__</tbody></table></section><section><h2>Downloads</h2><div class="downloads">__LINKS__</div></section><footer><p>Decisions and rebuild instructions: <a href="REVIEW.txt">usage notes</a>.</p></footer></main></body></html>'''
    replacements = {'TITLE':text(cfg['brand']+' brand kit'),'BRAND':text(cfg['brand']),'STATUS':text(cfg['status']),'VERSION':text(cfg['version']),'PANELS':panels,'SWATCHES':swatches,'PROFILES':profiles,'ROWS':rows,'LINKS':links,'SLUG':slug}
    for key,value in replacements.items():
        page=page.replace('__'+key+'__',value)
    (out/'review.html').write_text(page)

if __name__ == '__main__':
    try:
        main()
    except (ValueError, KeyError, ET.ParseError, subprocess.CalledProcessError, FileNotFoundError) as error:
        print(f'Brand kit build failed: {error}', file=sys.stderr)
        sys.exit(1)
